# -*- coding: utf-8 -*-
"""
EUROCLIMA / Estrela-RS — DIVISAO DE QUEDAS do rio das Antas / Taquari.

Produz o diagrama longitudinal no padrao de inventario hidroeletrico:
  - perfil do talvegue, da cabeceira do canal principal ate Bom Retiro do Sul;
  - aproveitamentos EXISTENTES, com o NA atual de cada reservatorio;
  - eixos PROPOSTOS (E01..E12), com NA maximo normal, NA maximo maximorum e
    crista, limitados a ALTURA ADMISSIVEL (sem afogar usina de montante);
  - identificacao dos trechos de queda ja aproveitados e dos trechos livres.

O eixo horizontal e' a distancia ao longo do talvegue; o vertical, a cota.
Cada barramento aparece como um degrau, e o remanso como o patamar horizontal
a montante — que e' exatamente a leitura de "divisao de quedas".

Saidas (06_resultados/CLAUDE/):
  claude_divisao_quedas.png
  claude_perfil_principal.csv
  claude_quedas_por_trecho.csv
"""
import os, time, warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import geopandas as gpd
from osgeo import gdal
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from shapely.geometry import Point

gdal.UseExceptions()

GIS = os.environ["GIS"]; SHP = os.environ["SHP"]
DEST = os.path.join(os.environ["EURO"], "05_MODELAGEM")
D_CAV = os.path.join(DEST, "01_dados", "cav")
D_TAB = os.path.join(DEST, "06_resultados", "tabelas")
D_OUT = os.path.join(DEST, "06_resultados", "CLAUDE")
FDR = os.path.join(GIS, "raster", "Fdr.tif")
MDE = os.path.join(GIS, "raster", "mdr.tif")
UTM22 = 31982
os.makedirs(D_OUT, exist_ok=True)

t0 = time.time()
def log(*a): print(f"[{time.time()-t0:6.1f}s]", *a, flush=True)

# =============================================================================
# 1. grade e rede de drenagem
# =============================================================================
mun = gpd.read_file(os.path.join(SHP, "Municipios_RS.shp")).to_crs(UTM22)
bac = gpd.read_file(os.path.join(SHP, "Bacia_Hidrografica_Taquari.shp")).to_crs(UTM22)
brs = mun[mun.NM_MUN == "Bom Retiro do Sul"]
bx = bac.total_bounds; cx = brs.total_bounds
uni = (min(bx[0], cx[0]), min(bx[1], cx[1]), max(bx[2], cx[2]), max(bx[3], cx[3]))

ds = gdal.Open(FDR); gt0 = ds.GetGeoTransform()
px = gt0[1]; cell = px * abs(gt0[5]); buf = 30 * px
c1 = max(0, int((uni[0] - buf - gt0[0]) / gt0[1]))
c2 = min(ds.RasterXSize, int((uni[2] + buf - gt0[0]) / gt0[1]) + 1)
r1 = max(0, int((uni[3] + buf - gt0[3]) / gt0[5]))
r2 = min(ds.RasterYSize, int((uni[1] - buf - gt0[3]) / gt0[5]) + 1)
NX, NY = c2 - c1, r2 - r1; N = NY * NX
gt = (gt0[0] + c1 * gt0[1], gt0[1], 0.0, gt0[3] + r1 * gt0[5], 0.0, gt0[5])
fdr = ds.GetRasterBand(1).ReadAsArray(c1, r1, NX, NY)
dsm = gdal.Open(MDE)
dem = dsm.GetRasterBand(1).ReadAsArray(c1, r1, NX, NY).astype(np.float32)
ndv = dsm.GetRasterBand(1).GetNoDataValue()
if ndv is not None: dem[dem == ndv] = np.nan
log(f"grade {NY} x {NX}")

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
area = acc.astype(np.float32) * cell / 1e6
log(f"  area maxima {area.max():,.0f} km2")

# =============================================================================
# 2. traca o canal principal ate Bom Retiro do Sul
# =============================================================================
brs_geom = brs.geometry.iloc[0]
# exutorio: celula de maior area dentro de Bom Retiro do Sul
minx, miny, maxx, maxy = brs.total_bounds
ra, ca = rc(minx, maxy); rb, cb = rc(maxx, miny)
ra, rb = max(0, min(ra, rb)), min(NY, max(ra, rb) + 1)
ca, cb = max(0, min(ca, cb)), min(NX, max(ca, cb) + 1)
sub = area.reshape(NY, NX)[ra:rb, ca:cb]
melhor = None
for rr_ in range(sub.shape[0]):
    for cc_ in range(sub.shape[1]):
        if not brs_geom.contains(Point(*xy(ra + rr_, ca + cc_))): continue
        if melhor is None or sub[rr_, cc_] > melhor[0]:
            melhor = (float(sub[rr_, cc_]), ra + rr_, ca + cc_)
_, r_ex, c_ex = melhor
no_ex = r_ex * NX + c_ex
log(f"exutorio em Bom Retiro do Sul: {area[no_ex]:,.0f} km2")

# sobe pelo canal principal (sempre o filho de maior area)
cam = [no_ex]; i = no_ex
for _ in range(20000):
    a_, b_ = off[i], off[i + 1]
    if b_ <= a_: break
    ks = filhos[a_:b_]
    j = int(ks[np.argmax(area[ks])])
    if area[j] < 300: break                # para nas cabeceiras
    cam.append(j); i = j
cam = cam[::-1]                            # de montante para jusante
log(f"canal principal: {len(cam)} estacas")

dist, cota, ar = [], [], []
d = 0.0
for k, no in enumerate(cam):
    r_, c_ = divmod(no, NX)
    if k > 0:
        rp, cp = divmod(cam[k - 1], NX)
        d += px * (1.4142 if (rp != r_ and cp != c_) else 1.0)
    dist.append(d / 1000.0); cota.append(float(dem[r_, c_])); ar.append(float(area[no]))
pf = pd.DataFrame(dict(dist_km=dist, cota_bruta_m=cota, area_km2=ar, no=cam))
# talvegue suavizado e monotonico
pf["cota_m"] = np.minimum.accumulate(
    pf.cota_bruta_m.rolling(21, center=True, min_periods=1).min()
      .rolling(31, center=True, min_periods=1).mean().values)
log(f"perfil: {pf.dist_km.max():.1f} km, cota {pf.cota_m.iloc[0]:.0f} -> {pf.cota_m.iloc[-1]:.0f} m")
_coords = np.array([xy(*divmod(int(n), NX)) for n in pf.no.values])
pf["x_utm"] = _coords[:, 0]; pf["y_utm"] = _coords[:, 1]
pf.drop(columns="no").to_csv(os.path.join(D_OUT, "claude_perfil_principal.csv"),
                             index=False, sep=";", decimal=",")

# coordenadas de cada estaca do perfil, para localizacao GEOMETRICA
_xy = _coords

def estaca_por_ponto(x, y):
    """Posicao no perfil geometricamente mais proxima do ponto (x, y).

    A localizacao por AREA DE DRENAGEM nao serve: usinas em tributarios com
    area semelhante a de uma secao do canal principal seriam projetadas no
    lugar errado, com cotas incoerentes. Usa-se a distancia geometrica e
    descarta-se o que estiver fora do corredor do canal principal.
    """
    d2 = (_xy[:, 0] - x) ** 2 + (_xy[:, 1] - y) ** 2
    i = int(np.argmin(d2))
    return (float(pf.dist_km.values[i]), float(pf.cota_m.values[i]),
            float(np.sqrt(d2[i])))

# =============================================================================
# 3. aproveitamentos existentes e eixos propostos
# =============================================================================
apr = pd.read_csv(os.path.join(D_TAB, "aproveitamentos_existentes.csv"), sep=";", decimal=",")
apr["potencia_MW"] = pd.to_numeric(
    apr.potencia_kW.astype(str).str.replace(",", "."), errors="coerce") / 1000.0
apr = apr[(apr.situacao == "operacao") & (apr.potencia_MW >= 15)].copy()

# alturas admissiveis REVISADAS (claude_03) quando disponiveis
_rev = os.path.join(D_OUT, "claude_altura_admissivel_revisada.csv")
if os.path.exists(_rev):
    adm = pd.read_csv(_rev, sep=";", decimal=",")
    adm["classe_interferencia"] = np.where(
        adm.limitante.str.startswith("teto"),
        "sem_interferencia_da_cascata", "limitado_por_remanso")
else:
    adm = pd.read_csv(os.path.join(D_TAB, "altura_maxima_admissivel.csv"),
                      sep=";", decimal=",")
    prio = pd.read_csv(os.path.join(D_TAB, "prioridade_eixos_sem_interferencia.csv"),
                       sep=";", decimal=",")
    adm = adm.merge(prio[["eixo", "classe_interferencia"]], on="eixo", how="left")
adm = adm[(adm.altura_max_m > 0)].copy()

DIST_STEM_M = 1500.0   # distancia maxima ao canal principal (m)

# posicao GEOMETRICA de cada aproveitamento e eixo
gex = gpd.GeoDataFrame(apr, geometry=gpd.points_from_xy(apr.lon, apr.lat),
                       crs=4674).to_crs(UTM22)
eixgeo = pd.read_csv(os.path.join(D_CAV, "eixos_todos.csv"), sep=";", decimal=",")
gpr = gpd.GeoDataFrame(eixgeo, geometry=gpd.points_from_xy(eixgeo.lon, eixgeo.lat),
                       crs=4326).to_crs(UTM22).set_index("codigo")

reg_ex, reg_pr = [], []
for _, a in gex.iterrows():
    dkm, zt, dd = estaca_por_ponto(a.geometry.x, a.geometry.y)
    reg_ex.append(dict(nome=a["nome"], potencia_MW=a.potencia_MW,
                       area_km2=a.area_drenagem_km2, dist_km=dkm,
                       cota_talvegue_m=zt, NA_m=a.cota_terreno_m,
                       dist_ao_canal_m=round(dd, 0),
                       no_canal_principal=dd <= DIST_STEM_M))
for _, a in adm.iterrows():
    if a.eixo not in gpr.index: continue
    g = gpr.loc[a.eixo]
    dkm, zt, dd = estaca_por_ponto(g.geometry.x, g.geometry.y)
    reg_pr.append(dict(eixo=a.eixo, area_km2=a.area_km2, dist_km=dkm,
                       cota_eixo_m=a.cota_eixo_m, cota_talvegue_m=zt,
                       altura_max_m=a.altura_max_m,
                       NA_max_m=a.cota_eixo_m + a.altura_max_m,
                       crista_m=a.cota_eixo_m + a.altura_max_m + 3.0,
                       volume_hm3=a.volume_max_hm3,
                       classe=a.classe_interferencia,
                       dist_ao_canal_m=round(dd, 0),
                       no_canal_principal=dd <= DIST_STEM_M))
ex = pd.DataFrame(reg_ex); pr = pd.DataFrame(reg_pr)
log(f"existentes no canal principal: {ex.no_canal_principal.sum()} de {len(ex)}")
log(f"propostos no canal principal:  {pr.no_canal_principal.sum()} de {len(pr)}")

# quedas por trecho entre barramentos do canal principal
tud = pd.concat([
    ex[ex.no_canal_principal].assign(tipo="existente", rot=ex.nome, nivel=ex.NA_m),
    pr[pr.no_canal_principal].assign(tipo="proposto", rot=pr.eixo, nivel=pr.NA_max_m),
], ignore_index=True).sort_values("dist_km")
q = []
for k in range(len(tud) - 1):
    a_, b_ = tud.iloc[k], tud.iloc[k + 1]
    q.append(dict(de=a_.rot, para=b_.rot, tipo_de=a_.tipo, tipo_para=b_.tipo,
                  dist_de_km=round(a_.dist_km, 1), dist_para_km=round(b_.dist_km, 1),
                  extensao_km=round(b_.dist_km - a_.dist_km, 1),
                  cota_de_m=round(a_.nivel, 1), cota_para_m=round(b_.nivel, 1),
                  queda_disponivel_m=round(a_.nivel - b_.nivel, 1)))
qd = pd.DataFrame(q)
qd.to_csv(os.path.join(D_OUT, "claude_quedas_por_trecho.csv"),
          index=False, sep=";", decimal=",")

# =============================================================================
# 4. FIGURA
# =============================================================================
CORES = {
    "sem_interferencia_da_cascata": "#1a7f37",
    "limitado_por_remanso": "#8b1f2e",
    "candidato_prioritario_baixa_interferencia": "#1a7f37",
    "candidato_independente_com_conflito_operacional": "#c26a2a",
    "interferencia_operacional_a_confirmar": "#8a6d3b",
    "cascata_critica_alta_interferencia": "#8b1f2e",
}
ROT = {
    "sem_interferencia_da_cascata": "sem interferência da cascata (teto técnico 120 m)",
    "limitado_por_remanso": "altura limitada pelo remanso da usina de montante",
    "candidato_prioritario_baixa_interferencia": "prioritário — baixa interferência",
    "candidato_independente_com_conflito_operacional": "independente com conflito operacional",
    "interferencia_operacional_a_confirmar": "interferência a confirmar",
    "cascata_critica_alta_interferencia": "cascata crítica — alta interferência",
}

fig, ax = plt.subplots(figsize=(16, 8.5))

# talvegue
ax.fill_between(pf.dist_km, pf.cota_m, pf.cota_m.min() - 30,
                color="#d9cfc1", zorder=1)
ax.plot(pf.dist_km, pf.cota_m, color="#5b4a34", lw=1.6, zorder=3, label="talvegue")

# municipios de referencia
for nome in ["Muçum", "Encantado", "Lajeado", "Estrela", "Bom Retiro do Sul"]:
    g = mun[mun.NM_MUN == nome]
    if not len(g): continue
    dentro = [brs_geom is not None]
    pts = [(pf.dist_km.values[i], pf.cota_m.values[i])
           for i in range(0, len(pf), 5)
           if g.geometry.iloc[0].contains(Point(*xy(*divmod(int(pf.no.values[i]), NX))))]
    if pts:
        dm = np.mean([p[0] for p in pts])
        ax.axvline(dm, color="#9aa0a6", lw=.7, ls=":", zorder=2)
        ax.text(dm, pf.cota_m.max() * .97, nome, rotation=90, va="top", ha="right",
                fontsize=8, color="#5f6368")

# aproveitamentos existentes
for _, a in ex[ex.no_canal_principal].iterrows():
    ax.plot([a.dist_km, a.dist_km], [a.cota_talvegue_m, a.NA_m],
            color="#1f5c8b", lw=3.2, solid_capstyle="butt", zorder=5)
    ax.plot([a.dist_km - 6, a.dist_km], [a.NA_m, a.NA_m],
            color="#1f5c8b", lw=1.1, alpha=.75, zorder=4)
    ax.annotate(f"{a['nome'][:16]}\n{a.potencia_MW:.0f} MW",
                (a.dist_km, a.NA_m), textcoords="offset points", xytext=(0, 7),
                ha="center", fontsize=7.2, color="#1f5c8b", fontweight="bold")

# eixos propostos
for _, a in pr[pr.no_canal_principal].iterrows():
    cor = CORES.get(a.classe, "#666666")
    ax.plot([a.dist_km, a.dist_km], [a.cota_talvegue_m, a.crista_m],
            color=cor, lw=3.2, ls="-", solid_capstyle="butt", zorder=6)
    ax.plot([a.dist_km - 6, a.dist_km], [a.NA_max_m, a.NA_max_m],
            color=cor, lw=1.1, ls="--", alpha=.85, zorder=5)
    ax.annotate(f"{a.eixo}\n{a.altura_max_m:.0f} m · {a.volume_hm3:.0f} hm³",
                (a.dist_km, a.crista_m), textcoords="offset points", xytext=(0, 6),
                ha="center", fontsize=7.6, color=cor, fontweight="bold")

ax.set_xlabel("distância ao longo do talvegue (km) — de montante para jusante")
ax.set_ylabel("cota (m)")
ax.set_title("Divisão de quedas — rio das Antas / Taquari até Bom Retiro do Sul",
             fontsize=14, fontweight="bold", loc="left")
ax.text(0, 1.015,
        "aproveitamentos existentes (azul) e eixos propostos limitados à altura admissível "
        "sem afogar usina de montante",
        transform=ax.transAxes, fontsize=9.5, color="#5f6368")
ax.grid(axis="y", alpha=.25, lw=.6)
ax.set_xlim(pf.dist_km.min(), pf.dist_km.max())
ax.set_ylim(pf.cota_m.min() - 25, max(pf.cota_m.max(), pr.crista_m.max()) * 1.10)
for s in ("top", "right"): ax.spines[s].set_visible(False)

leg = [Line2D([], [], color="#5b4a34", lw=1.8, label="talvegue"),
       Line2D([], [], color="#1f5c8b", lw=3.2, label="aproveitamento existente (NA atual)")]
for k, v in ROT.items():
    if (pr.classe == k).any():
        leg.append(Line2D([], [], color=CORES[k], lw=3.2, label=f"eixo proposto — {v}"))
leg.append(Line2D([], [], color="#666", lw=1.1, ls="--", label="NA máximo (remanso)"))
ax.legend(handles=leg, loc="upper right", frameon=False, fontsize=8.5)

fig.text(0.008, 0.012,
         "Triagem preliminar sobre MDE de 28,6 m. Alturas limitadas pela cota de restituição do "
         "aproveitamento imediatamente a montante (Manual de Inventário Hidroelétrico, MME 2007, item 4.6.1). "
         "Não substitui estudo de remanso.",
         fontsize=7.2, color="#80868b")
fig.tight_layout(rect=[0, 0.025, 1, 1])
out = os.path.join(D_OUT, "claude_divisao_quedas.png")
fig.savefig(out, dpi=170)
log(f"figura gravada: {out}")

pd.set_option("display.width", 200)
print("\n" + "=" * 110)
print("QUEDAS POR TRECHO — canal principal")
print("=" * 110)
print(qd.to_string(index=False))
print("\n" + "=" * 110)
print("EIXOS PROPOSTOS — posicao no perfil")
print("=" * 110)
print(pr[["eixo", "dist_km", "area_km2", "cota_eixo_m", "altura_max_m",
          "NA_max_m", "volume_hm3", "classe", "dist_ao_canal_m",
          "no_canal_principal"]].to_string(index=False))
log("FIM")
