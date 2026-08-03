# -*- coding: utf-8 -*-
"""
EUROCLIMA / Estrela-RS — VALIDACAO DO EIXO EXPLORATORIO MC2 (Monte Claro 2).

Contexto: na rodada isolada (OUTPUT_TAG=mc2) o eixo recebeu area de drenagem
D8 igual a ZERO. O diagnostico (claude_08) mostrou que a linha CRUZA o canal —
ha' celula com 12.225 km2 na estaca 400 m — e que a falha esta' na funcao de
ancoragem de `10_eixos_cascata.py`:

    perto = bho[bho.geometry.distance(geom) < 400]
    ln = perto.sort_values("nuareamont", ascending=False).iloc[0]

Ela escolhe o trecho BHO de MAIOR AREA no raio de 400 m, e nao o que de fato
INTERCEPTA a linha. No caso do MC2 havia dois trechos do mesmo curso: um a 0 m
com 12.318,5 km2 e outro a 397 m com 12.423,8 km2. Escolheu o segundo, projetou
o ponto de ancoragem na extremidade da linha e a janela de busca de +/-10
celulas (+/-286 m) nao alcancou o canal.

Aqui a ancoragem e' refeita com o criterio correto — entre os trechos que
efetivamente interceptam a linha, o de maior area — e o candidato e' validado
nos sete itens pedidos. NAO se promove o eixo a E13; recebe codigo provisorio.

Saidas (06_resultados/CLAUDE/):
  claude_mc2_validacao.csv     — ficha do candidato
  claude_mc2_cav.csv           — curva cota-area-volume PCHIP de 1 m
  claude_mc2_interferencia.csv — remanso e balanco energetico por altura
"""
import os, re, time, zipfile, warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import geopandas as gpd
from osgeo import gdal
from scipy import ndimage
from shapely.geometry import Point, LineString

gdal.UseExceptions()

GIS = os.environ["GIS"]; SHP = os.environ["SHP"]
EXTRA = os.environ["EXTRA_KMZ"]
DEST = os.path.join(os.environ["EURO"], "05_MODELAGEM")
D_CAV = os.path.join(DEST, "01_dados", "cav")
D_TAB = os.path.join(DEST, "06_resultados", "tabelas")
D_OUT = os.path.join(DEST, "06_resultados", "CLAUDE")
D_SNIRH = os.path.join(DEST, "01_dados", "cav_snirh")
FDR = os.path.join(GIS, "raster", "Fdr.tif")
MDE = os.path.join(GIS, "raster", "mdr.tif")
UTM22 = 31982
RD = dict(sep=";", decimal=",", encoding="utf-8-sig")
os.makedirs(D_OUT, exist_ok=True)

t0 = time.time()
def log(*a): print(f"[{time.time()-t0:6.1f}s]", *a, flush=True)

CODIGO = "MC2"            # codigo PROVISORIO — nao e' E13
CRISTA_M, TAL_M, TAL_J, BORDA = 10.0, 2.5, 2.0, 3.0
C_ATERRO, C_VERT, C_DESAP = 90.0, 8_000.0, 45_000.0
ALTURAS = list(range(10, 125, 5))
Q_ESPEC = 0.0269          # calibrada com Qmlt oficial SNIRH
RAZAO_CRIT = 0.55
K_EF, PERDA_CARGA, FK = 0.0088, 0.02, 0.55
FOLGA_M, H_TETO_M = 2.0, 120.0

# =========================================================== geometria e grade
z = zipfile.ZipFile(EXTRA)
kml = next(n for n in z.namelist() if n.lower().endswith(".kml"))
txt = z.read(kml).decode("utf-8", "ignore")
m = re.search(r"<coordinates>(.*?)</coordinates>", txt, re.S)
pts_ll = [tuple(map(float, t.split(",")[:2])) for t in m.group(1).split()]
linha = gpd.GeoSeries([LineString(pts_ll)], crs=4326).to_crs(UTM22).iloc[0]

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
    d = rec[fr]; m_ = d >= 0
    if not m_.any(): break
    fs, dx = fr[m_], d[m_].astype(np.int64)
    np.add.at(acc, dx, acc[fs]); np.add.at(indeg, dx, -1)
    al = np.unique(dx); fr = al[indeg[al] == 0].astype(np.int32)
area = acc.astype(np.float32) * cell / 1e6

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

# =============================================== ANCORAGEM CORRIGIDA
print("=" * 104)
print("1. ANCORAGEM — criterio corrigido")
print("=" * 104)
bho = gpd.read_file(os.path.join(SHP, "Drenagem_Bacia_Taquari.shp")).to_crs(UTM22)
bho = bho[bho.geometry.notna()].copy()
bho["d"] = bho.geometry.distance(linha)

# CRITERIO CORRETO: entre os trechos que efetivamente INTERCEPTAM a linha
# (distancia praticamente nula), o de maior area de montante.
intercepta = bho[bho.d <= px / 2]
if len(intercepta):
    ln_bho = intercepta.sort_values("nuareamont", ascending=False).iloc[0]
    criterio = "trecho BHO que intercepta a linha, de maior area"
else:
    ln_bho = bho.sort_values("d").iloc[0]
    criterio = "trecho BHO mais proximo (nenhum intercepta)"
alvo = float(ln_bho.nuareamont)
print(f"  criterio ............ {criterio}")
print(f"  area BHO de referencia: {alvo:,.1f} km2 (distancia {ln_bho.d:.1f} m)")

# celula D8: a de MAIOR area sobre a propria linha
best = None
for s in np.arange(0, linha.length + 1, px / 4):
    p = linha.interpolate(min(s, linha.length))
    r_, c_ = rc(p.x, p.y)
    if not (0 <= r_ < NY and 0 <= c_ < NX): continue
    i = r_ * NX + c_
    if best is None or area[i] > best[0]:
        best = (float(area[i]), r_, c_, i, float(s))
a_d8, r_, c_, no, s_star = best
z_eixo = float(dem[r_, c_])
ll = gpd.GeoSeries([Point(*xy(r_, c_))], crs=UTM22).to_crs(4326).iloc[0]
print(f"  celula D8 na linha .. {a_d8:,.1f} km2 | cota {z_eixo:.1f} m | estaca {s_star:.0f} m")
print(f"  aderencia a BHO ..... {100*(a_d8/alvo-1):+.2f} %")
print(f"  coordenadas ......... {ll.y:.6f}, {ll.x:.6f}")

mask = bfs(no)
print(f"  bacia delineada ..... {mask.sum()*cell/1e6:,.1f} km2")

# =============================================== 2. POSICAO LONGITUDINAL
print("\n" + "=" * 104)
print("2. POSICAO LONGITUDINAL E RELACAO COM A CARTEIRA")
print("=" * 104)
pf = pd.read_csv(os.path.join(D_OUT, "claude_perfil_principal.csv"), **RD)
_xy = pf[["x_utm", "y_utm"]].values
d2 = (_xy[:, 0] - xy(r_, c_)[0]) ** 2 + (_xy[:, 1] - xy(r_, c_)[1]) ** 2
k = int(np.argmin(d2))
estaca_km = float(pf.dist_km.values[k]); dist_canal = float(np.sqrt(d2[k]))
print(f"  estaca no perfil principal: {estaca_km:.1f} km "
      f"(distancia ao traco: {dist_canal:.0f} m)")

eix = pd.read_csv(os.path.join(D_CAV, "eixos_todos.csv"), **RD)
geix = gpd.GeoDataFrame(eix, geometry=gpd.points_from_xy(eix.lon, eix.lat),
                        crs=4326).to_crs(UTM22)
pmc2 = Point(*xy(r_, c_))
geix["dist_MC2_m"] = geix.geometry.distance(pmc2)
viz = geix.nsmallest(3, "dist_MC2_m")[["codigo", "area_km2", "cota_eixo_m", "dist_MC2_m"]]
print("\n  eixos da carteira mais proximos:")
print(viz.to_string(index=False))

# =============================================== 3. CAV (PCHIP de 1 m)
print("\n" + "=" * 104)
print("3. CURVA COTA-AREA-VOLUME")
print("=" * 104)
m2 = mask.reshape(NY, NX)
rs, cs = np.where(m2)
a1, a2, b1, b2 = rs.min(), rs.max() + 1, cs.min(), cs.max() + 1
sm, sz = m2[a1:a2, b1:b2], dem[a1:a2, b1:b2]
lr, lc = r_ - a1, c_ - b1
est3 = np.ones((3, 3))
cav_pts = []
for H in ALTURAS:
    niv = z_eixo + H
    lab, _ = ndimage.label(sm & np.isfinite(sz) & (sz <= niv), structure=est3)
    if lab[lr, lc] == 0: continue
    res = lab == lab[lr, lc]
    cav_pts.append(dict(altura_m=H, cota_NA_m=round(niv, 1),
                        area_alagada_km2=round(res.sum() * cell / 1e6, 3),
                        volume_hm3=round(float(np.nansum(niv - sz[res])) * cell / 1e6, 2)))
cav = pd.DataFrame(cav_pts)

# densificacao PCHIP de 1 m — mesma metodologia dos demais eixos
def pchip_slopes(x, y):
    h = np.diff(x); delta = np.diff(y) / h
    d = np.zeros_like(y, float)
    for k2 in range(1, len(x) - 1):
        if delta[k2 - 1] * delta[k2] > 0:
            w1 = 2 * h[k2] + h[k2 - 1]; w2 = h[k2] + 2 * h[k2 - 1]
            d[k2] = (w1 + w2) / (w1 / delta[k2 - 1] + w2 / delta[k2])
    d[0] = ((2 * h[0] + h[1]) * delta[0] - h[0] * delta[1]) / (h[0] + h[1])
    if d[0] * delta[0] <= 0: d[0] = 0.0
    elif delta[0] * delta[1] < 0 and abs(d[0]) > abs(3 * delta[0]): d[0] = 3 * delta[0]
    d[-1] = ((2 * h[-1] + h[-2]) * delta[-1] - h[-1] * delta[-2]) / (h[-1] + h[-2])
    if d[-1] * delta[-1] <= 0: d[-1] = 0.0
    elif delta[-1] * delta[-2] < 0 and abs(d[-1]) > abs(3 * delta[-1]): d[-1] = 3 * delta[-1]
    return d

def pchip(x, y, q):
    sl = pchip_slopes(x, y)
    idx = np.clip(np.searchsorted(x, q, "right") - 1, 0, len(x) - 2)
    h = x[idx + 1] - x[idx]; t = (q - x[idx]) / h
    t2, t3 = t * t, t * t * t
    return ((2*t3-3*t2+1)*y[idx] + (t3-2*t2+t)*h*sl[idx]
            + (-2*t3+3*t2)*y[idx+1] + (t3-t2)*h*sl[idx+1])

xh = cav.altura_m.to_numpy(float)
q1 = np.arange(int(xh.min()), int(xh.max()) + 1, 1.0)
dens = pd.DataFrame(dict(
    eixo=CODIGO, altura_m=q1, cota_NA_m=np.round(z_eixo + q1, 1),
    area_alagada_km2=np.round(pchip(xh, cav.area_alagada_km2.to_numpy(float), q1), 3),
    volume_hm3=np.round(pchip(xh, cav.volume_hm3.to_numpy(float), q1), 2),
    metodo="PCHIP monotonica entre pontos MDE de 5 m",
    confiabilidade="B - CAV do MDE natural, eixo sem reservatorio"))
dens.to_csv(os.path.join(D_OUT, "claude_mc2_cav.csv"), index=False, sep=";", decimal=",")
print(cav.to_string(index=False))
f_vol = lambda h: float(np.interp(h, dens.altura_m, dens.volume_hm3))
f_are = lambda h: float(np.interp(h, dens.altura_m, dens.area_alagada_km2))

# =============================================== 4. INTERFERENCIA / REMANSO
print("\n" + "=" * 104)
print("4. INTERFERENCIA COM MONTE CLARO E 14 DE JULHO")
print("=" * 104)
fic = pd.read_csv(os.path.join(D_SNIRH, "cav_snirh_ficha_tecnica.csv"), **RD)
curv = pd.read_csv(os.path.join(D_SNIRH, "curvas", "cav_snirh_consolidada.csv"), **RD)
base = curv.groupby("usina").cota_sl_m.min().rename("cota_leito_m")
fic = fic.merge(base, on="usina", how="left")
fic["queda_bruta_m"] = fic.cota_normal_sl_m - fic.cota_leito_m
fic["Ef_atual_MWmed"] = np.minimum(
    K_EF * fic.queda_bruta_m * (1 - PERDA_CARGA) * fic.qmlt_m3_s * RAZAO_CRIT,
    fic.potencia_mw)
print(fic[["usina", "cota_leito_m", "cota_normal_sl_m",
           "cota_minima_operacional_sl_m", "queda_bruta_m",
           "Ef_atual_MWmed"]].to_string(index=False))

# usina imediatamente a MONTANTE do MC2, por posicao longitudinal
apr = pd.read_csv(os.path.join(D_TAB, "aproveitamentos_existentes.csv"), **RD)
gapr = gpd.GeoDataFrame(apr, geometry=gpd.points_from_xy(apr.lon, apr.lat),
                        crs=4674).to_crs(UTM22)
est_ap, dcan_ap = [], []
for g in gapr.geometry:
    dd = (_xy[:, 0] - g.x) ** 2 + (_xy[:, 1] - g.y) ** 2
    j = int(np.argmin(dd))
    est_ap.append(float(pf.dist_km.values[j])); dcan_ap.append(float(np.sqrt(dd[j])))
apr["estaca_km"] = est_ap; apr["dist_canal_m"] = dcan_ap
apr["z_talv"] = np.interp(apr.estaca_km, pf.dist_km, pf.cota_m)
apr["valida"] = ((apr.situacao == "operacao") & (apr.dist_canal_m <= 1500)
                 & ((apr.cota_terreno_m - apr.z_talv).abs() <= 40))
mont = apr[apr.valida & (apr.estaca_km < estaca_km) & (apr.cota_terreno_m > z_eixo)]
if len(mont):
    lim = mont.loc[mont.estaca_km.idxmax()]
    h_rem = float(lim.cota_terreno_m) - FOLGA_M - z_eixo
    print(f"\n  usina imediatamente a montante: {lim['nome']} "
          f"(estaca {lim.estaca_km:.1f} km, cota {lim.cota_terreno_m:.1f} m)")
else:
    lim, h_rem = None, np.inf
    print("\n  nenhuma usina em operacao a montante no canal principal")

h_adm = min(h_rem, H_TETO_M)
limitante = ("remanso do aproveitamento de montante" if h_rem < H_TETO_M
             else "teto tecnico (remanso nao e' limitante)")
print(f"  altura por remanso .. {h_rem:.1f} m")
print(f"  altura admissivel ... {h_adm:.1f} m  ({limitante})")
print(f"  volume nessa altura . {f_vol(h_adm):,.1f} hm3 | area {f_are(h_adm):.2f} km2")

# =============================================== 5. ENERGIA E BALANCO
print("\n" + "=" * 104)
print("5. ENERGIA NOVA, PERDA A MONTANTE E BALANCO LIQUIDO")
print("=" * 104)
Q_novo = a_d8 * Q_ESPEC * RAZAO_CRIT
regs = []
for H in [10, 20, 30, 40, 50, 60, 80, 100, 120]:
    NA = z_eixo + H
    Hl = H * (1 - PERDA_CARGA)
    Ef_novo = K_EF * Hl * Q_novo
    perda, veto, quem = 0.0, False, ""
    for _, u in fic.iterrows():
        # a usina so e' afetada se estiver a MONTANTE (cota de leito acima)
        if u.cota_leito_m <= z_eixo: continue
        dh = min(max(NA - u.cota_leito_m, 0.0), u.queda_bruta_m)
        if dh > 0:
            p_ = K_EF * dh * (1 - PERDA_CARGA) * u.qmlt_m3_s * RAZAO_CRIT
            if p_ > perda: perda, quem = p_, u.usina
        if NA >= u.cota_minima_operacional_sl_m and u.cota_leito_m > z_eixo:
            veto = True
    regs.append(dict(
        eixo=CODIGO, altura_m=H, cota_NA_m=round(NA, 1),
        volume_hm3=round(f_vol(H), 1), area_alagada_km2=round(f_are(H), 2),
        Ef_novo_MWmed=round(Ef_novo, 1),
        perda_montante_MWmed=round(perda, 2), usina_afetada=quem,
        Ef_liquido_MWmed=round(Ef_novo - perda, 1),
        VETO_min_operacional=veto,
        dentro_da_altura_admissivel=bool(H <= h_adm)))
itf = pd.DataFrame(regs)
itf.to_csv(os.path.join(D_OUT, "claude_mc2_interferencia.csv"),
           index=False, sep=";", decimal=",")
pd.set_option("display.width", 220)
print(itf.to_string(index=False))

# =============================================== 6. GEOMETRIA E CUSTO
kfd = int(fdr[r_, c_])
v = np.array([DC.get(kfd, 1), -DR.get(kfd, 0)], float); v /= (np.linalg.norm(v) or 1)
nx_, ny_ = -v[1], v[0]
x0, y0 = xy(r_, c_)
s_ = np.arange(-6000, 6000 + px / 2, px / 2)
zs = np.array([dem[rc(x0 + nx_ * t, y0 + ny_ * t)] if
               (0 <= rc(x0 + nx_ * t, y0 + ny_ * t)[0] < NY and
                0 <= rc(x0 + nx_ * t, y0 + ny_ * t)[1] < NX) else np.nan for t in s_])
def geom_barragem(H):
    crista = z_eixo + H + BORDA
    i0 = len(s_) // 2
    def lim_(dirn):
        i = i0
        while 0 < i < len(s_) - 1:
            i += dirn
            if np.isfinite(zs[i]) and zs[i] >= crista: return i
        return i
    iE, iD = lim_(-1), lim_(+1)
    ss, zz = s_[iE:iD + 1], zs[iE:iD + 1]
    if len(ss) < 2: return np.nan, np.nan
    Lc = float(ss[-1] - ss[0]); dsx = float(np.mean(np.diff(ss)))
    hl = np.clip(crista - zz, 0, None); hl[~np.isfinite(hl)] = 0
    mm = (TAL_M + TAL_J) / 2.0
    V = float(np.sum(CRISTA_M * hl + mm * hl ** 2) * dsx)
    return Lc, V / 1e6

L_cr, V_at = geom_barragem(h_adm)
custo = ((V_at * 1e6 * C_ATERRO + L_cr * C_VERT
          + f_are(h_adm) * 100 * C_DESAP) * 1.35 / 1e6) if np.isfinite(L_cr) else np.nan

# =============================================== FICHA FINAL
ficha = pd.DataFrame([dict(
    codigo_provisorio=CODIGO,
    nome_origem="EIXO-MONTECLARO2",
    arquivo=os.path.basename(EXTRA),
    lat=round(ll.y, 6), lon=round(ll.x, 6),
    extensao_linha_m=round(linha.length, 1),
    estaca_perfil_km=round(estaca_km, 1),
    dist_ao_canal_principal_m=round(dist_canal, 0),
    area_D8_km2=round(a_d8, 1), area_BHO_km2=round(alvo, 1),
    aderencia_BHO_pct=round(100 * (a_d8 / alvo - 1), 2),
    cota_eixo_MDE_m=round(z_eixo, 1),
    altura_remanso_m=round(h_rem, 1) if np.isfinite(h_rem) else np.nan,
    altura_admissivel_m=round(h_adm, 1), limitante=limitante,
    restricao_montante=(lim["nome"] if lim is not None else "sem restricao"),
    volume_admissivel_hm3=round(f_vol(h_adm), 1),
    area_alagada_km2=round(f_are(h_adm), 2),
    L_crista_m=round(L_cr, 1) if np.isfinite(L_cr) else np.nan,
    V_aterro_hm3=round(V_at, 3) if np.isfinite(V_at) else np.nan,
    custo_MRS=round(custo) if np.isfinite(custo) else np.nan,
    confiabilidade_CAV="B - MDE natural, eixo sem reservatorio",
    alt_KML_nao_usada="altitudes do Google Earth; datum nao conferido")])
ficha.to_csv(os.path.join(D_OUT, "claude_mc2_validacao.csv"),
             index=False, sep=";", decimal=",")

print("\n" + "=" * 104)
print("FICHA DO CANDIDATO")
print("=" * 104)
for k2, v2 in ficha.iloc[0].items():
    print(f"  {k2:<32} {v2}")
log("FIM")
