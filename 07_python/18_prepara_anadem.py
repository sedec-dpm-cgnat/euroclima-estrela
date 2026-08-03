# -*- coding: utf-8 -*-
"""Baixa o ANADEM do ImageServer e alinha ao recorte do Fdr.tif.

Uso recomendado: python 18_prepara_anadem.py --baixar
"""
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError
import argparse
import json
import time
import geopandas as gpd
from shapely.geometry import box
from osgeo import gdal

gdal.UseExceptions()
RAIZ = Path(r"C:\Users\cassi\OneDrive\Documents\SEDEC\PROJETO_EUROCLIMA")
ESP = RAIZ / "Documentos EUROCLIMA+" / "Espanha"
GIS = ESP / "GIS"
SHP = GIS / "shapefiles"
FDR = GIS / "raster" / "Fdr.tif"
OUT = GIS / "raster" / "anadem_taquari_31982.tif"
SERVICE = "https://iede.rs.gov.br/image/rest/services/SEMA/ATLASHIDRO_ANADEM/ImageServer/exportImage"
MAX_WIDTH = 4000
MAX_HEIGHT = 2000


def janela_alvo():
    ds = gdal.Open(str(FDR))
    gt0 = ds.GetGeoTransform()
    px = gt0[1]
    bac = gpd.read_file(SHP / "Bacia_Hidrografica_Taquari.shp").to_crs(31982)
    bx = bac.total_bounds
    buf = 40 * px
    c1 = max(0, int((bx[0] - buf - gt0[0]) / gt0[1]))
    c2 = min(ds.RasterXSize, int((bx[2] + buf - gt0[0]) / gt0[1]) + 1)
    r1 = max(0, int((bx[3] + buf - gt0[3]) / gt0[5]))
    r2 = min(ds.RasterYSize, int((bx[1] - buf - gt0[3]) / gt0[5]) + 1)
    nx, ny = c2 - c1, r2 - r1
    gt = (gt0[0] + c1 * gt0[1], gt0[1], 0.0,
          gt0[3] + r1 * gt0[5], 0.0, gt0[5])
    return gt, nx, ny


def transformar_bbox(gt, c0, c1, r0, r1):
    xmin = gt[0] + c0 * gt[1]
    xmax = gt[0] + c1 * gt[1]
    ymax = gt[3] + r0 * gt[5]
    ymin = gt[3] + r1 * gt[5]
    geom = gpd.GeoSeries([box(xmin, ymin, xmax, ymax)], crs=31982).to_crs(4674)
    return geom.total_bounds.tolist()


def url_faixa(bbox, width, height):
    params = {
        "bbox": ",".join(f"{x:.10f}" for x in bbox),
        "bboxSR": 4674, "imageSR": 4674,
        "size": f"{width},{height}", "format": "tiff", "f": "image",
    }
    return SERVICE + "?" + urlencode(params)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baixar", action="store_true", help="baixa e gera o raster alinhado")
    ap.add_argument("--forcar", action="store_true", help="substitui o produto alinhado")
    args = ap.parse_args()
    gt, nx, ny = janela_alvo()
    if OUT.exists() and not args.forcar:
        print("Já existe:", OUT, "| use --forcar para substituir")
        return
    if not args.baixar:
        print("Produto ainda não baixado; execute com --baixar para gerar", OUT)
        return

    work = OUT.parent / "_anadem_faixas"
    work.mkdir(parents=True, exist_ok=True)
    faixas = []
    for r0 in range(0, ny, MAX_HEIGHT):
        r1 = min(ny, r0 + MAX_HEIGHT)
        for c0 in range(0, nx, MAX_WIDTH):
            c1 = min(nx, c0 + MAX_WIDTH)
            largura, altura = c1 - c0, r1 - r0
            url = url_faixa(transformar_bbox(gt, c0, c1, r0, r1), largura, altura)
            arq = work / f"tile_r{r0:05d}_c{c0:05d}.tif"
            test = gdal.Open(str(arq)) if arq.exists() else None
            if test is not None and test.RasterXSize == largura and test.RasterYSize == altura:
                print("Reutilizando", arq.name)
            else:
                print("Baixando", arq.name, largura, "x", altura, "pixels")
                ultimo = None
                for tentativa in range(1, 5):
                    try:
                        with urlopen(Request(url, headers={"User-Agent": "EUROCLIMA-MIDR/1.0"}), timeout=300) as resp:
                            arq.write_bytes(resp.read())
                        ultimo = None
                        break
                    except HTTPError as e:
                        ultimo = e
                        print("  HTTP", e.code, "— tentativa", tentativa, "; aguardando")
                        time.sleep(8 * tentativa)
                if ultimo is not None:
                    raise ultimo
            test = gdal.Open(str(arq))
            if test is None or test.RasterXSize != largura or test.RasterYSize != altura:
                raise RuntimeError(f"resposta ANADEM inválida em {arq}")
            faixas.append(arq)

    vrt = work / "mosaico.vrt"
    gdal.BuildVRT(str(vrt), [str(x) for x in faixas])
    print("Reamostrando para a grade Fdr.tif")
    gdal.Warp(
        str(OUT), str(vrt), format="GTiff", dstSRS="EPSG:31982",
        outputBounds=(gt[0], gt[3] + ny * gt[5], gt[0] + nx * gt[1], gt[3]),
        width=nx, height=ny, resampleAlg="bilinear", outputType=gdal.GDT_Float32,
        dstNodata=-9999, creationOptions=["TILED=YES", "COMPRESS=DEFLATE"],
    )
    meta = {
        "fonte": SERVICE, "produto": "ANADEM — MDT corrigido de vegetação",
        "resolucao_fonte_m": 30, "crs_saida": "EPSG:31982",
        "grade_saida": "janela de Fdr.tif com buffer de 40 pixels",
        "raster_saida": str(OUT), "faixas": [str(x) for x in faixas],
    }
    (GIS / "00_CATALOGO" / "anadem_metadata.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("Concluído:", OUT)


if __name__ == "__main__":
    main()
