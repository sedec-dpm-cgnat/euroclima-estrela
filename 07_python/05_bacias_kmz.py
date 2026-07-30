# -*- coding: utf-8 -*-
"""
EUROCLIMA / Estrela-RS — delineacao das bacias e curvas CAV para eixos de
barragem fornecidos em KMZ/KML.

Le automaticamente todos os .kmz/.kml da pasta indicada, faz snap na drenagem,
delineia a bacia contribuinte, gera curvas cota-area-volume e exporta
geometrias. Generalizacao do 02_bacias_barragens.py.
"""
import os, re, time, glob, zipfile, warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import geopandas as gpd
from osgeo import gdal, ogr, osr
from scipy import ndimage
from shapely.geometry import Point

gdal.UseExceptions()

GIS = os.environ["GIS"]; SHP = os.environ["SHP"]; OUT = os.environ["SP"]
KMZ = os.environ.get("KMZ", os.path.join(os.path.dirname(GIS), "kmz"))
FDR = os.path.join(GIS, "raster", "Fdr.tif")
MDE = os.path.join(GIS, "raster", "mdr.tif")
UTM22 = 31982

t0 = time.time()
def log(*a): print(f"[{time.time()-t0:7.1f}s]", *a, flush=True)

# ------------------------------------------------------------- 1. le os KMZ
def le_pontos_kmz(pasta):
    pts = []
    for f in sorted(glob.glob(os.path.join(pasta, "*.km[lz]"))):
        if f.lower().endswith(".kmz"):
            with zipfile.ZipFile(f) as z:
                kml = next(n for n in z.namelist() if n.lower().endswith(".kml"))
                txt = z.read(kml).decode("utf-8", "ignore")
        else:
            txt = open(f, encoding="utf-8", errors="ignore").read()
        base = os.path.splitext(os.path.basename(f))[0]
        for m in re.finditer(r"<coordinates>(.*?)</coordinates>", txt, re.S):
            c = m.group(1).split()
            if not c: continue
            lon, lat = float(c[0].split(",")[0]), float(c[0].split(",")[1])
            pts.append(dict(id=base, lon_orig=lon, lat_orig=lat, arquivo=os.path.basename(f)))
    return pts

pontos = le_pontos_kmz(KMZ)
log(f"{len(pontos)} ponto(s) lido(s) de {KMZ}")
for p in pontos:
    log(f"  {p['id']}: {p['lat_orig']:.5f}, {p['lon_orig']:.5f}")

# ---------------------------------------------------------------- 2. rasters
bac_tq = gpd.read_file(os.path.join(SHP, "Bacia_Hidrografica_Taquari.shp")).to_crs(UTM22)
minx, miny, maxx, maxy = bac_tq.total_bounds
ds = gdal.Open(FDR); gt0 = ds.GetGeoTransform()
px = gt0[1]; cell_area = px * abs(gt0[5]); buf = 40 * px
c1 = max(0, int((minx - buf - gt0[0]) / gt0[1]))
c2 = min(ds.RasterXSize, int((maxx + buf - gt0[0]) / gt0[1]) + 1)
r1 = max(0, int((maxy + buf - gt0[3]) / gt0[5]))
r2 = min(ds.RasterYSize, int((miny - buf - gt0[3]) / gt0[5]) + 1)
NX, NY = c2 - c1, r2 - r1; N = NY * NX
gt = (gt0[0] + c1 * gt0[1], gt0[1], 0.0, gt0[3] + r1 * gt0[5], 0.0, gt0[5])
fdr = ds.GetRasterBand(1).ReadAsArray(c1, r1, NX, NY)
dsm = gdal.Open(MDE)
dem = dsm.GetRasterBand(1).ReadAsArray(c1, r1, NX, NY).astype(np.float32)
nd = dsm.GetRasterBand(1).GetNoDataValue()
if nd is not None: dem[dem == nd] = np.nan
log(f"grade {NY}x{NX} = {N/1e6:.1f} M celulas")

def rc(x, y): return int((y - gt[3]) / gt[5]), int((x - gt[0]) / gt[1])
def xy(r, c): return gt[0] + (c + .5) * gt[1], gt[3] + (r + .5) * gt[5]

# ------------------------------------------------------- 3. grafo + acumulacao
DR = {1:0, 2:1, 4:1, 8:1, 16:0, 32:-1, 64:-1, 128:-1}
DC = {1:1, 2:1, 4:0, 8:-1, 16:-1, 32:-1, 64:0, 128:1}
dr = np.zeros(256, np.int8); dc = np.zeros(256, np.int8); ok = np.zeros(256, bool)
for k in DR: dr[k], dc[k], ok[k] = DR[k], DC[k], True
rows = np.repeat(np.arange(NY, dtype=np.int32), NX)
cols = np.tile(np.arange(NX, dtype=np.int32), NY)
f = fdr.ravel()
rr = rows + dr[f]; cc = cols + dc[f]
val = ok[f] & (rr >= 0) & (rr < NY) & (cc >= 0) & (cc < NX)
rec = np.where(val, rr.astype(np.int64) * NX + cc, -1).astype(np.int32)
del rows, cols, rr, cc

tem = rec >= 0
pais = rec[tem].astype(np.int64)
ordf = np.argsort(pais, kind="stable").astype(np.int32)
filhos = np.flatnonzero(tem).astype(np.int32)[ordf]
cnt = np.bincount(pais, minlength=N).astype(np.int32)
off = np.zeros(N + 1, np.int64); np.cumsum(cnt, out=off[1:])
del pais, ordf

log("acumulacao de fluxo...")
indeg = cnt.copy(); acc = np.ones(N, np.int32)
frente = np.flatnonzero(indeg == 0).astype(np.int32)
while frente.size:
    d = rec[frente]; m = d >= 0
    if not m.any(): break
    fs, dsx = frente[m], d[m].astype(np.int64)
    np.add.at(acc, dsx, acc[fs]); np.add.at(indeg, dsx, -1)
    alvo = np.unique(dsx); frente = alvo[indeg[alvo] == 0].astype(np.int32)
log(f"  acumulacao maxima = {acc.max()*cell_area/1e6:,.0f} km2")

def bfs_montante(no):
    sel = np.zeros(N, bool); sel[no] = True
    fr = np.array([no], np.int32)
    while fr.size:
        c_ = cnt[fr]; tot = int(c_.sum())
        if tot == 0: break
        base = np.repeat(off[fr], c_)
        desl = np.arange(tot) - np.repeat(np.cumsum(c_) - c_, c_)
        kids = filhos[(base + desl).astype(np.int64)]
        kids = kids[~sel[kids]]
        if kids.size == 0: break
        sel[kids] = True; fr = kids
    return sel

# --------------------------------------------------------------- 4. snap BHO
bho = gpd.read_file(os.path.join(SHP, "Drenagem_Bacia_Taquari.shp")).to_crs(UTM22)
bho = bho[bho.geometry.notna()].copy(); sidx = bho.sindex

log("snap e delineacao...")
for p in pontos:
    pt22 = gpd.GeoSeries([Point(p["lon_orig"], p["lat_orig"])], crs=4326).to_crs(UTM22).iloc[0]
    p["x"], p["y"] = pt22.x, pt22.y
    cand = bho.iloc[list(sidx.query(pt22.buffer(3000)))].copy()
    cand["d"] = cand.geometry.distance(pt22)
    perto = cand[cand.d < 800]
    ln = (perto.sort_values("nuareamont", ascending=False).iloc[0]
          if len(perto) else cand.sort_values("d").iloc[0])
    p["area_BHO_km2"] = round(float(ln.get("nuareamont", np.nan)), 1)
    p["dist_BHO_m"] = round(float(ln["d"]), 1)

    r0, c0 = rc(pt22.x, pt22.y); alvo = p["area_BHO_km2"]; best = None
    for ddr in range(-5, 6):
        for ddc in range(-5, 6):
            r, c = r0 + ddr, c0 + ddc
            if not (0 <= r < NY and 0 <= c < NX): continue
            i = r * NX + c
            a = acc[i] * cell_area / 1e6
            s = abs(a - alvo) if np.isfinite(alvo) else -a
            if best is None or s < best[0]: best = (s, r, c, a, i)
    _, r, c, a, i = best
    p["r"], p["c"], p["no"] = r, c, i
    p["area_km2"] = round(float(a), 1)
    p["cota_eixo_m"] = round(float(dem[r, c]), 1)
    ll = gpd.GeoSeries([Point(*xy(r, c))], crs=UTM22).to_crs(4326).iloc[0]
    p["lat"], p["lon"] = round(ll.y, 5), round(ll.x, 5)
    p["desloc_snap_m"] = round(Point(*xy(r, c)).distance(pt22), 1)
    p["_mask"] = bfs_montante(i).reshape(NY, NX)
    log(f"  {p['id']}: BHO={alvo:>9.1f} | D8={a:>9.1f} km2 | cota {p['cota_eixo_m']:>6.1f} m "
        f"| snap {p['desloc_snap_m']:>5.1f} m")

# ---------------------------------------------------------------- 5. CAV
ALTURAS = (5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100)
def cav(p):
    m = p["_mask"]; rs, cs = np.where(m)
    a1, a2, b1, b2 = rs.min(), rs.max() + 1, cs.min(), cs.max() + 1
    sm, sz = m[a1:a2, b1:b2], dem[a1:a2, b1:b2]
    lr, lc = p["r"] - a1, p["c"] - b1
    z0 = p["cota_eixo_m"]; est = np.ones((3, 3)); linhas = []
    for h in ALTURAS:
        niv = z0 + h
        lab, _ = ndimage.label(sm & np.isfinite(sz) & (sz <= niv), structure=est)
        if lab[lr, lc] == 0: continue
        res = lab == lab[lr, lc]
        linhas.append(dict(barragem=p["id"], altura_m=h, cota_NA_m=round(niv, 1),
                           area_km2=round(res.sum() * cell_area / 1e6, 2),
                           volume_hm3=round(float(np.nansum(niv - sz[res])) * cell_area / 1e6, 1)))
        p.setdefault("_res", {})[h] = (res, a1, b1)
    return linhas

log("curvas cota-area-volume...")
todas = []
for p in pontos:
    todas += cav(p); log(f"  {p['id']} ok")
cavdf = pd.DataFrame(todas)

# ------------------------------------------------------------ 6. exportacao
def poligoniza(mask2d, campos):
    mem = gdal.GetDriverByName("MEM").Create("", NX, NY, 1, gdal.GDT_Byte)
    mem.SetGeoTransform(gt)
    srs = osr.SpatialReference(); srs.ImportFromEPSG(UTM22)
    mem.SetProjection(srs.ExportToWkt())
    mem.GetRasterBand(1).WriteArray(mask2d.astype(np.uint8))
    tmp = os.path.join(OUT, "_tmp_kmz.geojson")
    if os.path.exists(tmp): os.remove(tmp)
    dsv = ogr.GetDriverByName("GeoJSON").CreateDataSource(tmp)
    lyr = dsv.CreateLayer("p", srs, ogr.wkbPolygon)
    lyr.CreateField(ogr.FieldDefn("val", ogr.OFTInteger))
    gdal.Polygonize(mem.GetRasterBand(1), mem.GetRasterBand(1), lyr, 0)
    dsv = None
    g = gpd.read_file(tmp); os.remove(tmp)
    g = g[g.val == 1].dissolve()
    for k, v in campos.items(): g[k] = v
    return g[list(campos) + ["geometry"]]

DEST = os.path.join(os.environ["EURO"], "05_MODELAGEM")
log("exportando...")
bacs = [poligoniza(p["_mask"], dict(barragem=p["id"], area_km2=p["area_km2"],
                                    cota_eixo_m=p["cota_eixo_m"])) for p in pontos]
gpd.GeoDataFrame(pd.concat(bacs, ignore_index=True), crs=UTM22).to_file(
    os.path.join(DEST, "01_dados", "gis_derivado", "bacias_kmz.gpkg"),
    layer="bacias", driver="GPKG")

reservs = []
for p in pontos:
    for h, (rmask, a1, b1) in p.get("_res", {}).items():
        if h not in (30, 50, 70): continue
        full = np.zeros((NY, NX), bool)
        full[a1:a1 + rmask.shape[0], b1:b1 + rmask.shape[1]] = rmask
        reservs.append(poligoniza(full, dict(barragem=p["id"], altura_m=h,
                                             cota_NA_m=round(p["cota_eixo_m"] + h, 1))))
gpd.GeoDataFrame(pd.concat(reservs, ignore_index=True), crs=UTM22).to_file(
    os.path.join(DEST, "01_dados", "gis_derivado", "reservatorios_kmz.gpkg"),
    layer="reservatorios", driver="GPKG")

res = pd.DataFrame([{k: v for k, v in p.items() if not k.startswith("_")} for p in pontos])
res = res.drop(columns=["x", "y", "r", "c", "no"])
res.to_csv(os.path.join(DEST, "01_dados", "cav", "eixos_kmz.csv"), index=False, sep=";", decimal=",")
cavdf.to_csv(os.path.join(DEST, "01_dados", "cav", "cav_kmz.csv"), index=False, sep=";", decimal=",")

pd.set_option("display.width", 220)
print("\n" + "=" * 104)
print("EIXOS DE BARRAGEM (KMZ) — SINTESE")
print("=" * 104)
print(res.to_string(index=False))
print("\n" + "=" * 104)
print("CURVAS COTA-AREA-VOLUME")
print("=" * 104)
print(cavdf.pivot(index="altura_m", columns="barragem",
                  values=["area_km2", "volume_hm3"]).to_string())
log("FIM")
