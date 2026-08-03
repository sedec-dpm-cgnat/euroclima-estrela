# -*- coding: utf-8 -*-
"""
EUROCLIMA / Estrela-RS — manchas de inundacao COM e SEM barragens,
do eixo barrado ate Bom Retiro do Sul.

Metodo: HAND (Height Above Nearest Drainage) + curva-chave sintetica de
Manning por trecho (Rennó et al. 2008; Nobre et al. 2011; Goerl et al.,
"O modelo HAND como ferramenta de mapeamento de áreas propensas a inundar",
XX Simpósio Brasileiro de Recursos Hídricos). O HAND é usado como triagem;
os parâmetros precisam ser calibrados contra dados observados antes de
interpretar as manchas como resultado hidráulico definitivo.

Arquitetura em dois estagios, por desempenho:
  ESTAGIO 1 — acumulacao de fluxo sobre a BACIA INTEIRA (51 M celulas)
  ESTAGIO 2 — HAND, curvas-chave e mapeamento apenas no CORREDOR (12 M)

Saidas: mancha_<cenario>.tif, mancha_diferenca.tif, manchas.gpkg,
        perfil_linha_dagua.csv, manchas_por_municipio.csv
"""
import os, re, time, zipfile, warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import geopandas as gpd
from osgeo import gdal, ogr, osr
from scipy import ndimage
from shapely.geometry import LineString

gdal.UseExceptions()

GIS = os.environ["GIS"]; SHP = os.environ["SHP"]; KMZ = os.environ["KMZ"]
DEST = os.path.join(os.environ["EURO"], "05_MODELAGEM")
D_GIS = os.path.join(DEST, "01_dados", "gis_derivado")
D_TAB = os.path.join(DEST, "06_resultados", "tabelas")
FDR = os.path.join(GIS, "raster", "Fdr.tif")
MDE = os.path.join(GIS, "raster", "mdr.tif")
UTM22 = 31982
os.makedirs(D_GIS, exist_ok=True); os.makedirs(D_TAB, exist_ok=True)

t0 = time.time()
def log(*a): print(f"[{time.time()-t0:7.1f}s]", *a, flush=True)

MANNING_CANAL    = 0.035
MANNING_PLANICIE = 0.070
LIM_CANAL_KM2    = 150.0
HAND_MAX         = 45.0
N_CELULAS_TRECHO = 40          # celulas de canal por trecho de calculo

# =========================================================== 1. areas e eixos
mun = gpd.read_file(os.path.join(SHP, "Municipios_RS.shp")).to_crs(UTM22)
CORREDOR = ["Muçum", "Roca Sales", "Encantado", "Colinas", "Arroio do Meio",
            "Cruzeiro do Sul", "Lajeado", "Estrela", "Bom Retiro do Sul",
            "Fazenda Vilanova", "Taquari", "Venâncio Aires", "Mato Leitão",
            "Santa Clara do Sul", "Marques de Souza", "Travesseiro", "Capitão",
            "Bom Princípio", "Sério"]
sel = mun[mun.NM_MUN.isin(CORREDOR)].copy()
log(f"corredor: {len(sel)} municipios")

z = zipfile.ZipFile(os.path.join(KMZ, "EUROCLIMA.kmz"))
txt = z.read("doc.kml").decode("utf-8", "ignore")
eixos_ln = []
for pm in re.findall(r"<Placemark>(.*?)</Placemark>", txt, re.S):
    n = re.search(r"<name>(.*?)</name>", pm, re.S)
    if not n or not n.group(1).strip().startswith("EIXO"):
        continue
    m = re.search(r"<coordinates>(.*?)</coordinates>", pm, re.S)
    pts = [tuple(map(float, tk.split(",")[:2])) for tk in m.group(1).split()]
    eixos_ln.append(dict(nome=n.group(1).strip(), geometry=LineString(pts)))
eixos_ln = gpd.GeoDataFrame(eixos_ln, crs=4326).to_crs(UTM22)
log(f"eixos: {list(eixos_ln.nome)}")

# ===================================== 2. ESTAGIO 1 — acumulacao (bacia toda)
bac = gpd.read_file(os.path.join(SHP, "Bacia_Hidrografica_Taquari.shp")).to_crs(UTM22)
bx = bac.total_bounds
ds = gdal.Open(FDR); gt0 = ds.GetGeoTransform()
px = gt0[1]; cell = px * abs(gt0[5]); buf = 30 * px

def janela(bounds):
    a = max(0, int((bounds[0] - buf - gt0[0]) / gt0[1]))
    b = min(ds.RasterXSize, int((bounds[2] + buf - gt0[0]) / gt0[1]) + 1)
    c = max(0, int((bounds[3] + buf - gt0[3]) / gt0[5]))
    d = min(ds.RasterYSize, int((bounds[1] - buf - gt0[3]) / gt0[5]) + 1)
    return a, c, b - a, d - c            # c1, r1, nx, ny

# a janela do estagio 1 precisa CONTER a do corredor: os municipios de jusante
# (Taquari, Venancio Aires) extrapolam a bbox da bacia Taquari-Antas.
cxb = sel.total_bounds
uni = (min(bx[0], cxb[0]), min(bx[1], cxb[1]), max(bx[2], cxb[2]), max(bx[3], cxb[3]))
C1, R1, BX, BY = janela(uni)
log(f"ESTAGIO 1 — bacia + corredor: {BY} x {BX} = {BY*BX/1e6:.1f} M celulas")
fdrB = ds.GetRasterBand(1).ReadAsArray(C1, R1, BX, BY)

DR = {1:0, 2:1, 4:1, 8:1, 16:0, 32:-1, 64:-1, 128:-1}
DC = {1:1, 2:1, 4:0, 8:-1, 16:-1, 32:-1, 64:0, 128:1}
dra = np.zeros(256, np.int8); dca = np.zeros(256, np.int8); okv = np.zeros(256, bool)
for k in DR: dra[k], dca[k], okv[k] = DR[k], DC[k], True

def receptores(fdr_arr, ny, nx):
    rows = np.repeat(np.arange(ny, dtype=np.int32), nx)
    cols = np.tile(np.arange(nx, dtype=np.int32), ny)
    f = fdr_arr.ravel()
    rr = rows + dra[f]; cc = cols + dca[f]
    v = okv[f] & (rr >= 0) & (rr < ny) & (cc >= 0) & (cc < nx)
    return np.where(v, rr.astype(np.int64) * nx + cc, -1).astype(np.int32)

recB = receptores(fdrB, BY, BX)
NB = BY * BX
log("  acumulando...")
temB = recB >= 0
cntB = np.bincount(recB[temB].astype(np.int64), minlength=NB).astype(np.int32)
indeg = cntB.copy(); accB = np.ones(NB, np.int32)
fr = np.flatnonzero(indeg == 0).astype(np.int32)
while fr.size:
    d = recB[fr]; m = d >= 0
    if not m.any(): break
    fs, dx = fr[m], d[m].astype(np.int64)
    np.add.at(accB, dx, accB[fs]); np.add.at(indeg, dx, -1)
    al = np.unique(dx); fr = al[indeg[al] == 0].astype(np.int32)
areaB = (accB.astype(np.float32) * cell / 1e6).reshape(BY, BX)
log(f"  area maxima: {areaB.max():,.0f} km2")
del recB, cntB, indeg, accB, fdrB, temB

# ===================================== 3. ESTAGIO 2 — corredor
cx = sel.total_bounds
c1, r1, NX, NY = janela(cx)
N = NY * NX
gt = (gt0[0] + c1 * gt0[1], gt0[1], 0.0, gt0[3] + r1 * gt0[5], 0.0, gt0[5])
log(f"ESTAGIO 2 — corredor: {NY} x {NX} = {N/1e6:.2f} M celulas")

fdr = ds.GetRasterBand(1).ReadAsArray(c1, r1, NX, NY)
dsm = gdal.Open(MDE)
dem = dsm.GetRasterBand(1).ReadAsArray(c1, r1, NX, NY).astype(np.float32)
ndv = dsm.GetRasterBand(1).GetNoDataValue()
if ndv is not None: dem[dem == ndv] = np.nan
# recorta a area de drenagem calculada no estagio 1
oy, ox = r1 - R1, c1 - C1
area_km2 = areaB[oy:oy + NY, ox:ox + NX].ravel().copy()
del areaB
log(f"  area de drenagem no corredor: max {area_km2.max():,.0f} km2")

rec = receptores(fdr, NY, NX)
z1 = dem.ravel()
canal = area_km2 >= LIM_CANAL_KM2
log(f"  celulas de canal: {canal.sum():,}")

# ------------------------------------------------------------------ HAND
log("HAND (pointer chasing)...")
ref = np.where(canal, np.arange(N, dtype=np.int32), np.int32(-1))
pend = (~canal) & (rec >= 0)
rec_w = rec.copy()
it = 0
while pend.any() and it < 5000:
    it += 1
    idx = np.flatnonzero(pend).astype(np.int32)
    nxt = rec_w[idx]
    achou = (nxt >= 0) & (ref[nxt.clip(0)] >= 0)
    ref[idx[achou]] = ref[nxt[achou]]
    pend[idx[achou]] = False
    seg = idx[~achou]
    if seg.size == 0: break
    prox = rec_w[seg]
    bom = prox >= 0
    rec_w[seg[bom]] = rec_w[prox[bom]]
    pend[seg[~bom]] = False
del rec_w
hand = np.full(N, np.nan, np.float32)
tr = ref >= 0
hand[tr] = z1[tr] - z1[ref[tr]]
hand[hand < 0] = 0
log(f"  {it} iteracoes; sem referencia: {(~tr).sum():,}")
log(f"  HAND na planicie (celulas com ref): mediana {np.nanmedian(hand[tr]):.1f} m")

# ------------------------------------------------- trechos (agrupamento unico)
log("segmentando canal e agrupando celulas por trecho...")
canal_idx = np.flatnonzero(canal).astype(np.int32)
ordem = canal_idx[np.argsort(area_km2[canal_idx])]
n_trechos = max(8, len(ordem) // N_CELULAS_TRECHO)
grupos = np.array_split(ordem, n_trechos)
trecho_de = np.full(N, np.int32(-1), np.int32)
for i, g in enumerate(grupos):
    trecho_de[g] = i

# cada celula herda o trecho da sua celula de canal de referencia — UMA passada
trecho_cell = np.where(tr, trecho_de[ref.clip(0)], np.int32(-1))
valid = trecho_cell >= 0
cells_v = np.flatnonzero(valid).astype(np.int32)
tv = trecho_cell[valid]
o = np.argsort(tv, kind="stable")
cells_ord = cells_v[o]
cnts = np.bincount(tv, minlength=n_trechos)
offs = np.zeros(n_trechos + 1, np.int64); np.cumsum(cnts, out=offs[1:])
def celulas_do_trecho(i):
    return cells_ord[offs[i]:offs[i + 1]]
log(f"  {n_trechos} trechos ({N_CELULAS_TRECHO} celulas de canal cada)")

# ------------------------------------------------------- curvas-chave sinteticas
HS = np.arange(0.5, HAND_MAX + 0.5, 0.5)
log("curvas-chave por trecho...")
rating = {}
for i in range(n_trechos):
    idx = grupos[i]
    zz = z1[idx]; zz = zz[np.isfinite(zz)]
    if len(zz) < 3: continue
    S = max((np.nanmax(zz) - np.nanmin(zz)) / max(len(idx) * px, 1.0), 1e-4)
    cel = celulas_do_trecho(i)
    hh = hand[cel]
    hh = hh[np.isfinite(hh) & (hh <= HAND_MAX)]
    if hh.size < 20: continue
    L = len(idx) * px
    frac_canal = float((hh <= 2).sum()) / hh.size
    n_man = MANNING_CANAL * frac_canal + MANNING_PLANICIE * (1 - frac_canal)
    Q = np.zeros(len(HS))
    for k, h in enumerate(HS):
        prof = np.clip(h - hh, 0, None)
        if prof.max() <= 0: continue
        A = prof.sum() * cell / L
        larg = (prof > 0).sum() * cell / L
        P = max(larg, np.sqrt(max(A, 1e-6)))
        R = A / max(P, 1e-3)
        Q[k] = (1 / n_man) * A * R ** (2 / 3) * np.sqrt(S)
    if Q.max() <= 0: continue
    rating[i] = dict(S=S, Q=Q, area_km2=float(np.median(area_km2[idx])),
                     z_talvegue=float(np.nanmedian(zz)), n_manning=n_man,
                     x=float(np.mean([(g % NX) for g in idx])),
                     y=float(np.mean([(g // NX) for g in idx])))
log(f"  {len(rating)} trechos validos")

# =============================================================== 4. cenarios
Q_PICO_ESTRELA = 18000.0
AREA_ESTRELA   = 19440.0
EIXO_AREA_KM2  = 15457.0     # B1 (EIXO-A)
Q_EFLUENTE_B1  = 2600.0      # efluente de pico da barragem seca de 90 m

def q_de_area(a, cenario):
    q_nat = Q_PICO_ESTRELA * (a / AREA_ESTRELA) ** 0.85
    if cenario == "sem_barragem" or a <= EIXO_AREA_KM2:
        return q_nat
    a_livre = a - EIXO_AREA_KM2
    return Q_EFLUENTE_B1 + Q_PICO_ESTRELA * (a_livre / AREA_ESTRELA) ** 0.85

CENARIOS = ["sem_barragem", "com_barragem_B1_90m"]

log("rasterizando corredor...")
_m = gdal.GetDriverByName("MEM").Create("", NX, NY, 1, gdal.GDT_Byte)
_m.SetGeoTransform(gt)
_s = osr.SpatialReference(); _s.ImportFromEPSG(UTM22); _m.SetProjection(_s.ExportToWkt())
_t = os.path.join(D_GIS, "_corr.geojson")
if os.path.exists(_t): os.remove(_t)
sel[["NM_MUN", "geometry"]].to_file(_t, driver="GeoJSON")
_v = ogr.Open(_t); gdal.RasterizeLayer(_m, [1], _v.GetLayer(), burn_values=[1])
mask_corr = _m.GetRasterBand(1).ReadAsArray().ravel().astype(bool)
_v = None; os.remove(_t)
log(f"  corredor: {mask_corr.sum()*cell/1e6:,.0f} km2")

def salva_raster(arr, caminho):
    o = gdal.GetDriverByName("GTiff").Create(
        caminho, NX, NY, 1, gdal.GDT_Float32,
        options=["COMPRESS=DEFLATE", "TILED=YES"])
    o.SetGeoTransform(gt)
    s = osr.SpatialReference(); s.ImportFromEPSG(UTM22); o.SetProjection(s.ExportToWkt())
    b = o.GetRasterBand(1); b.WriteArray(arr.reshape(NY, NX)); b.SetNoDataValue(-9999)
    o = None

manchas = {}
perfil = []
for cen in CENARIOS:
    log(f"mapeando — {cen}")
    prof = np.full(N, -9999.0, np.float32)
    for i, rt in rating.items():
        q = q_de_area(rt["area_km2"], cen)
        Qc = rt["Q"]
        h = (HS[0] * q / max(Qc[0], 1e-6) if q <= Qc[0]
             else HS[-1] if q >= Qc[-1] else float(np.interp(q, Qc, HS)))
        cel = celulas_do_trecho(i)
        d = h - hand[cel]
        pos = np.isfinite(d) & (d > 0)
        cp = cel[pos]
        prof[cp] = np.maximum(prof[cp], d[pos])
        perfil.append(dict(cenario=cen, trecho=i, area_km2=round(rt["area_km2"], 1),
                           Q_m3s=round(q), h_m=round(h, 2),
                           z_talvegue_m=round(rt["z_talvegue"], 1),
                           z_linha_dagua_m=round(rt["z_talvegue"] + h, 1),
                           declividade=round(rt["S"], 5), n_manning=round(rt["n_manning"], 3)))
    m2 = (prof > 0).reshape(NY, NX)
    lab, _ = ndimage.label(m2, structure=np.ones((3, 3)))
    lc = np.unique(lab.ravel()[canal & (lab.ravel() > 0)])
    prof[~np.isin(lab, lc).ravel()] = -9999.0
    prof[~mask_corr] = -9999.0
    manchas[cen] = prof.copy()
    a = (prof > 0).sum() * cell / 1e6
    log(f"  area inundada: {a:,.1f} km2 | prof. media {np.nanmean(prof[prof>0]):.2f} m")
    salva_raster(prof, os.path.join(D_GIS, f"mancha_{cen}.tif"))

pd.DataFrame(perfil).to_csv(os.path.join(D_TAB, "perfil_linha_dagua.csv"),
                            index=False, sep=";", decimal=",")

dif = np.where((manchas["sem_barragem"] > 0) & (manchas["com_barragem_B1_90m"] <= 0), 1,
      np.where((manchas["sem_barragem"] > 0) & (manchas["com_barragem_B1_90m"] > 0), 2,
               -9999)).astype(np.float32)
salva_raster(dif, os.path.join(D_GIS, "mancha_diferenca.tif"))

# ------------------------------------------------------ estatisticas municipais
log("estatisticas por municipio...")
regs = []
for _, mr in sel.iterrows():
    mm = gdal.GetDriverByName("MEM").Create("", NX, NY, 1, gdal.GDT_Byte)
    mm.SetGeoTransform(gt)
    s = osr.SpatialReference(); s.ImportFromEPSG(UTM22); mm.SetProjection(s.ExportToWkt())
    tp = os.path.join(D_GIS, "_m1.geojson")
    if os.path.exists(tp): os.remove(tp)
    gpd.GeoDataFrame([{"geometry": mr.geometry}], crs=UTM22).to_file(tp, driver="GeoJSON")
    vv = ogr.Open(tp); gdal.RasterizeLayer(mm, [1], vv.GetLayer(), burn_values=[1])
    mk = mm.GetRasterBand(1).ReadAsArray().ravel().astype(bool)
    vv = None; os.remove(tp)
    a0 = ((manchas["sem_barragem"] > 0) & mk).sum() * cell / 1e6
    a1 = ((manchas["com_barragem_B1_90m"] > 0) & mk).sum() * cell / 1e6
    if a0 <= 0: continue
    p0 = float(np.nanmean(manchas["sem_barragem"][(manchas["sem_barragem"] > 0) & mk]))
    p1 = (float(np.nanmean(manchas["com_barragem_B1_90m"][(manchas["com_barragem_B1_90m"] > 0) & mk]))
          if a1 > 0 else 0.0)
    regs.append(dict(municipio=mr.NM_MUN, area_mun_km2=round(mr.AREA_KM2, 1),
                     inund_sem_km2=round(a0, 2), inund_com_km2=round(a1, 2),
                     reducao_km2=round(a0 - a1, 2),
                     reducao_pct=round(100 * (1 - a1 / a0), 1) if a0 > 0 else 0,
                     prof_media_sem_m=round(p0, 2), prof_media_com_m=round(p1, 2)))
est = pd.DataFrame(regs).sort_values("inund_sem_km2", ascending=False)
est.to_csv(os.path.join(D_TAB, "manchas_por_municipio.csv"), index=False, sep=";", decimal=",")

# ----------------------------------------------------------------- poligonos
log("vetorizando...")
pol = []
for cen in CENARIOS:
    mm = gdal.GetDriverByName("MEM").Create("", NX, NY, 1, gdal.GDT_Byte)
    mm.SetGeoTransform(gt)
    s = osr.SpatialReference(); s.ImportFromEPSG(UTM22); mm.SetProjection(s.ExportToWkt())
    mm.GetRasterBand(1).WriteArray((manchas[cen] > 0).reshape(NY, NX).astype(np.uint8))
    tp = os.path.join(D_GIS, "_mp.geojson")
    if os.path.exists(tp): os.remove(tp)
    dv = ogr.GetDriverByName("GeoJSON").CreateDataSource(tp)
    ly = dv.CreateLayer("p", s, ogr.wkbPolygon)
    ly.CreateField(ogr.FieldDefn("val", ogr.OFTInteger))
    gdal.Polygonize(mm.GetRasterBand(1), mm.GetRasterBand(1), ly, 0)
    dv = None
    g = gpd.read_file(tp); os.remove(tp)
    g = g[g.val == 1].dissolve(); g["cenario"] = cen
    g["area_km2"] = round(g.to_crs(UTM22).area.sum() / 1e6, 2)
    pol.append(g[["cenario", "area_km2", "geometry"]])
gpd.GeoDataFrame(pd.concat(pol, ignore_index=True), crs=UTM22).to_file(
    os.path.join(D_GIS, "manchas.gpkg"), layer="manchas", driver="GPKG")

print("\n" + "=" * 92)
print("MANCHAS DE INUNDACAO — EVENTO DE REFERENCIA")
print("=" * 92)
a0 = (manchas["sem_barragem"] > 0).sum() * cell / 1e6
a1 = (manchas["com_barragem_B1_90m"] > 0).sum() * cell / 1e6
print(f"  sem barragem ................. {a0:8,.1f} km2")
print(f"  com barragem B1 90 m seca .... {a1:8,.1f} km2")
print(f"  REDUCAO ...................... {a0-a1:8,.1f} km2  ({100*(1-a1/a0):.1f}%)")
print("\n" + "=" * 92)
print("POR MUNICIPIO")
print("=" * 92)
print(est.to_string(index=False))
log("FIM")
