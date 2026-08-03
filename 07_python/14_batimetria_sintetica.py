# -*- coding: utf-8 -*-
"""
EUROCLIMA / Estrela-RS — BATIMETRIA SINTETICA dos reservatorios existentes.

PROBLEMA
--------
O MDE de 28,6 m registra a SUPERFICIE da agua, nao o fundo. Por isso o volume
ARMAZENADO nos reservatorios existentes — e portanto o volume de espera que se
poderia abrir por deplecionamento preventivo, sem obra nenhuma — nao pode ser
lido diretamente do MDE. Essa era a lacuna que travava a analise da alternativa
mais barata de todas.

ABORDAGEM  (adaptação de triagem inspirada em Domeneghetti, WRR 52(4), 2016 —
"On the use of SRTM and altimetry data for flood modeling in data-sparse regions")
------------------------------------------------------------------------------
Domeneghetti mostra que a geometria submersa pode ser INFERIDA, e nao medida,
tratando-a como parametro e amarrando-a a observacoes de superficie. Aqui a
aplicacao e adaptada para reservatorios: a amarracao e geomorfologica em vez
de altimetrica e o resultado e uma curva sintetica de sensibilidade, nao uma
batimetria medida ou calibrada:

  1. O reservatorio e' identificado como o patamar plano no MDE a montante do
     barramento (superficie de agua, cota ~ constante = NA atual).
  2. O TALVEGUE PRE-BARRAMENTO e' reconstruido interpolando o perfil
     longitudinal do rio entre a cauda do remanso (a montante) e o pe da
     barragem (a jusante) — dois trechos onde o MDE ainda enxerga o leito
      natural. Usa-se, nesta triagem, ajuste linear da declividade; a forma do
      perfil deve ser calibrada com secoes de campo.
  3. Em cada secao transversal do reservatorio mede-se a LARGURA do espelho no
     MDE e calcula-se a PROFUNDIDADE como (NA atual - talvegue reconstruido).
  4. A forma da secao submersa e' adotada como parabolica (exponente p),
     forma usual de vales encaixados:  A_submersa = (p/(p+1)) * B * h
  5. O volume submerso e' a integral das areas ao longo do reservatorio.

VALIDACAO CRUZADA
-----------------
A profundidade tambem e' estimada por inversao da equacao de Manning para a
vazao de referencia (procedimento equivalente ao segundo metodo testado por
Domeneghetti):     h = [ (Q n) / (B sqrt(S)) ] ^ (3/5)
As duas estimativas sao reportadas lado a lado. Divergencia grande indica que
o trecho merece batimetria de campo.

Saida: batimetria_sintetica.csv, volume_deplecionamento.csv
"""
import os, time, warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import geopandas as gpd
from osgeo import gdal
from scipy import ndimage
from shapely.geometry import Point

gdal.UseExceptions()

GIS = os.environ["GIS"]; SHP = os.environ["SHP"]
DEST = os.path.join(os.environ["EURO"], "05_MODELAGEM")
D_GIS = os.path.join(DEST, "01_dados", "gis_derivado")
D_TAB = os.path.join(DEST, "06_resultados", "tabelas")
FDR = os.path.join(GIS, "raster", "Fdr.tif")
MDE = os.environ.get("MDE_ANALISE", os.path.join(GIS, "raster", "mdr.tif"))
MDE_FONTE = os.path.basename(MDE)
SUFIXO = "_anadem" if "anadem" in MDE_FONTE.lower() else "_mdr"
UTM22 = 31982

t0 = time.time()
def log(*a): print(f"[{time.time()-t0:7.1f}s]", *a, flush=True)

POT_MIN_MW   = 15.0
TOL_ESPELHO  = 1.5     # m — tolerancia para identificar o patamar de agua
EXP_SECAO    = 2.0     # expoente da secao parabolica (2 = parabola)
MANNING      = 0.030   # canal natural em leito rochoso/cascalho
Q_ESPECIFICO = 0.020   # m3/s/km2 — vazao media de longo termo [CALIBRAR]
DEPLEC       = [1, 2, 3, 5, 8, 10, 15]   # rebaixamentos testados (m)
TRAP = np.trapezoid if hasattr(np, "trapezoid") else np.trapz

# ------------------------------------------------------------------- entradas
ap = gpd.read_file(os.path.join(D_GIS, "aproveitamentos.gpkg"), layer="aneel").to_crs(UTM22)
ap["potencia_MW"] = pd.to_numeric(
    ap.potencia_kW.astype(str).str.replace(",", "."), errors="coerce") / 1000.0
ap = ap[(ap.situacao == "operacao") & (ap.potencia_MW >= POT_MIN_MW)].copy()
ap = ap.sort_values("area_drenagem_km2", ascending=False)
log(f"{len(ap)} aproveitamentos em operacao >= {POT_MIN_MW:.0f} MW")

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
if dsm.RasterXSize == NX and dsm.RasterYSize == NY:
    dem = dsm.GetRasterBand(1).ReadAsArray().astype(np.float32)
else:
    dem = dsm.GetRasterBand(1).ReadAsArray(c1, r1, NX, NY).astype(np.float32)
ndv = dsm.GetRasterBand(1).GetNoDataValue()
if ndv is not None: dem[dem == ndv] = np.nan
log(f"grade {NY} x {NX} | MDE: {MDE}")

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

def caminho_montante(no, npassos=1200):
    """Segue a montante sempre pelo filho de maior area (canal principal)."""
    cam = [no]; i = no
    for _ in range(npassos):
        a, b = off[i], off[i + 1]
        if b <= a: break
        ks = filhos[a:b]
        j = ks[np.argmax(area_km2[ks])]
        cam.append(int(j)); i = int(j)
    return cam

def caminho_jusante(no, npassos=600):
    cam = [no]; i = no
    for _ in range(npassos):
        j = rec[i]
        if j < 0: break
        cam.append(int(j)); i = int(j)
    return cam

# ------------------------------------------------------- ancoragem no espelho
bho = gpd.read_file(os.path.join(SHP, "Drenagem_Bacia_Taquari.shp")).to_crs(UTM22)
bho = bho[bho.geometry.notna()].copy(); sidx = bho.sindex

def ancora_espelho(a):
    cand = bho.iloc[list(sidx.query(a.geometry.buffer(2500)))].copy()
    if len(cand) == 0: return None
    ln = cand.sort_values("nuareamont", ascending=False).iloc[0]
    alvo = float(ln.get("nuareamont", np.nan))
    if not np.isfinite(alvo): return None
    r0, c0 = rc(a.geometry.x, a.geometry.y)
    best = None
    for dr in range(-15, 16):
        for dc in range(-15, 16):
            r, c = r0 + dr, c0 + dc
            if not (0 <= r < NY and 0 <= c < NX): continue
            i = r * NX + c
            if abs(area_km2[i] - alvo) / alvo > 0.20: continue
            z = float(dem[r, c])
            if not np.isfinite(z): continue
            if best is None or z > best[0]: best = (z, r, c, i)
    return best

# ============================================================================
# NUCLEO — reconstrucao da batimetria
# ============================================================================
def reconstroi(a):
    b = ancora_espelho(a)
    if b is None: return None
    z_na, r, c, no = b

    # -------- 1. perfil longitudinal a montante (canal principal) ------------
    cam_m = caminho_montante(no)
    dist_m, cota_m = [], []
    d = 0.0
    for k in range(1, len(cam_m)):
        r1_, c1_ = divmod(cam_m[k - 1], NX); r2_, c2_ = divmod(cam_m[k], NX)
        d += px * (1.4142 if (r1_ != r2_ and c1_ != c2_) else 1.0)
        z = float(dem[r2_, c2_])
        if np.isfinite(z):
            dist_m.append(d); cota_m.append(z)
    dist_m = np.array(dist_m); cota_m = np.array(cota_m)
    if len(dist_m) < 40: return None

    # cauda do remanso: primeira estaca onde a cota supera o NA + tolerancia
    acima = np.where(cota_m > z_na + TOL_ESPELHO)[0]
    if len(acima) == 0: return None
    i_cauda = int(acima[0])
    L_res = float(dist_m[i_cauda])            # comprimento do remanso (m)
    if L_res < 2 * px: return None

    # -------- 2. talvegue pre-barramento ------------------------------------
    # Ajusta o perfil natural usando SO os trechos onde o MDE ve o leito:
    #   (a) a montante da cauda do remanso
    #   (b) a jusante da barragem
    sel_m = (dist_m > L_res) & (dist_m < L_res + 15000)
    cam_j = caminho_jusante(no, 400)
    dist_j, cota_j = [], []
    d = 0.0
    for k in range(1, len(cam_j)):
        r1_, c1_ = divmod(cam_j[k - 1], NX); r2_, c2_ = divmod(cam_j[k], NX)
        d += px * (1.4142 if (r1_ != r2_ and c1_ != c2_) else 1.0)
        z = float(dem[r2_, c2_])
        if np.isfinite(z):
            dist_j.append(-d); cota_j.append(z)
    dist_j = np.array(dist_j); cota_j = np.array(cota_j)

    # declividade natural do trecho, dos dois lados
    S_m = np.polyfit(dist_m[sel_m], cota_m[sel_m], 1)[0] if sel_m.sum() > 10 else np.nan
    S_j = np.polyfit(dist_j, cota_j, 1)[0] if len(dist_j) > 10 else np.nan
    S = np.nanmean([abs(S_m), abs(S_j)])
    if not np.isfinite(S) or S <= 0: S = 1e-3

    # cota do talvegue no pe da barragem: extrapola do trecho de jusante
    z_pe = float(np.interp(0, dist_j[::-1], cota_j[::-1])) if len(dist_j) else z_na
    # perfil pre-barramento dentro do remanso: linear com a declividade natural
    def z_talvegue(dd):
        return z_pe + S * dd

    # -------- 3. largura do espelho por estaca ------------------------------
    mask = bfs(no).reshape(NY, NX)
    espelho = mask & np.isfinite(dem) & (dem <= z_na + TOL_ESPELHO)
    lab, _ = ndimage.label(espelho, structure=np.ones((3, 3)))
    if lab[r, c] == 0: return None
    espelho = lab == lab[r, c]

    larguras, profs, dists = [], [], []
    for k in range(1, i_cauda + 1):
        i_no = cam_m[k]
        rr_, cc_ = divmod(i_no, NX)
        # direcao do escoamento -> perpendicular
        kfd = int(fdr[rr_, cc_])
        if kfd not in DR: continue
        v = np.array([DC[kfd], -DR[kfd]], float); v /= np.linalg.norm(v)
        nx_, ny_ = -v[1], v[0]
        x0, y0 = xy(rr_, cc_)
        # varre para os dois lados enquanto estiver no espelho
        larg = 0.0
        for sgn in (-1, 1):
            for s in np.arange(px / 2, 4000, px / 2):
                xx, yy = x0 + sgn * nx_ * s, y0 + sgn * ny_ * s
                ri, ci = rc(xx, yy)
                if not (0 <= ri < NY and 0 <= ci < NX): break
                if not espelho[ri, ci]: break
                larg += px / 2
        dd = float(dist_m[k - 1]) if k - 1 < len(dist_m) else 0.0
        h = z_na - z_talvegue(dd)
        if larg <= 0 or h <= 0: continue
        larguras.append(larg); profs.append(h); dists.append(dd)

    if len(larguras) < 3: return None
    B = np.array(larguras); H = np.array(profs); D = np.array(dists)

    # -------- 4. volume submerso (secao parabolica) -------------------------
    kf = EXP_SECAO / (EXP_SECAO + 1.0)          # 2/3 para parabola
    A_sub = kf * B * H
    ordem = np.argsort(D)
    V_sub = float(TRAP(A_sub[ordem], D[ordem]))     # m3

    # -------- 5. validacao cruzada por Manning ------------------------------
    Q_ref = float(area_km2[no]) * Q_ESPECIFICO
    B_med = float(np.median(B))
    h_manning = ((Q_ref * MANNING) / (B_med * np.sqrt(S))) ** 0.6
    razao = float(np.mean(H) / max(h_manning, 1e-6))
    if razao > 10:
        qualidade = "revisar — profundidade muito acima de Manning"
    elif razao < 0.5:
        qualidade = "revisar — profundidade abaixo de Manning"
    elif L_res < 1000:
        qualidade = "revisar — remanso curto"
    else:
        qualidade = "triagem utilizável, requer calibração"

    # -------- 6. volume liberavel por deplecionamento -----------------------
    dep = {}
    for dh in DEPLEC:
        Hd = np.clip(H - dh, 0, None)
        # volume entre NA e NA-dh: integral da area do espelho na faixa
        # aproximada pela largura na cota correspondente (secao parabolica)
        Bd = B * np.sqrt(np.clip(1 - dh / np.maximum(H, 1e-6), 0, 1))
        # Todas as grandezas devem seguir a mesma ordenacao longitudinal.
        # O erro anterior reordenava D mas deixava B/Bd na ordem original.
        B_ord, Bd_ord = B[ordem], Bd[ordem]
        V_faixa = float(TRAP(
            ((B_ord + Bd_ord) / 2) * np.minimum(dh, H[ordem]), D[ordem]
        ))
        dep[f"V_deplec_{dh}m_hm3"] = round(V_faixa / 1e6, 1)

    return dict(
        nome=a["nome"], mde_fonte=MDE_FONTE, potencia_MW=round(a.potencia_MW, 1),
        area_drenagem_km2=round(float(area_km2[no]), 1),
        NA_atual_m=round(z_na, 1),
        compr_remanso_km=round(L_res / 1000.0, 2),
        declividade=round(float(S), 6),
        larg_media_m=round(float(np.mean(B)), 1),
        prof_media_m=round(float(np.mean(H)), 1),
        prof_max_m=round(float(np.max(H)), 1),
        prof_Manning_m=round(float(h_manning), 1),
        razao_prof=round(razao, 2),
        qualidade_triagem=qualidade,
        area_espelho_km2=round(float(espelho.sum() * cell / 1e6), 2),
        V_submerso_hm3=round(V_sub / 1e6, 1),
        **dep)

log("reconstruindo batimetria...")
regs = []
for _, a in ap.iterrows():
    try:
        r = reconstroi(a)
    except Exception as e:
        log(f"  {a['nome'][:26]}: erro — {e}"); continue
    if r is None:
        log(f"  {a['nome'][:26]:<26} — nao foi possivel reconstruir")
        continue
    regs.append(r)
    log(f"  {r['nome'][:26]:<26} remanso {r['compr_remanso_km']:>5.1f} km  "
        f"larg {r['larg_media_m']:>6.0f} m  prof {r['prof_media_m']:>5.1f} m  "
        f"(Manning {r['prof_Manning_m']:>5.1f} m)  V={r['V_submerso_hm3']:>7.1f} hm3")

df = pd.DataFrame(regs)
if not len(df):
    raise SystemExit("nenhum reservatorio reconstruido")
for nome_saida in ("batimetria_sintetica.csv", f"batimetria_sintetica{SUFIXO}.csv"):
    df.to_csv(os.path.join(D_TAB, nome_saida), index=False, sep=";", decimal=",")

pd.set_option("display.width", 240)
print("\n" + "=" * 128)
print("BATIMETRIA SINTETICA — geometria submersa inferida (abordagem Domeneghetti 2016)")
print("=" * 128)
print(df[["nome", "potencia_MW", "area_drenagem_km2", "NA_atual_m", "compr_remanso_km",
          "larg_media_m", "prof_media_m", "prof_Manning_m", "razao_prof",
          "area_espelho_km2", "V_submerso_hm3"]].to_string(index=False))

print("\n  razao_prof = profundidade reconstruida / profundidade por Manning.")
print("  Valores proximos de 1 indicam consistencia entre os dois metodos;")
print("  muito acima de 1 indica reservatorio profundo (vale afogado), o que e'")
print("  esperado; muito abaixo de 1 sugere reconstrucao subestimada.")

print("\n" + "=" * 128)
print("VOLUME LIBERAVEL POR DEPLECIONAMENTO PREVENTIVO — sem obra nenhuma")
print("=" * 128)
cols = ["nome", "potencia_MW", "V_submerso_hm3"] + [f"V_deplec_{d}m_hm3" for d in DEPLEC]
print(df[cols].to_string(index=False))

print("\n" + "-" * 128)
for d in DEPLEC:
    col = f"V_deplec_{d}m_hm3"
    print(f"  deplecionamento de {d:>2d} m em toda a cascata: {df[col].sum():>8,.0f} hm3"
          f"   ({100*df[col].sum()/3230:>5.1f}% do volume necessario)")
print(f"\n  Volume submerso total da cascata: {df.V_submerso_hm3.sum():,.0f} hm3")
print("  Referencia: 3.230 hm3 e' o volume necessario para evitar os danos de 2024.")

for nome_saida in ("volume_deplecionamento.csv", f"volume_deplecionamento{SUFIXO}.csv"):
    df[["nome", "mde_fonte", "potencia_MW", "V_submerso_hm3"] +
       [f"V_deplec_{d}m_hm3" for d in DEPLEC]].to_csv(
        os.path.join(D_TAB, nome_saida), index=False, sep=";", decimal=",")
log("FIM")
