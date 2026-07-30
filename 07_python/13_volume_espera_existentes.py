# -*- coding: utf-8 -*-
"""
EUROCLIMA / Estrela-RS — VOLUME DE ESPERA nos reservatorios JA EXISTENTES.

A bacia do Taquari-Antas tem 49 aproveitamentos em operacao, entre eles a
cascata do rio das Antas (Monte Claro 130 MW, Castro Alves 130 MW,
14 de Julho 100 MW). Todos operam a fio d'agua, sem qualquer volume alocado
para controle de cheias — razao pela qual nao atenuaram os eventos de
2023/2024.

Este script responde: QUANTO volume de espera seria possivel alocar nesses
reservatorios apenas por REGRA OPERATIVA (deplecionamento preventivo), sem
nenhuma obra nova?

Metodo: para cada aproveitamento, reconstroi-se a curva cota-area-volume a
partir do MDE, por flood-fill a montante do eixo. O volume de espera e' o
volume entre o NA normal (aproximado pela cota do terreno no local, que no
MDE ja reflete o reservatorio cheio) e um rebaixamento de dh metros.

LIMITACAO IMPORTANTE: o MDE de 28,6 m ja "enxerga" a lamina d'agua dos
reservatorios existentes. A curva obtida e' portanto a do volume ACIMA do NA
atual para elevacoes positivas, e uma ESTIMATIVA do volume abaixo dele para
rebaixamentos — sujeita a erro, pois a batimetria do reservatorio nao esta'
no MDE. Os volumes de deplecionamento aqui sao LIMITES SUPERIORES.

Saida: volume_espera_existentes.csv
"""
import os, time, warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import geopandas as gpd
from osgeo import gdal
from scipy import ndimage

gdal.UseExceptions()

GIS = os.environ["GIS"]; SHP = os.environ["SHP"]
DEST = os.path.join(os.environ["EURO"], "05_MODELAGEM")
D_GIS = os.path.join(DEST, "01_dados", "gis_derivado")
D_TAB = os.path.join(DEST, "06_resultados", "tabelas")
FDR = os.path.join(GIS, "raster", "Fdr.tif")
MDE = os.path.join(GIS, "raster", "mdr.tif")
UTM22 = 31982

t0 = time.time()
def log(*a): print(f"[{time.time()-t0:7.1f}s]", *a, flush=True)

POT_MIN_MW = 15.0        # so aproveitamentos com alguma relevancia de porte
ALTEAMENTO = [1, 2, 3, 5, 8, 10, 15, 20]   # alteamentos testados (m)

# ------------------------------------------------------------------- entradas
ap = gpd.read_file(os.path.join(D_GIS, "aproveitamentos.gpkg"), layer="aneel").to_crs(UTM22)
ap["potencia_MW"] = pd.to_numeric(
    ap.potencia_kW.astype(str).str.replace(",", "."), errors="coerce") / 1000.0
ap = ap[(ap.situacao == "operacao") & (ap.potencia_MW >= POT_MIN_MW)].copy()
ap = ap.sort_values("area_drenagem_km2", ascending=False)
log(f"{len(ap)} aproveitamentos em operacao com >= {POT_MIN_MW:.0f} MW")

# --------------------------------------------------------------------- grade
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
log(f"grade {NY} x {NX}")

def rc(x, y): return int((y - gt[3]) / gt[5]), int((x - gt[0]) / gt[1])

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
area_km2 = acc.astype(np.float32) * cell / 1e6

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

# ------------------------------------------------- CAV de cada reservatorio
bho = gpd.read_file(os.path.join(SHP, "Drenagem_Bacia_Taquari.shp")).to_crs(UTM22)
bho = bho[bho.geometry.notna()].copy(); sidx = bho.sindex

log("reconstruindo curvas cota-volume dos reservatorios existentes...")
regs = []
for _, a in ap.iterrows():
    cand = bho.iloc[list(sidx.query(a.geometry.buffer(2500)))].copy()
    if len(cand) == 0: continue
    ln = cand.sort_values("nuareamont", ascending=False).iloc[0]
    alvo = float(ln.get("nuareamont", np.nan))
    # ANCORAGEM NO ESPELHO D'AGUA, nao no pe da barragem.
    # O ponto da ANEEL marca a casa de forca. Se o snap for feito apenas por
    # area de drenagem, ele cai a JUSANTE do barramento, no canal de fuga, e
    # o flood-fill enche a calha de jusante em vez do reservatorio.
    # Criterio: entre as celulas de canal proximas com area compativel,
    # escolhe-se a de MAIOR cota — que e' a superficie do reservatorio.
    r0, c0 = rc(a.geometry.x, a.geometry.y)
    best = None
    for dr in range(-15, 16):
        for dc in range(-15, 16):
            r, c = r0 + dr, c0 + dc
            if not (0 <= r < NY and 0 <= c < NX): continue
            i = r * NX + c
            if not np.isfinite(alvo): continue
            if abs(area_km2[i] - alvo) / alvo > 0.20: continue   # mesmo trecho
            z = float(dem[r, c])
            if not np.isfinite(z): continue
            if best is None or z > best[0]: best = (z, r, c, i)
    if best is None:
        log(f"  {a['nome'][:26]}: sem celula de canal compativel — pulando")
        continue
    z0, r, c, i = best
    mask = bfs(i).reshape(NY, NX)
    rs, cs = np.where(mask)
    if len(rs) < 10: continue
    a1, a2, b1, b2 = rs.min(), rs.max() + 1, cs.min(), cs.max() + 1
    sm, sz = mask[a1:a2, b1:b2], dem[a1:a2, b1:b2]
    lr, lc = r - a1, c - b1

    reg = dict(nome=a["nome"], potencia_MW=round(a.potencia_MW, 1),
               area_drenagem_km2=round(float(area_km2[i]), 1),
               cota_NA_atual_m=round(z0, 1))
    # volume acima do NA atual (elevacao) e area alagada correspondente
    for h in ALTEAMENTO:
        niv = z0 + h
        lab, _ = ndimage.label(sm & np.isfinite(sz) & (sz <= niv), structure=np.ones((3, 3)))
        if lab[lr, lc] == 0:
            reg[f"V_acima_{h}m_hm3"] = 0.0
            continue
        res = lab == lab[lr, lc]
        reg[f"V_acima_{h}m_hm3"] = round(
            float(np.nansum(niv - sz[res])) * cell / 1e6, 1)
        if h == ALTEAMENTO[0]:
            reg["area_espelho_km2"] = round(res.sum() * cell / 1e6, 2)
    regs.append(reg)
    log(f"  {a['nome'][:26]:<26} {a.potencia_MW:>6.1f} MW  "
        f"A={area_km2[i]:>9,.0f} km2  NA={z0:>6.1f} m  "
        f"espelho={reg.get('area_espelho_km2',0):>6.2f} km2")

df = pd.DataFrame(regs)
df.to_csv(os.path.join(D_TAB, "volume_espera_existentes.csv"),
          index=False, sep=";", decimal=",")

pd.set_option("display.width", 220)
print("\n" + "=" * 118)
print("RESERVATORIOS EXISTENTES — VOLUME DISPONIVEL ACIMA DO NA ATUAL")
print("(quanto o reservatorio comporta se o NA subir h metros — proxy do volume")
print(" de espera mobilizavel por deplecionamento preventivo equivalente)")
print("=" * 118)
cols = ["nome", "potencia_MW", "area_drenagem_km2", "cota_NA_atual_m", "area_espelho_km2"] + \
       [f"V_acima_{h}m_hm3" for h in ALTEAMENTO]
print(df[[c for c in cols if c in df.columns]].to_string(index=False))

for h in (2, 5, 10):
    col = f"V_acima_{h}m_hm3"
    if col in df.columns:
        print(f"\n  Soma da cascata com {h:>2d} m de faixa: {df[col].sum():>8,.0f} hm3")

print("\n  Referencia: o volume necessario para evitar os danos da cheia de 2024")
print("  em Estrela e' da ordem de 3.230 hm3.")
log("FIM")
