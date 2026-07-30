# -*- coding: utf-8 -*-
"""
EUROCLIMA / Estrela-RS — Passo 2
Delineacao das bacias contribuintes dos eixos de barragem candidatos e
curvas Cota-Area-Volume (CAV) dos reservatorios.

Entradas : Fdr.tif  (D8 ArcGIS, 28,6 m, EPSG:31982)
           mdr.tif  (MDE, mesma grade)
           Barragem_A/A2/B.shp
           Drenagem_Bacia_Taquari.shp (BHO/ANA -> nuareamont)
Saidas   : eixos_barragens.csv, cav_barragens.csv, bacias_barragens.gpkg,
           reservatorios_barragens.gpkg
"""
import os, time, warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import geopandas as gpd
from osgeo import gdal, ogr, osr
from scipy import ndimage
from shapely.geometry import Point

gdal.UseExceptions()

GIS = os.environ["GIS"]; SHP = os.environ["SHP"]; OUT = os.environ["SP"]
FDR = os.path.join(GIS, "raster", "Fdr.tif")
MDE = os.path.join(GIS, "raster", "mdr.tif")
UTM22 = 31982

t0 = time.time()
def log(*a): print(f"[{time.time()-t0:7.1f}s]", *a, flush=True)

# ------------------------------------------------------------------ 1. recorte
bac_tq = gpd.read_file(os.path.join(SHP, "Bacia_Hidrografica_Taquari.shp")).to_crs(UTM22)
minx, miny, maxx, maxy = bac_tq.total_bounds
log(f"bbox bacia Taquari-Antas: {minx:.0f},{miny:.0f} -> {maxx:.0f},{maxy:.0f}")

ds = gdal.Open(FDR); gt0 = ds.GetGeoTransform()
px = gt0[1]; cell_area = px * abs(gt0[5])
buf = 40 * px
c1 = max(0, int((minx - buf - gt0[0]) / gt0[1]))
c2 = min(ds.RasterXSize, int((maxx + buf - gt0[0]) / gt0[1]) + 1)
r1 = max(0, int((maxy + buf - gt0[3]) / gt0[5]))
r2 = min(ds.RasterYSize, int((miny - buf - gt0[3]) / gt0[5]) + 1)
NX, NY = c2 - c1, r2 - r1
gt = (gt0[0] + c1 * gt0[1], gt0[1], 0.0, gt0[3] + r1 * gt0[5], 0.0, gt0[5])
log(f"recorte {NY} x {NX} = {NY*NX/1e6:.1f} M celulas  ({cell_area:,.0f} m2/celula)")

fdr = ds.GetRasterBand(1).ReadAsArray(c1, r1, NX, NY)
dsm = gdal.Open(MDE)
dem = dsm.GetRasterBand(1).ReadAsArray(c1, r1, NX, NY).astype(np.float32)
nd = dsm.GetRasterBand(1).GetNoDataValue()
if nd is not None: dem[dem == nd] = np.nan
log(f"Fdr codigos={np.unique(fdr)}  MDE {np.nanmin(dem):.0f}-{np.nanmax(dem):.0f} m")

def rc(x, y): return int((y - gt[3]) / gt[5]), int((x - gt[0]) / gt[1])
def xy(r, c): return gt[0] + (c + .5) * gt[1], gt[3] + (r + .5) * gt[5]

# ------------------------------------------------- 2. receptor D8 (vetorizado)
# ArcGIS D8: 1=E 2=SE 4=S 8=SW 16=W 32=NW 64=N 128=NE
DR = {1:0, 2:1, 4:1, 8:1, 16:0, 32:-1, 64:-1, 128:-1}
DC = {1:1, 2:1, 4:0, 8:-1, 16:-1, 32:-1, 64:0, 128:1}
log("montando grafo de drenagem...")
N = NY * NX
dr = np.zeros(256, np.int8); dc = np.zeros(256, np.int8); ok = np.zeros(256, bool)
for k in DR: dr[k], dc[k], ok[k] = DR[k], DC[k], True
rows = np.repeat(np.arange(NY, dtype=np.int32), NX)
cols = np.tile(np.arange(NX, dtype=np.int32), NY)
f = fdr.ravel()
rr = rows + dr[f]; cc = cols + dc[f]
valido = ok[f] & (rr >= 0) & (rr < NY) & (cc >= 0) & (cc < NX)
rec = np.where(valido, rr.astype(np.int64) * NX + cc, -1).astype(np.int32)
del rows, cols, rr, cc
log(f"  celulas com receptor: {valido.sum()/1e6:.1f} M de {N/1e6:.1f} M")

# --------------------------------- 3. CSR de filhos (para BFS a montante)
log("indexando montantes (CSR)...")
tem = rec >= 0
pais = rec[tem].astype(np.int64)
filhos_ord = np.argsort(pais, kind="stable").astype(np.int32)
filhos = np.flatnonzero(tem).astype(np.int32)[filhos_ord]
cnt = np.bincount(pais, minlength=N).astype(np.int32)
off = np.zeros(N + 1, np.int64); np.cumsum(cnt, out=off[1:])
del pais, filhos_ord

# --------------------------------------------- 4. acumulacao de fluxo (peeling)
log("calculando acumulacao de fluxo...")
indeg = cnt.copy()
acc = np.ones(N, np.int32)
frente = np.flatnonzero(indeg == 0).astype(np.int32)
ondas = 0
while frente.size:
    ondas += 1
    d = rec[frente]
    m = d >= 0
    if not m.any(): break
    fs, dsx = frente[m], d[m].astype(np.int64)
    np.add.at(acc, dsx, acc[fs])
    np.add.at(indeg, dsx, -1)
    alvo = np.unique(dsx)
    frente = alvo[indeg[alvo] == 0].astype(np.int32)
log(f"  {ondas} ondas; acumulacao max = {acc.max()*cell_area/1e6:,.0f} km2")

def bfs_montante(no):
    """Bacia a montante do no (indice plano) — BFS vetorizado pelo CSR."""
    sel = np.zeros(N, bool); sel[no] = True
    fr = np.array([no], np.int32)
    while fr.size:
        c_ = cnt[fr]
        tot = int(c_.sum())
        if tot == 0: break
        base = np.repeat(off[fr], c_)
        desl = np.arange(tot) - np.repeat(np.cumsum(c_) - c_, c_)
        kids = filhos[(base + desl).astype(np.int64)]
        kids = kids[~sel[kids]]
        if kids.size == 0: break
        sel[kids] = True
        fr = kids
    return sel

# --------------------------------------------------- 5. eixos + snap + bacias
log("carregando eixos e BHO...")
eixos = []
for nome, arq in [("BAR-A", "Barragem_A"), ("BAR-A2", "Barragem_A2"), ("BAR-B", "Barragem_B")]:
    g = gpd.read_file(os.path.join(SHP, arq + ".shp")).to_crs(UTM22)
    p = g.geometry.iloc[0]
    eixos.append(dict(id=nome, arquivo_origem=arq, x=p.x, y=p.y))

bho = gpd.read_file(os.path.join(SHP, "Drenagem_Bacia_Taquari.shp")).to_crs(UTM22)
bho = bho[bho.geometry.notna()].copy()
sidx = bho.sindex

for e in eixos:
    pt = Point(e["x"], e["y"])
    cand = bho.iloc[list(sidx.query(pt.buffer(2000)))].copy()
    cand["d"] = cand.geometry.distance(pt)
    perto = cand[cand.d < 600]
    ln = (perto.sort_values("nuareamont", ascending=False).iloc[0]
          if len(perto) else cand.sort_values("d").iloc[0])
    e["area_BHO_km2"] = round(float(ln.get("nuareamont", np.nan)), 1)
    e["dist_drenagem_m"] = round(float(ln["d"]), 1)

log("snap na celula de drenagem (janela 9x9, alvo = area BHO)...")
for e in eixos:
    r0, c0 = rc(e["x"], e["y"])
    alvo = e["area_BHO_km2"]
    best = None
    for ddr in range(-4, 5):
        for ddc in range(-4, 5):
            r, c = r0 + ddr, c0 + ddc
            if not (0 <= r < NY and 0 <= c < NX): continue
            i = r * NX + c
            a = acc[i] * cell_area / 1e6
            s = abs(a - alvo) if np.isfinite(alvo) else -a
            if best is None or s < best[0]: best = (s, r, c, a, i)
    _, r, c, a, i = best
    e["r"], e["c"], e["no"] = r, c, i
    e["area_bacia_km2"] = round(float(a), 1)
    e["cota_eixo_m"] = round(float(dem[r, c]), 1)
    ll = gpd.GeoSeries([Point(*xy(r, c))], crs=UTM22).to_crs(4326).iloc[0]
    e["lat"], e["lon"] = round(ll.y, 5), round(ll.x, 5)
    log(f"  {e['id']}: BHO={alvo:>8.1f} km2 | D8={a:>8.1f} km2 | cota {e['cota_eixo_m']:>6.1f} m "
        f"| ({e['lat']}, {e['lon']}) | snap {e['dist_drenagem_m']} m")

log("delineando bacias...")
for e in eixos:
    sel = bfs_montante(e["no"])
    e["_mask"] = sel.reshape(NY, NX)
    log(f"  {e['id']}: {sel.sum()*cell_area/1e6:,.1f} km2")

# --------------------------------------------------------- 6. curvas CAV
def cav(e, alturas=(5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80)):
    m = e["_mask"]
    rs, cs = np.where(m)
    a1, a2, b1, b2 = rs.min(), rs.max() + 1, cs.min(), cs.max() + 1
    sm, sz = m[a1:a2, b1:b2], dem[a1:a2, b1:b2]
    lr, lc = e["r"] - a1, e["c"] - b1
    z0 = e["cota_eixo_m"]
    linhas = []
    est = np.ones((3, 3))
    for h in alturas:
        niv = z0 + h
        cand = sm & np.isfinite(sz) & (sz <= niv)
        lab, _ = ndimage.label(cand, structure=est)
        if lab[lr, lc] == 0: continue
        res = lab == lab[lr, lc]
        area = res.sum() * cell_area / 1e6
        vol = float(np.nansum(niv - sz[res])) * cell_area / 1e6
        linhas.append(dict(barragem=e["id"], altura_m=h, cota_NA_m=round(niv, 1),
                           area_km2=round(area, 2), volume_hm3=round(vol, 1)))
        e.setdefault("_res", {})[h] = (res, a1, b1)
    return linhas

log("curvas cota-area-volume...")
todas = []
for e in eixos:
    todas += cav(e); log(f"  {e['id']} ok")
cavdf = pd.DataFrame(todas)
cavdf.to_csv(os.path.join(OUT, "cav_barragens.csv"), index=False, sep=";", decimal=",")

res = pd.DataFrame([{k: v for k, v in e.items() if not k.startswith("_")} for e in eixos])
res.drop(columns=["x", "y", "r", "c", "no"]).to_csv(
    os.path.join(OUT, "eixos_barragens.csv"), index=False, sep=";", decimal=",")

# ------------------------------------------------------------ 7. geometrias
def poligoniza(mask2d, campos):
    mem = gdal.GetDriverByName("MEM").Create("", NX, NY, 1, gdal.GDT_Byte)
    mem.SetGeoTransform(gt)
    srs = osr.SpatialReference(); srs.ImportFromEPSG(UTM22)
    mem.SetProjection(srs.ExportToWkt())
    mem.GetRasterBand(1).WriteArray(mask2d.astype(np.uint8))
    tmp = os.path.join(OUT, "_tmp_poly.geojson")
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

log("exportando geometrias...")
bacs = [poligoniza(e["_mask"], dict(barragem=e["id"], area_km2=e["area_bacia_km2"],
                                    cota_eixo_m=e["cota_eixo_m"])) for e in eixos]
gpd.GeoDataFrame(pd.concat(bacs, ignore_index=True), crs=UTM22).to_file(
    os.path.join(OUT, "bacias_barragens.gpkg"), layer="bacias", driver="GPKG")

reservs = []
for e in eixos:
    for h, (rmask, a1, b1) in e.get("_res", {}).items():
        if h not in (20, 30, 40): continue
        full = np.zeros((NY, NX), bool)
        full[a1:a1 + rmask.shape[0], b1:b1 + rmask.shape[1]] = rmask
        reservs.append(poligoniza(full, dict(barragem=e["id"], altura_m=h,
                                             cota_NA_m=round(e["cota_eixo_m"] + h, 1))))
gpd.GeoDataFrame(pd.concat(reservs, ignore_index=True), crs=UTM22).to_file(
    os.path.join(OUT, "reservatorios_barragens.gpkg"), layer="reservatorios", driver="GPKG")

print("\n" + "=" * 100)
print("EIXOS DE BARRAGEM CANDIDATOS — SINTESE")
print("=" * 100)
pd.set_option("display.width", 200)
print(res.drop(columns=["x", "y", "r", "c", "no"]).to_string(index=False))
print("\n" + "=" * 100)
print("CURVAS COTA-AREA-VOLUME  (area em km2 / volume em hm3)")
print("=" * 100)
print(cavdf.pivot(index="altura_m", columns="barragem",
                  values=["area_km2", "volume_hm3"]).to_string())
log("FIM")
