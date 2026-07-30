# -*- coding: utf-8 -*-
"""
EUROCLIMA / Estrela-RS — aproveitamentos EXISTENTES e EM ESTUDO na bacia
do Taquari-Antas.

Objetivo (item 4.6.1 do Manual de Inventario Hidroeletrico, MME 2007):
  - o nivel de agua normal a jusante (NAjn) de um aproveitamento e' o nivel
    natural no local OU o NA maximo normal do reservatorio imediatamente a
    jusante, se este for mais elevado;
  - eixos propostos nao podem ter o pe afogado pelo remanso de um reservatorio
    existente, nem o seu proprio remanso invadir o NA de outro.

Fontes (dados abertos):
  - ANEEL SIGA .................. empreendimentos de geracao em operacao
  - ANEEL ....................... empreendimentos hidreletricos em estudo
                                  (inventario/viabilidade ja registrados)

Saidas: aproveitamentos_existentes.csv, conflitos_remanso.csv,
        aproveitamentos.gpkg
"""
import os, io, time, warnings, urllib.request
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import geopandas as gpd
from osgeo import gdal
from shapely.geometry import Point

gdal.UseExceptions()

GIS = os.environ["GIS"]; SHP = os.environ["SHP"]
DEST = os.path.join(os.environ["EURO"], "05_MODELAGEM")
D_GIS = os.path.join(DEST, "01_dados", "gis_derivado")
D_TAB = os.path.join(DEST, "06_resultados", "tabelas")
D_CAV = os.path.join(DEST, "01_dados", "cav")
D_RAW = os.path.join(DEST, "01_dados", "aneel")
FDR = os.path.join(GIS, "raster", "Fdr.tif")
MDE = os.path.join(GIS, "raster", "mdr.tif")
UTM22 = 31982
for d in (D_GIS, D_TAB, D_RAW): os.makedirs(d, exist_ok=True)

t0 = time.time()
def log(*a): print(f"[{time.time()-t0:7.1f}s]", *a, flush=True)

FONTES = {
    "operacao": "https://dadosabertos.aneel.gov.br/dataset/6d90b77c-c5f5-4d81-bdec-7bc619494bb9/"
                "resource/11ec447d-698d-4ab8-977f-b424d5deee6a/download/siga-empreendimentos-geracao.csv",
    "estudo":   "https://dadosabertos.aneel.gov.br/dataset/fb81a809-e0eb-4acb-b589-3130380cd9f4/"
                "resource/cdb7f515-f90c-4727-8ff8-109d78991dcb/download/empreendimento-hidreletrico-estudo.csv",
}

def baixa(nome, url):
    dest = os.path.join(D_RAW, f"aneel_{nome}.csv")
    if os.path.exists(dest) and os.path.getsize(dest) > 1000:
        log(f"  {nome}: ja baixado")
        return dest
    log(f"  baixando {nome}...")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=240) as r, open(dest, "wb") as f:
            f.write(r.read())
        log(f"    {os.path.getsize(dest)/1e6:.1f} MB")
        return dest
    except Exception as e:
        log(f"    FALHA: {e}")
        return None

def le_csv(p):
    for enc in ("utf-8-sig", "latin-1"):
        for sep in (";", ","):
            try:
                d = pd.read_csv(p, sep=sep, encoding=enc, low_memory=False,
                                skiprows=lambda i: False)
                if d.shape[1] > 3:
                    return d
            except Exception:
                continue
    return None

log("=== ANEEL — dados abertos ===")
tabs = {}
for k, u in FONTES.items():
    p = baixa(k, u)
    if p:
        d = le_csv(p)
        if d is not None:
            tabs[k] = d
            log(f"  {k}: {d.shape[0]} linhas x {d.shape[1]} colunas")

if not tabs:
    raise SystemExit("nenhuma fonte disponivel — rode novamente com internet")

for k, d in tabs.items():
    log(f"\ncolunas de '{k}':")
    log("  " + " | ".join(list(d.columns)[:28]))

# --------------------------------------------------- localiza lat/lon e filtra
def acha_col(cols, *chaves):
    for c in cols:
        cl = c.lower()
        if all(x in cl for x in chaves):
            return c
    return None

bac = gpd.read_file(os.path.join(SHP, "Bacia_Hidrografica_Taquari.shp")).to_crs(4674)
bac_u = bac.geometry.union_all() if hasattr(bac.geometry, "union_all") else bac.geometry.unary_union

registros = []
for k, d in tabs.items():
    clat = (acha_col(d.columns, "lat") or acha_col(d.columns, "coordn")
            or acha_col(d.columns, "nulatitude"))
    clon = (acha_col(d.columns, "long") or acha_col(d.columns, "coorde")
            or acha_col(d.columns, "nulongitude"))
    if not clat or not clon:
        log(f"  {k}: sem colunas de coordenada — pulando")
        continue
    dd = d.copy()
    for c in (clat, clon):
        dd[c] = (dd[c].astype(str).str.replace(",", ".", regex=False)
                 .str.extract(r"(-?\d+\.?\d*)")[0].astype(float))
    dd = dd.dropna(subset=[clat, clon])
    # so hidraulicas
    ctipo = acha_col(dd.columns, "sigtipogeracao") or acha_col(dd.columns, "tipo")
    if ctipo is not None:
        m = dd[ctipo].astype(str).str.upper().str.contains(
            "HID|UHE|PCH|CGH|CENTRAL GERADORA HID", na=False)
        if m.any(): dd = dd[m]
    g = gpd.GeoDataFrame(dd, geometry=gpd.points_from_xy(dd[clon], dd[clat]), crs=4674)
    g = g[g.geometry.within(bac_u)]
    log(f"  {k}: {len(g)} aproveitamento(s) dentro da bacia Taquari-Antas")
    if len(g) == 0: continue
    cnome = acha_col(g.columns, "nome") or acha_col(g.columns, "nom")
    cpot  = acha_col(g.columns, "potencia") or acha_col(g.columns, "pot")
    cmun  = acha_col(g.columns, "municip")
    for _, r in g.iterrows():
        registros.append(dict(
            situacao=k,
            nome=str(r[cnome])[:60] if cnome else "",
            potencia_kW=r[cpot] if cpot else np.nan,
            municipio=str(r[cmun])[:40] if cmun else "",
            lat=r[clat], lon=r[clon], geometry=r.geometry))

if not registros:
    raise SystemExit("nenhum aproveitamento na bacia — verificar filtros")

apr = gpd.GeoDataFrame(registros, crs=4674).to_crs(UTM22)
log(f"\ntotal na bacia: {len(apr)}")

# ------------------------------------------- area de drenagem e cota de cada um
log("ancorando na drenagem e amostrando o MDE...")
bho = gpd.read_file(os.path.join(SHP, "Drenagem_Bacia_Taquari.shp")).to_crs(UTM22)
bho = bho[bho.geometry.notna()].copy()
ds = gdal.Open(MDE); gt = ds.GetGeoTransform()
band = ds.GetRasterBand(1); ndv = band.GetNoDataValue()

def cota(x, y):
    c = int((x - gt[0]) / gt[1]); r = int((y - gt[3]) / gt[5])
    if not (0 <= r < ds.RasterYSize and 0 <= c < ds.RasterXSize): return np.nan
    v = band.ReadAsArray(c, r, 1, 1)
    if v is None: return np.nan
    v = float(v[0, 0])
    return np.nan if (ndv is not None and v == ndv) else v

sidx = bho.sindex
areas, cotas, rios = [], [], []
for _, r in apr.iterrows():
    cand = bho.iloc[list(sidx.query(r.geometry.buffer(2500)))].copy()
    if len(cand):
        cand["d"] = cand.geometry.distance(r.geometry)
        ln = cand.sort_values("nuareamont", ascending=False).iloc[0]
        areas.append(float(ln.get("nuareamont", np.nan)))
        rios.append(str(ln.get("cocursodag", ""))[:20])
    else:
        areas.append(np.nan); rios.append("")
    cotas.append(cota(r.geometry.x, r.geometry.y))
apr["area_drenagem_km2"] = np.round(areas, 1)
apr["cota_terreno_m"] = np.round(cotas, 1)
apr["curso_dagua"] = rios
apr = apr.sort_values("area_drenagem_km2")

pd.set_option("display.width", 210)
print("\n" + "=" * 105)
print("APROVEITAMENTOS NA BACIA TAQUARI-ANTAS")
print("=" * 105)
print(apr[["situacao", "nome", "potencia_kW", "municipio",
           "area_drenagem_km2", "cota_terreno_m", "lat", "lon"]].to_string(index=False))

apr.drop(columns="geometry").to_csv(
    os.path.join(D_TAB, "aproveitamentos_existentes.csv"), index=False, sep=";", decimal=",")
apr.to_file(os.path.join(D_GIS, "aproveitamentos.gpkg"), layer="aneel", driver="GPKG")

# ------------------------------------------- conflito com os eixos propostos
eix_p = os.path.join(D_CAV, "eixos_todos.csv")
if os.path.exists(eix_p):
    eixos = pd.read_csv(eix_p, sep=";", decimal=",")
    geo = pd.read_csv(os.path.join(D_CAV, "geometria_todos.csv"), sep=";", decimal=",")
    log("\navaliando conflitos de remanso...")
    conf = []
    for _, e in eixos.iterrows():
        # cota do NA para cada altura considerada
        sub = geo[geo.eixo == e.codigo]
        for _, a in apr.iterrows():
            if not np.isfinite(a.area_drenagem_km2): continue
            # existente esta A MONTANTE do eixo se tem area menor no mesmo rio
            montante = a.area_drenagem_km2 < e.area_km2
            if not montante: continue
            # o remanso do eixo afoga o existente se NA do eixo > cota do existente
            for _, s in sub.iterrows():
                if s.cota_NA_m > a.cota_terreno_m:
                    conf.append(dict(eixo=e.codigo, altura_m=s.altura_m,
                                     cota_NA_eixo_m=s.cota_NA_m,
                                     aproveitamento=a["nome"], situacao=a.situacao,
                                     potencia_kW=a.potencia_kW,
                                     cota_existente_m=a.cota_terreno_m,
                                     area_exist_km2=a.area_drenagem_km2,
                                     afogamento_m=round(s.cota_NA_m - a.cota_terreno_m, 1)))
                    break     # primeira altura que causa conflito
    cdf = pd.DataFrame(conf)
    if len(cdf):
        cdf = cdf.sort_values(["eixo", "altura_m"])
        cdf.to_csv(os.path.join(D_TAB, "conflitos_remanso.csv"),
                   index=False, sep=";", decimal=",")
        print("\n" + "=" * 105)
        print("CONFLITOS DE REMANSO — altura minima do eixo que afoga cada aproveitamento")
        print("=" * 105)
        print(cdf.to_string(index=False))
        print("\n  Interpretacao: acima da altura indicada, o remanso do eixo proposto")
        print("  atinge a cota do aproveitamento existente/em estudo. Nessas condicoes")
        print("  o NAjn do eixo de montante passa a ser o NA do reservatorio de jusante")
        print("  (item 4.6.1 do Manual de Inventario) e ha' perda de queda.")
    else:
        print("\n  nenhum conflito de remanso identificado")
log("FIM")
