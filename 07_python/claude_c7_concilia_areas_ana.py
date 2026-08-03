# -*- coding: utf-8 -*-
"""
EUROCLIMA / Estrela-RS — CONCILIACAO DAS AREAS ANA x D8 e revisao da
transposicao de vazoes.

MOTIVO
------
Em C3 a transposicao Mucum -> Estrela usou as areas do HidroInventario da ANA
(16.000 e 22.472 km2) e produziu expoente 0,395, muito abaixo do 0,85 usual.
Antes de concluir que ha' forte amortecimento na planicie, e' preciso verificar
se as areas oficiais e as delineadas pela grade D8 concordam. Uma divergencia
de area produz erro direto no expoente.

O QUE SE FAZ
------------
1. Delineia a bacia D8 nas coordenadas OFICIAIS de cada posto.
2. Compara com a area do HidroInventario e com a BHO/ANA.
3. Recalcula o expoente de transposicao com as areas que se confirmarem.
4. Reavalia o pico no ponto de analise (limite de montante do trecho).

Saidas: claude_c7_areas_postos.csv, claude_c7_transposicao_revisada.csv
"""
import os, time, warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import geopandas as gpd
from osgeo import gdal
from shapely.geometry import Point

gdal.UseExceptions()

GIS = os.environ["GIS"]; SHP = os.environ["SHP"]
DEST = os.path.join(os.environ["EURO"], "05_MODELAGEM")
D_ANA = os.path.join(DEST, "01_dados", "ana_hidroweb")
D_OUT = os.path.join(DEST, "06_resultados", "CLAUDE")
FDR = os.path.join(GIS, "raster", "Fdr.tif")
UTM22 = 31982
RD = dict(sep=";", decimal=",")
os.makedirs(D_OUT, exist_ok=True)

t0 = time.time()
def log(*a): print(f"[{time.time()-t0:6.1f}s]", *a, flush=True)

# Fichas oficiais do HidroInventario da ANA
POSTOS = [
    dict(cod=86510000, nome="MUCUM",     area_ana=16000.0, lat=-29.1672, lon=-51.8686),
    dict(cod=86879300, nome="ESTRELA",   area_ana=22472.0, lat=-29.4733, lon=-51.9622),
    dict(cod=86720000, nome="ENCANTADO", area_ana=19100.0, lat=-29.2344, lon=-51.8550),
]
AREA_PONTO_ANALISE = 19440.0   # limite de montante do trecho modelado

# =============================================================================
# grade e acumulacao
# =============================================================================
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

# =============================================================================
# delineacao nos postos
# =============================================================================
bho = gpd.read_file(os.path.join(SHP, "Drenagem_Bacia_Taquari.shp")).to_crs(UTM22)
bho = bho[bho.geometry.notna()].copy()

print("=" * 110)
print("1. AREAS NOS POSTOS — ANA (HidroInventario) x D8 x BHO")
print("=" * 110)
regs = []
for p in POSTOS:
    pt = gpd.GeoSeries([Point(p["lon"], p["lat"])], crs=4326).to_crs(UTM22).iloc[0]
    r0, c0 = rc(pt.x, pt.y)
    # celula de maior area numa janela de +/-15 celulas (+/- 430 m)
    best = None
    for dr_ in range(-15, 16):
        for dc_ in range(-15, 16):
            r_, c_ = r0 + dr_, c0 + dc_
            if not (0 <= r_ < NY and 0 <= c_ < NX): continue
            i = r_ * NX + c_
            if best is None or area[i] > best[0]:
                best = (float(area[i]), r_, c_, i,
                        float(np.hypot(dr_ * px, dc_ * px)))
    a_d8, r_, c_, i, desl = best
    # BHO mais proxima
    cand = bho[bho.geometry.distance(pt) < 2000].copy()
    a_bho = float(cand.nuareamont.max()) if len(cand) else np.nan
    d_bho = float(cand.geometry.distance(pt).min()) if len(cand) else np.nan
    regs.append(dict(
        codigo=p["cod"], nome=p["nome"],
        area_ANA_km2=p["area_ana"],
        area_D8_km2=round(a_d8, 1),
        area_BHO_km2=round(a_bho, 1) if np.isfinite(a_bho) else np.nan,
        dif_D8_vs_ANA_pct=round(100 * (a_d8 / p["area_ana"] - 1), 2),
        dif_BHO_vs_ANA_pct=round(100 * (a_bho / p["area_ana"] - 1), 2)
        if np.isfinite(a_bho) else np.nan,
        deslocamento_snap_m=round(desl, 0),
        dist_BHO_m=round(d_bho, 0) if np.isfinite(d_bho) else np.nan))
ar = pd.DataFrame(regs)
ar.to_csv(os.path.join(D_OUT, "claude_c7_areas_postos.csv"),
          index=False, sep=";", decimal=",")
pd.set_option("display.width", 200)
print(ar.to_string(index=False))

# =============================================================================
# transposicao revisada
# =============================================================================
print("\n" + "=" * 110)
print("2. TRANSPOSICAO REVISADA")
print("=" * 110)
mu = pd.read_csv(os.path.join(D_ANA, "86510000_vazao.csv"), **RD, parse_dates=["data"])
es = pd.read_csv(os.path.join(D_ANA, "86879300_vazao.csv"), **RD, parse_dates=["data"])
q_mu = float(mu[mu.data.dt.year == 2023].vazao.max())
q_es = float(es[es.data.dt.year == 2023].vazao.max())

cenarios = []
for rot, a_mu, a_es in [
        ("areas ANA (HidroInventario)",
         ar.loc[ar.nome == "MUCUM", "area_ANA_km2"].iloc[0],
         ar.loc[ar.nome == "ESTRELA", "area_ANA_km2"].iloc[0]),
        ("areas D8 (delineadas)",
         ar.loc[ar.nome == "MUCUM", "area_D8_km2"].iloc[0],
         ar.loc[ar.nome == "ESTRELA", "area_D8_km2"].iloc[0]),
        ("areas BHO (ottocodificada)",
         ar.loc[ar.nome == "MUCUM", "area_BHO_km2"].iloc[0],
         ar.loc[ar.nome == "ESTRELA", "area_BHO_km2"].iloc[0])]:
    if not (np.isfinite(a_mu) and np.isfinite(a_es)): continue
    rz_area = a_es / a_mu
    rz_q = q_es / q_mu
    exp_ = np.log(rz_q) / np.log(rz_area)
    q_an = q_es * (AREA_PONTO_ANALISE / a_es) ** exp_
    q_an85 = q_es * (AREA_PONTO_ANALISE / a_es) ** 0.85
    cenarios.append(dict(
        fonte_areas=rot, area_mucum_km2=round(a_mu, 1), area_estrela_km2=round(a_es, 1),
        razao_area=round(rz_area, 3), razao_vazao=round(rz_q, 3),
        expoente=round(exp_, 3),
        q_ponto_analise_exp_obs=round(q_an),
        q_ponto_analise_exp_085=round(q_an85)))
cn = pd.DataFrame(cenarios)
cn.to_csv(os.path.join(D_OUT, "claude_c7_transposicao_revisada.csv"),
          index=False, sep=";", decimal=",")
print(f"  evento de 2023: Mucum {q_mu:,.0f} m3/s | Estrela {q_es:,.0f} m3/s "
      f"(razao {q_es/q_mu:.3f})\n")
print(cn.to_string(index=False))

# =============================================================================
# LEITURA
# =============================================================================
print("\n" + "-" * 110)
print("LEITURA")
print("-" * 110)
for _, r in ar.iterrows():
    tag = "OK" if abs(r.dif_D8_vs_ANA_pct) <= 5 else "DIVERGE"
    print(f"  {r.nome:<10} ANA {r.area_ANA_km2:>9,.0f} | D8 {r.area_D8_km2:>9,.0f} "
          f"({r.dif_D8_vs_ANA_pct:+6.2f}%) | BHO {r.area_BHO_km2:>9,.0f} "
          f"({r.dif_BHO_vs_ANA_pct:+6.2f}%)  [{tag}]")

exps = cn.expoente.values
print(f"\n  expoente de transposicao pelas tres fontes de area: "
      f"{exps.min():.3f} a {exps.max():.3f}")
if exps.max() < 0.6:
    print("  Em TODAS as hipoteses de area o expoente fica muito abaixo de 0,85.")
    print("  A divergencia de area NAO explica o resultado — a razao de vazao")
    print("  observada e' realmente baixa para a razao de area.")
    print("\n  Restam as duas hipoteses fisicas:")
    print("    (a) amortecimento na planicie entre Mucum e Estrela;")
    print("    (b) curva-chave de Estrela extrapolada (3,1 anos de dados).")
    print("  Ambas exigem as medicoes de vazao previstas no Eixo 1 do TR.")
else:
    print("  A escolha da fonte de area altera materialmente o expoente.")
log("FIM")
