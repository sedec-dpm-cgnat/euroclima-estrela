# -*- coding: utf-8 -*-
"""
EUROCLIMA / Estrela-RS — geometria das barragens a partir do MDE.

Para cada eixo e cada altura, extrai do MDE:
  - o perfil transversal do vale, perpendicular a direcao do escoamento;
  - o comprimento de crista necessario para fechar o vale;
  - o volume de aterro (secao trapezoidal tipica de barragem de terra/enrocamento);
  - a curva cota-area-volume do reservatorio.

Saida: geometria_barragens.csv + perfis_transversais.csv
"""
import os, re, time, glob, zipfile, warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import geopandas as gpd
from osgeo import gdal
from scipy import ndimage
from shapely.geometry import Point, LineString

gdal.UseExceptions()

GIS = os.environ["GIS"]; SHP = os.environ["SHP"]
KMZ = os.environ.get("KMZ", os.path.join(os.path.dirname(GIS), "kmz"))
DEST = os.path.join(os.environ["EURO"], "05_MODELAGEM")
FDR = os.path.join(GIS, "raster", "Fdr.tif")
MDE = os.path.join(GIS, "raster", "mdr.tif")
UTM22 = 31982

t0 = time.time()
def log(*a): print(f"[{time.time()-t0:7.1f}s]", *a, flush=True)

# ---------------------------------------------------- parametros de projeto
CRISTA_M     = 10.0    # largura da crista (m)
TALUDE_MONT  = 2.5     # 1V : 2,5H
TALUDE_JUS   = 2.0     # 1V : 2,0H
BORDA_LIVRE  = 3.0     # folga acima do NA maximo (m)

# custos unitarios de referencia (R$, ordem de grandeza — REVISAR com SINAPI)
C_ATERRO     = 90.0        # R$/m3 de aterro compactado
C_VERTEDOURO = 8_000.0     # R$/m3 de concreto  (estimado por m de crista)
C_DESAPROP   = 45_000.0    # R$/ha de area inundada (rural, Vale do Taquari)

# ------------------------------------------------------------------ rasters
bac = gpd.read_file(os.path.join(SHP, "Bacia_Hidrografica_Taquari.shp")).to_crs(UTM22)
minx, miny, maxx, maxy = bac.total_bounds
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
log(f"grade {NY}x{NX}")

def rc(x, y): return int((y - gt[3]) / gt[5]), int((x - gt[0]) / gt[1])
def xy(r, c): return gt[0] + (c + .5) * gt[1], gt[3] + (r + .5) * gt[5]

def amostra_dem(x, y):
    r, c = rc(x, y)
    if 0 <= r < NY and 0 <= c < NX:
        return float(dem[r, c])
    return np.nan

# ------------------------------------------------- grafo D8 e delineacao
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
log("acumulacao...")
indeg = cnt.copy(); acc = np.ones(N, np.int32)
fr = np.flatnonzero(indeg == 0).astype(np.int32)
while fr.size:
    d = rec[fr]; m = d >= 0
    if not m.any(): break
    fs, dx = fr[m], d[m].astype(np.int64)
    np.add.at(acc, dx, acc[fs]); np.add.at(indeg, dx, -1)
    al = np.unique(dx); fr = al[indeg[al] == 0].astype(np.int32)

def bfs(no):
    sel = np.zeros(N, bool); sel[no] = True
    q = np.array([no], np.int32)
    while q.size:
        c_ = cnt[q]; tot = int(c_.sum())
        if tot == 0: break
        base = np.repeat(off[q], c_)
        de = np.arange(tot) - np.repeat(np.cumsum(c_) - c_, c_)
        k = filhos[(base + de).astype(np.int64)]
        k = k[~sel[k]]
        if k.size == 0: break
        sel[k] = True; q = k
    return sel

# ------------------------------------------------------------- eixos (KMZ)
def le_kmz(pasta):
    pts = []
    for fp in sorted(glob.glob(os.path.join(pasta, "*.km[lz]"))):
        if fp.lower().endswith(".kmz"):
            with zipfile.ZipFile(fp) as z:
                kml = next(n for n in z.namelist() if n.lower().endswith(".kml"))
                txt = z.read(kml).decode("utf-8", "ignore")
        else:
            txt = open(fp, encoding="utf-8", errors="ignore").read()
        base = re.sub(r"Ponto[-_]Barragem", "B", os.path.splitext(os.path.basename(fp))[0])
        for m in re.finditer(r"<coordinates>(.*?)</coordinates>", txt, re.S):
            c = m.group(1).split()
            if not c: continue
            lon, lat = float(c[0].split(",")[0]), float(c[0].split(",")[1])
            pts.append(dict(id=base, lon=lon, lat=lat))
    return pts

eixos = le_kmz(KMZ)
for e in eixos:
    p22 = gpd.GeoSeries([Point(e["lon"], e["lat"])], crs=4326).to_crs(UTM22).iloc[0]
    r0, c0 = rc(p22.x, p22.y)
    best = None
    for ddr in range(-5, 6):
        for ddc in range(-5, 6):
            r, c = r0 + ddr, c0 + ddc
            if not (0 <= r < NY and 0 <= c < NX): continue
            i = r * NX + c
            a = acc[i] * cell_area / 1e6
            if best is None or a > best[0]: best = (a, r, c, i)
    a, r, c, i = best
    e.update(r=r, c=c, no=i, area_km2=round(a, 1),
             cota_eixo=round(float(dem[r, c]), 1), x=float(xy(r, c)[0]), y=float(xy(r, c)[1]))
    e["_mask"] = bfs(i).reshape(NY, NX)
    log(f"  {e['id']}: {e['area_km2']:,.1f} km2  cota {e['cota_eixo']:.1f} m")

# ============================================================================
# PERFIL TRANSVERSAL DO VALE E GEOMETRIA DA BARRAGEM
# ============================================================================
def direcao_fluxo(r, c):
    """Vetor unitario da direcao de escoamento na celula."""
    k = int(fdr[r, c])
    if k not in DR: return (1.0, 0.0)
    v = np.array([DC[k], -DR[k]], float)   # x para leste, y para norte
    return tuple(v / np.linalg.norm(v))

def perfil_transversal(e, alcance_m=6000, passo_m=None):
    """Amostra o MDE ao longo da perpendicular a direcao de fluxo."""
    passo = passo_m or px / 2
    ux, uy = direcao_fluxo(e["r"], e["c"])
    nx_, ny_ = -uy, ux                       # perpendicular
    s = np.arange(-alcance_m, alcance_m + passo, passo)
    xs = e["x"] + nx_ * s
    ys = e["y"] + ny_ * s
    zs = np.array([amostra_dem(a, b) for a, b in zip(xs, ys)])
    return s, zs, (nx_, ny_)

def geometria(e, H):
    """Comprimento de crista e volume de aterro para altura H."""
    s, z, _ = e["_perfil"]
    z0 = e["cota_eixo"]
    cota_crista = z0 + H + BORDA_LIVRE
    i0 = len(s) // 2                          # posicao do eixo (talvegue)
    # avanca para cada lado ate o terreno atingir a cota de crista
    def limite(direcao):
        i = i0
        while 0 < i < len(s) - 1:
            i += direcao
            if not np.isfinite(z[i]):
                continue
            if z[i] >= cota_crista:
                return i
        return i
    iE, iD = limite(-1), limite(+1)
    ss, zz = s[iE:iD + 1], z[iE:iD + 1]
    if len(ss) < 2:
        return dict(L_crista_m=np.nan, V_aterro_hm3=np.nan, h_max_m=np.nan)
    L = float(ss[-1] - ss[0])
    ds = float(np.mean(np.diff(ss)))
    hloc = np.clip(cota_crista - zz, 0, None)
    hloc[~np.isfinite(hloc)] = 0
    # secao trapezoidal: A = b*h + (m1+m2)/2 * h^2
    m = (TALUDE_MONT + TALUDE_JUS) / 2.0
    A = CRISTA_M * hloc + m * hloc**2
    V = float(np.sum(A) * ds)
    return dict(L_crista_m=round(L, 1), V_aterro_hm3=round(V / 1e6, 3),
                h_max_m=round(float(np.nanmax(hloc)), 1),
                cota_crista_m=round(cota_crista, 1))

def cav_ponto(e, H):
    m = e["_mask"]; rs, cs = np.where(m)
    a1, a2, b1, b2 = rs.min(), rs.max() + 1, cs.min(), cs.max() + 1
    sm, sz = m[a1:a2, b1:b2], dem[a1:a2, b1:b2]
    lr, lc = e["r"] - a1, e["c"] - b1
    niv = e["cota_eixo"] + H
    lab, _ = ndimage.label(sm & np.isfinite(sz) & (sz <= niv), structure=np.ones((3, 3)))
    if lab[lr, lc] == 0:
        return 0.0, 0.0
    res = lab == lab[lr, lc]
    return (res.sum() * cell_area / 1e6,
            float(np.nansum(niv - sz[res])) * cell_area / 1e6)

log("extraindo perfis transversais...")
for e in eixos:
    e["_perfil"] = perfil_transversal(e)
    s, z, _ = e["_perfil"]
    log(f"  {e['id']}: perfil {len(s)} pontos, cota {np.nanmin(z):.0f}-{np.nanmax(z):.0f} m")

ALTURAS = list(range(20, 125, 5))
log("calculando geometria e CAV por altura...")
regs = []
for e in eixos:
    for H in ALTURAS:
        g = geometria(e, H)
        area, vol = cav_ponto(e, H)
        if not np.isfinite(g["L_crista_m"]):
            continue
        c_aterro = g["V_aterro_hm3"] * 1e6 * C_ATERRO
        c_vert   = g["L_crista_m"] * C_VERTEDOURO
        c_desap  = area * 100 * C_DESAPROP          # km2 -> ha
        regs.append(dict(
            barragem=e["id"], altura_m=H,
            cota_eixo_m=e["cota_eixo"], cota_NA_m=round(e["cota_eixo"] + H, 1),
            cota_crista_m=g["cota_crista_m"],
            area_controlada_km2=e["area_km2"],
            L_crista_m=g["L_crista_m"], V_aterro_hm3=g["V_aterro_hm3"],
            area_alagada_km2=round(area, 2), volume_hm3=round(vol, 1),
            custo_aterro_MRS=round(c_aterro / 1e6, 1),
            custo_vertedouro_MRS=round(c_vert / 1e6, 1),
            custo_desapropr_MRS=round(c_desap / 1e6, 1),
            custo_total_MRS=round((c_aterro + c_vert + c_desap) * 1.35 / 1e6, 1),  # +35% BDI/obras compl.
        ))
    log(f"  {e['id']} ok")

df = pd.DataFrame(regs)
os.makedirs(os.path.join(DEST, "01_dados", "cav"), exist_ok=True)
df.to_csv(os.path.join(DEST, "01_dados", "cav", "geometria_barragens.csv"),
          index=False, sep=";", decimal=",")

# perfis para grafico
perfis = []
for e in eixos:
    s, z, _ = e["_perfil"]
    for a, b in zip(s, z):
        if np.isfinite(b):
            perfis.append(dict(barragem=e["id"], estaca_m=round(float(a), 1),
                               cota_m=round(float(b), 2), cota_eixo_m=e["cota_eixo"]))
pd.DataFrame(perfis).to_csv(
    os.path.join(DEST, "01_dados", "cav", "perfis_transversais.csv"),
    index=False, sep=";", decimal=",")

pd.set_option("display.width", 240)
print("\n" + "=" * 120)
print("GEOMETRIA DAS BARRAGENS POR ALTURA")
print("=" * 120)
for b in df.barragem.unique():
    print(f"\n--- {b} ---")
    print(df[df.barragem == b][["altura_m", "L_crista_m", "V_aterro_hm3",
                                "area_alagada_km2", "volume_hm3",
                                "custo_total_MRS"]].to_string(index=False))
log("FIM")
