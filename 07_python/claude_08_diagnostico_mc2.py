# -*- coding: utf-8 -*-
"""
EUROCLIMA / Estrela-RS — DIAGNOSTICO do eixo exploratorio EIXO-MONTECLARO2.

Na rodada isolada (OUTPUT_TAG=mc2) o eixo recebeu area de drenagem D8 igual a
ZERO, enquanto a BHO indica 12.423,8 km2. Este script apura a causa antes de
qualquer conclusao sobre o candidato:

  1. geometria recebida — extensao, azimute, pontos, altitudes do KML
  2. distancia da linha ao canal D8 (celulas com area acima do limiar)
  3. distancia da linha a drenagem ottocodificada da ANA
  4. varredura da area de drenagem D8 ao longo e ao redor da linha
  5. verificacao do datum das altitudes do KML contra o MDE

Saidas: claude_mc2_diagnostico.csv, claude_mc2_varredura.csv
"""
import os, re, time, zipfile, warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import geopandas as gpd
from osgeo import gdal
from shapely.geometry import Point, LineString

gdal.UseExceptions()

GIS = os.environ["GIS"]; SHP = os.environ["SHP"]
EXTRA = os.environ["EXTRA_KMZ"]
DEST = os.path.join(os.environ["EURO"], "05_MODELAGEM")
D_OUT = os.path.join(DEST, "06_resultados", "CLAUDE")
FDR = os.path.join(GIS, "raster", "Fdr.tif")
MDE = os.path.join(GIS, "raster", "mdr.tif")
UTM22 = 31982
os.makedirs(D_OUT, exist_ok=True)

t0 = time.time()
def log(*a): print(f"[{time.time()-t0:6.1f}s]", *a, flush=True)

# =========================================================== 1. geometria KML
z = zipfile.ZipFile(EXTRA)
kml = next(n for n in z.namelist() if n.lower().endswith(".kml"))
txt = z.read(kml).decode("utf-8", "ignore")
m = re.search(r"<coordinates>(.*?)</coordinates>", txt, re.S)
toks = m.group(1).split()
pts_ll, alt_kml = [], []
for t in toks:
    p = t.split(",")
    pts_ll.append((float(p[0]), float(p[1])))
    alt_kml.append(float(p[2]) if len(p) > 2 else np.nan)

ln = gpd.GeoSeries([LineString(pts_ll)], crs=4326).to_crs(UTM22).iloc[0]
cen = ln.centroid
cen_ll = gpd.GeoSeries([cen], crs=UTM22).to_crs(4326).iloc[0]

print("=" * 100)
print("1. GEOMETRIA RECEBIDA")
print("=" * 100)
print(f"  arquivo ............. {os.path.basename(EXTRA)}")
print(f"  vertices ............ {len(pts_ll)}")
print(f"  extensao ............ {ln.length:,.1f} m")
p0 = gpd.GeoSeries([Point(pts_ll[0])], crs=4326).to_crs(UTM22).iloc[0]
p1 = gpd.GeoSeries([Point(pts_ll[-1])], crs=4326).to_crs(UTM22).iloc[0]
az = (np.degrees(np.arctan2(p1.x - p0.x, p1.y - p0.y)) + 360) % 360
print(f"  azimute ............. {az:.1f} graus")
print(f"  ponto medio ......... {cen_ll.y:.7f}, {cen_ll.x:.7f}")
print(f"  altitudes do KML .... {alt_kml[0]:.1f} m -> {alt_kml[-1]:.1f} m")

# =========================================================== 2. grade e canal
bac = gpd.read_file(os.path.join(SHP, "Bacia_Hidrografica_Taquari.shp")).to_crs(UTM22)
bx = bac.total_bounds
ds = gdal.Open(FDR); gt0 = ds.GetGeoTransform()
px = gt0[1]; cell = px * abs(gt0[5]); buf = 40 * px
c1 = max(0, int((bx[0] - buf - gt0[0]) / gt0[1]))
c2 = min(ds.RasterXSize, int((bx[2] + buf - gt0[0]) / gt0[1]) + 1)
r1 = max(0, int((bx[3] + buf - gt0[3]) / gt0[5]))
r2 = min(ds.RasterYSize, int((bx[1] - buf - gt0[3]) / gt0[5]) + 1)
NX, NY = c2 - c1, r2 - r1; N = NY * NX
gt = (gt0[0] + c1 * gt0[1], gt0[1], 0.0, gt0[3] + r1 * gt0[5], 0.0, gt0[5])
fdr = ds.GetRasterBand(1).ReadAsArray(c1, r1, NX, NY)
dsm = gdal.Open(MDE)
dem = dsm.GetRasterBand(1).ReadAsArray(c1, r1, NX, NY).astype(np.float32)
ndv = dsm.GetRasterBand(1).GetNoDataValue()
if ndv is not None: dem[dem == ndv] = np.nan

def rc(x, y): return int((y - gt[3]) / gt[5]), int((x - gt[0]) / gt[1])
def xy(r, c): return gt[0] + (c + .5) * gt[1], gt[3] + (r + .5) * gt[5]

DR = {1:0, 2:1, 4:1, 8:1, 16:0, 32:-1, 64:-1, 128:-1}
DC = {1:1, 2:1, 4:0, 8:-1, 16:-1, 32:-1, 64:0, 128:1}
dra = np.zeros(256, np.int8); dca = np.zeros(256, np.int8); okv = np.zeros(256, bool)
for k in DR: dra[k], dca[k], okv[k] = DR[k], DC[k], True
rows = np.repeat(np.arange(NY, dtype=np.int32), NX)
cols = np.tile(np.arange(NX, dtype=np.int32), NY)
f = fdr.ravel()
rr = rows + dra[f]; cc = cols + dca[f]
val = okv[f] & (rr >= 0) & (rr < NY) & (cc >= 0) & (cc < NX)
rec = np.where(val, rr.astype(np.int64) * NX + cc, -1).astype(np.int32)
del rows, cols, rr, cc
log("acumulacao...")
tem = rec >= 0
cnt = np.bincount(rec[tem].astype(np.int64), minlength=N).astype(np.int32)
indeg = cnt.copy(); acc = np.ones(N, np.int32)
fr = np.flatnonzero(indeg == 0).astype(np.int32)
while fr.size:
    d = rec[fr]; m_ = d >= 0
    if not m_.any(): break
    fs, dx = fr[m_], d[m_].astype(np.int64)
    np.add.at(acc, dx, acc[fs]); np.add.at(indeg, dx, -1)
    al = np.unique(dx); fr = al[indeg[al] == 0].astype(np.int32)
area = acc.astype(np.float32) * cell / 1e6
log(f"  area maxima {area.max():,.0f} km2")

# ================================================ 3. varredura ao longo da linha
print("\n" + "=" * 100)
print("2. VARREDURA DA AREA DE DRENAGEM D8 AO LONGO DA LINHA")
print("=" * 100)
regs = []
for s in np.arange(0, ln.length + 1, 25.0):
    p = ln.interpolate(min(s, ln.length))
    r_, c_ = rc(p.x, p.y)
    if not (0 <= r_ < NY and 0 <= c_ < NX): continue
    i = r_ * NX + c_
    regs.append(dict(dist_m=round(float(s), 1), x=p.x, y=p.y,
                     area_D8_km2=round(float(area[i]), 3),
                     cota_MDE_m=round(float(dem[r_, c_]), 1)))
vr = pd.DataFrame(regs)
print(vr.to_string(index=False))
print(f"\n  area D8 MAXIMA sobre a linha: {vr.area_D8_km2.max():,.3f} km2")

# ---------------------------------- busca do canal mais proximo, raio crescente
print("\n" + "=" * 100)
print("3. DISTANCIA AO CANAL D8 (celulas com area >= 1.000 km2)")
print("=" * 100)
LIM = 1000.0
canal = (area >= LIM).reshape(NY, NX)
rr_, cc_ = np.where(canal)
xs = gt[0] + (cc_ + .5) * gt[1]
ys = gt[3] + (rr_ + .5) * gt[5]
d2 = (xs - cen.x) ** 2 + (ys - cen.y) ** 2
k = int(np.argmin(d2))
dmin = float(np.sqrt(d2[k]))
i_can = int(rr_[k]) * NX + int(cc_[k])
ll_can = gpd.GeoSeries([Point(xs[k], ys[k])], crs=UTM22).to_crs(4326).iloc[0]
print(f"  canal D8 mais proximo do ponto medio: {dmin:,.0f} m")
print(f"    area la: {area[i_can]:,.1f} km2 | cota {dem[int(rr_[k]), int(cc_[k])]:.1f} m")
print(f"    coordenadas: {ll_can.y:.6f}, {ll_can.x:.6f}")

# ------------------------------------------------------------ 4. BHO
print("\n" + "=" * 100)
print("4. DISTANCIA A DRENAGEM OTTOCODIFICADA (BHO/ANA)")
print("=" * 100)
bho = gpd.read_file(os.path.join(SHP, "Drenagem_Bacia_Taquari.shp")).to_crs(UTM22)
bho = bho[bho.geometry.notna()].copy()
bho["d"] = bho.geometry.distance(ln)
perto = bho.nsmallest(5, "d")[["cocursodag", "nuareamont", "d"]]
print(perto.to_string(index=False))
d_bho = float(perto.d.iloc[0])
print(f"\n  trecho BHO mais proximo: {d_bho:,.0f} m, "
      f"area de montante {perto.nuareamont.iloc[0]:,.1f} km2")

# =============================================== 5. datum das altitudes do KML
print("\n" + "=" * 100)
print("5. ALTITUDES DO KML x MDE")
print("=" * 100)
for j, (llx, lly) in enumerate(pts_ll):
    p = gpd.GeoSeries([Point(llx, lly)], crs=4326).to_crs(UTM22).iloc[0]
    r_, c_ = rc(p.x, p.y)
    zm = float(dem[r_, c_]) if (0 <= r_ < NY and 0 <= c_ < NX) else np.nan
    print(f"  vertice {j+1}: KML {alt_kml[j]:8.1f} m | MDE {zm:7.1f} m | "
          f"diferenca {alt_kml[j]-zm:+8.1f} m")
print("\n  As altitudes do KML sao do Google Earth (referencial proprio) e NAO")
print("  devem ser usadas como cota de projeto, conforme o plano de trabalho.")

# ------------------------------------------------------------------- saidas
vr.to_csv(os.path.join(D_OUT, "claude_mc2_varredura.csv"),
          index=False, sep=";", decimal=",")
diag = pd.DataFrame([dict(
    arquivo=os.path.basename(EXTRA), vertices=len(pts_ll),
    extensao_m=round(ln.length, 1), azimute_graus=round(az, 1),
    lat_medio=round(cen_ll.y, 7), lon_medio=round(cen_ll.x, 7),
    alt_kml_ini_m=alt_kml[0], alt_kml_fim_m=alt_kml[-1],
    area_D8_max_sobre_linha_km2=round(float(vr.area_D8_km2.max()), 3),
    dist_ao_canal_D8_m=round(dmin, 0),
    area_no_canal_D8_km2=round(float(area[i_can]), 1),
    dist_a_BHO_m=round(d_bho, 0),
    area_BHO_km2=round(float(perto.nuareamont.iloc[0]), 1),
    cota_MDE_ponto_medio_m=round(float(dem[rc(cen.x, cen.y)]), 1))])
diag.to_csv(os.path.join(D_OUT, "claude_mc2_diagnostico.csv"),
            index=False, sep=";", decimal=",")

print("\n" + "=" * 100)
print("DIAGNOSTICO")
print("=" * 100)
if vr.area_D8_km2.max() < 100:
    print("  A linha NAO cruza o canal principal na grade D8.")
    print(f"  Area maxima sobre a linha: {vr.area_D8_km2.max():.1f} km2 — e' encosta/cabeceira.")
    print(f"  O canal com mais de {LIM:.0f} km2 esta a {dmin:,.0f} m do ponto medio.")
    print(f"  A BHO mais proxima esta a {d_bho:,.0f} m.")
    print("\n  Como o pipeline ancora pela BHO e depois busca a celula D8 numa")
    print("  janela de +/-10 celulas (+/-286 m), a ancoragem falhou e a area")
    print("  saiu ZERO. O resultado da rodada mc2 para este eixo NAO e' valido.")
else:
    print("  A linha cruza o canal; a falha de ancoragem tem outra causa.")
log("FIM")
