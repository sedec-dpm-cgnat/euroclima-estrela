# -*- coding: utf-8 -*-
"""
EUROCLIMA / Estrela-RS — pipeline GENERICO de eixos de barragem.

Le TODOS os eixos (linhas ou pontos cujo nome contenha EIXO / BARRAGEM) de
qualquer .kmz/.kml da pasta, e para cada um:
  - ancora no canal via BHO/ANA + grid D8
  - delineia a bacia contribuinte
  - monta a curva cota-area-volume
  - extrai a geometria da barragem (crista, aterro) e o custo preliminar
  - identifica a TOPOLOGIA (quem esta a montante de quem) para permitir
    analise de alternativas em CASCATA

Basta acrescentar novos eixos ao KMZ e rodar de novo — nada precisa ser
alterado no codigo.

Saidas: eixos_todos.csv, cav_todos.csv, geometria_todos.csv,
        topologia_eixos.csv, bacias_todas.gpkg
"""
import os, re, time, glob, zipfile, warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import geopandas as gpd
from osgeo import gdal, ogr, osr
from scipy import ndimage
from shapely.geometry import Point, LineString

gdal.UseExceptions()

GIS = os.environ["GIS"]; SHP = os.environ["SHP"]; KMZ = os.environ["KMZ"]
DEST = os.path.join(os.environ["EURO"], "05_MODELAGEM")
D_GIS = os.path.join(DEST, "01_dados", "gis_derivado")
D_CAV = os.path.join(DEST, "01_dados", "cav")
FDR = os.path.join(GIS, "raster", "Fdr.tif")
MDE = os.path.join(GIS, "raster", "mdr.tif")
UTM22 = 31982
for d in (D_GIS, D_CAV): os.makedirs(d, exist_ok=True)

t0 = time.time()
def log(*a): print(f"[{time.time()-t0:7.1f}s]", *a, flush=True)

CRISTA_M, TAL_M, TAL_J, BORDA = 10.0, 2.5, 2.0, 3.0
C_ATERRO, C_VERT, C_DESAP = 90.0, 8_000.0, 45_000.0
ALTURAS = list(range(10, 125, 5))
PADRAO_EIXO = re.compile(r"(EIXO|BARRAGEM|BARRAG)", re.I)

# ------------------------------------------------------------- 1. le os eixos
def le_eixos(pasta):
    """Le os eixos do KMZ mais recente da pasta. Nomes repetidos (varios
    'EIXO') recebem sufixo provisorio; a numeracao definitiva e' atribuida
    depois, de montante para jusante."""
    arqs = sorted(glob.glob(os.path.join(pasta, "*.km[lz]")),
                  key=os.path.getmtime, reverse=True)
    # usa o arquivo mais recente que contenha eixos; ignora os antigos
    arqs = [max(arqs, key=os.path.getmtime)] if arqs else []
    out = []
    for fp in arqs:
        if fp.lower().endswith(".kmz"):
            with zipfile.ZipFile(fp) as z:
                k = next(n for n in z.namelist() if n.lower().endswith(".kml"))
                txt = z.read(k).decode("utf-8", "ignore")
        else:
            txt = open(fp, encoding="utf-8", errors="ignore").read()
        for pm in re.findall(r"<Placemark>(.*?)</Placemark>", txt, re.S):
            n = re.search(r"<name>(.*?)</name>", pm, re.S)
            if not n: continue
            nome = n.group(1).strip()
            if not PADRAO_EIXO.search(nome): continue
            m = re.search(r"<coordinates>(.*?)</coordinates>", pm, re.S)
            if not m: continue
            pts = [tuple(map(float, tk.split(",")[:2])) for tk in m.group(1).split()]
            if len(pts) < 1: continue
            g = LineString(pts) if len(pts) > 1 else Point(pts[0])
            out.append(dict(rotulo=nome, fonte=os.path.basename(fp), geometry=g))
    g = gpd.GeoDataFrame(out, crs=4326).to_crs(UTM22)
    # prioriza LINHAS sobre pontos e descarta pontos que coincidam com uma linha
    g["prio"] = np.where(g.geom_type == "LineString", 0, 1)
    g = g.sort_values("prio").reset_index(drop=True)
    manter = []
    for i, r in g.iterrows():
        if r.prio == 1:  # ponto: descarta se ja existe linha a menos de 2,5 km
            linhas = g[(g.prio == 0)]
            if len(linhas) and linhas.geometry.distance(r.geometry).min() < 2500:
                continue
        manter.append(i)
    g = g.loc[manter].drop(columns="prio").reset_index(drop=True)
    g["eixo"] = [f"{r.rotulo}#{i:02d}" for i, r in g.iterrows()]
    return g

eixos = le_eixos(KMZ)
log(f"{len(eixos)} eixo(s) encontrado(s): {list(eixos.eixo)}")

# ------------------------------------------------------------------- 2. grade
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
log(f"grade {NY} x {NX} = {N/1e6:.1f} M celulas")

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

# --------------------------------------------------------- 3. ancoragem BHO
bho = gpd.read_file(os.path.join(SHP, "Drenagem_Bacia_Taquari.shp")).to_crs(UTM22)
bho = bho[bho.geometry.notna()].copy()

def ancora(geom):
    perto = bho[bho.geometry.distance(geom) < 400]
    if len(perto) == 0:
        perto = bho[bho.geometry.distance(geom) < 3000]
    if len(perto) == 0: return None
    ln = perto.sort_values("nuareamont", ascending=False).iloc[0]
    alvo = float(ln.get("nuareamont", np.nan))
    if geom.geom_type == "LineString":
        s = min((geom.interpolate(t).distance(ln.geometry), t)
                for t in np.arange(0, geom.length, px / 2))[1]
        p = geom.interpolate(s)
    else:
        p = geom
    r0, c0 = rc(p.x, p.y)
    best = None
    for dr in range(-10, 11):
        for dc in range(-10, 11):
            r, c = r0 + dr, c0 + dc
            if not (0 <= r < NY and 0 <= c < NX): continue
            i = r * NX + c
            sc = abs(area[i] - alvo) if np.isfinite(alvo) else -area[i]
            if best is None or sc < best[0]: best = (sc, r, c, i, float(area[i]), alvo)
    return best

log("ancorando eixos e delineando bacias...")
info = []
for _, e in eixos.iterrows():
    b = ancora(e.geometry)
    if b is None:
        log(f"  {e.eixo}: sem drenagem proxima — IGNORADO"); continue
    _, r, c, i, a, alvo = b
    mask = bfs(i)
    ll = gpd.GeoSeries([Point(*xy(r, c))], crs=UTM22).to_crs(4326).iloc[0]
    info.append(dict(eixo=e.eixo, fonte=e.fonte, no=i, r=r, c=c,
                     area_km2=round(a, 1), area_BHO_km2=round(alvo, 1),
                     cota_eixo_m=round(float(dem[r, c]), 1),
                     lat=round(ll.y, 5), lon=round(ll.x, 5),
                     tipo_geom=e.geometry.geom_type,
                     compr_eixo_m=round(e.geometry.length, 1)
                     if e.geometry.geom_type == "LineString" else np.nan,
                     _mask=mask))
    log(f"  {e.eixo:<18} D8={a:>10,.1f} km2  (BHO={alvo:>10,.1f})  cota {dem[r,c]:>6.1f} m")

# ------------------------------------------------------------ 4. topologia
log("montando topologia (quem esta a montante de quem)...")
topo = []
for i, a in enumerate(info):
    for j, b in enumerate(info):
        if i == j: continue
        if a["_mask"][b["no"]]:          # b esta dentro da bacia de a
            topo.append(dict(eixo=a["eixo"], montante=b["eixo"],
                             area_eixo_km2=a["area_km2"],
                             area_montante_km2=b["area_km2"]))
topo = pd.DataFrame(topo)

# ------------------------------------- 4b. NUMERACAO LOGICA (montante->jusante)
# Convencao de inventario hidreletrico: numera-se de montante para jusante.
# Ordena-se por area de drenagem crescente; empates sao resolvidos pela cota.
log("atribuindo numeracao logica de montante para jusante...")
ordem = sorted(range(len(info)),
               key=lambda k: (info[k]["area_km2"], -info[k]["cota_eixo_m"]))
rot = {}
for pos, k in enumerate(ordem, start=1):
    novo = f"E{pos:02d}"
    rot[info[k]["eixo"]] = novo
    info[k]["codigo"] = novo
    info[k]["ordem"] = pos
if len(topo):
    topo["eixo"] = topo["eixo"].map(rot)
    topo["montante"] = topo["montante"].map(rot)

# quantos eixos ha a montante de cada um, e area incremental
for e in info:
    ms = topo[topo.eixo == e["codigo"]]["montante"].tolist() if len(topo) else []
    e["n_montante"] = len(ms)
    e["eixos_montante"] = ",".join(sorted(ms))
    # area incremental = area propria - soma das areas dos montantes IMEDIATOS
    if ms:
        areas_m = [x["area_km2"] for x in info if x["codigo"] in ms]
        # montantes imediatos: os que nao estao a montante de outro montante
        imed = [m for m in ms
                if not any((topo.eixo == m) & (topo.montante.isin(ms)))] if len(topo) else ms
        areas_i = [x["area_km2"] for x in info if x["codigo"] in imed]
        e["area_incremental_km2"] = round(e["area_km2"] - sum(areas_i), 1)
    else:
        e["area_incremental_km2"] = e["area_km2"]

if len(topo):
    log(f"  {len(topo)} relacoes de aninhamento")
    for _, t in topo.iterrows():
        log(f"    {t.montante} a MONTANTE de {t.eixo}")
else:
    log("  nenhum aninhamento: todos os eixos sao independentes")

# ---------------------------------------------------- 5. CAV e geometria
def perfil_transv(e, alcance=6000):
    k = int(fdr[e["r"], e["c"]])
    if k not in DR: ux, uy = 1.0, 0.0
    else:
        v = np.array([DC[k], -DR[k]], float); ux, uy = v / np.linalg.norm(v)
    nx_, ny_ = -uy, ux
    s = np.arange(-alcance, alcance + px / 2, px / 2)
    X = xy(e["r"], e["c"])[0] + nx_ * s
    Y = xy(e["r"], e["c"])[1] + ny_ * s
    Z = []
    for a_, b_ in zip(X, Y):
        r, c = rc(a_, b_)
        Z.append(float(dem[r, c]) if (0 <= r < NY and 0 <= c < NX) else np.nan)
    return s, np.array(Z)

def geometria(e, H):
    s, z = e["_perfil"]
    z0 = e["cota_eixo_m"]; crista = z0 + H + BORDA
    i0 = len(s) // 2
    def lim(dirn):
        i = i0
        while 0 < i < len(s) - 1:
            i += dirn
            if np.isfinite(z[i]) and z[i] >= crista: return i
        return i
    iE, iD = lim(-1), lim(+1)
    ss, zz = s[iE:iD + 1], z[iE:iD + 1]
    if len(ss) < 2: return None
    L = float(ss[-1] - ss[0]); dsx = float(np.mean(np.diff(ss)))
    h = np.clip(crista - zz, 0, None); h[~np.isfinite(h)] = 0
    m = (TAL_M + TAL_J) / 2.0
    V = float(np.sum(CRISTA_M * h + m * h ** 2) * dsx)
    return dict(L_crista_m=round(L, 1), V_aterro_hm3=round(V / 1e6, 3),
                cota_crista_m=round(crista, 1))

def cav(e, H):
    m = e["_mask"]; rs, cs = np.where(m.reshape(NY, NX))
    a1, a2, b1, b2 = rs.min(), rs.max() + 1, cs.min(), cs.max() + 1
    sm = m.reshape(NY, NX)[a1:a2, b1:b2]; sz = dem[a1:a2, b1:b2]
    lr, lc = e["r"] - a1, e["c"] - b1
    niv = e["cota_eixo_m"] + H
    lab, _ = ndimage.label(sm & np.isfinite(sz) & (sz <= niv), structure=np.ones((3, 3)))
    if lab[lr, lc] == 0: return 0.0, 0.0
    res = lab == lab[lr, lc]
    return (res.sum() * cell / 1e6,
            float(np.nansum(niv - sz[res])) * cell / 1e6)

log("perfis transversais, CAV e geometria...")
regs = []
for e in info:
    e["_perfil"] = perfil_transv(e)
    for H in ALTURAS:
        g = geometria(e, H)
        if g is None: continue
        a_km2, v_hm3 = cav(e, H)
        ca = g["V_aterro_hm3"] * 1e6 * C_ATERRO
        cv = g["L_crista_m"] * C_VERT
        cd = a_km2 * 100 * C_DESAP
        regs.append(dict(eixo=e["codigo"], rotulo_kmz=e["eixo"], altura_m=H,
                         cota_eixo_m=e["cota_eixo_m"], cota_NA_m=round(e["cota_eixo_m"] + H, 1),
                         cota_crista_m=g["cota_crista_m"],
                         area_controlada_km2=e["area_km2"],
                         L_crista_m=g["L_crista_m"], V_aterro_hm3=g["V_aterro_hm3"],
                         area_alagada_km2=round(a_km2, 2), volume_hm3=round(v_hm3, 1),
                         custo_total_MRS=round((ca + cv + cd) * 1.35 / 1e6, 1)))
    log(f"  {e['codigo']} ok")

df = pd.DataFrame(regs)
df.to_csv(os.path.join(D_CAV, "geometria_todos.csv"), index=False, sep=";", decimal=",")
df[["eixo", "altura_m", "cota_NA_m", "area_alagada_km2", "volume_hm3"]].to_csv(
    os.path.join(D_CAV, "cav_todos.csv"), index=False, sep=";", decimal=",")
res = pd.DataFrame([{k: v for k, v in e.items() if not k.startswith("_")} for e in info])
res.drop(columns=["no", "r", "c"]).to_csv(
    os.path.join(D_CAV, "eixos_todos.csv"), index=False, sep=";", decimal=",")
topo.to_csv(os.path.join(D_CAV, "topologia_eixos.csv"), index=False, sep=";", decimal=",")

# ------------------------------------------------------------- 6. geometrias
def poligoniza(mask1d, campos):
    mem = gdal.GetDriverByName("MEM").Create("", NX, NY, 1, gdal.GDT_Byte)
    mem.SetGeoTransform(gt)
    s = osr.SpatialReference(); s.ImportFromEPSG(UTM22); mem.SetProjection(s.ExportToWkt())
    mem.GetRasterBand(1).WriteArray(mask1d.reshape(NY, NX).astype(np.uint8))
    tp = os.path.join(D_GIS, "_tp.geojson")
    if os.path.exists(tp): os.remove(tp)
    dv = ogr.GetDriverByName("GeoJSON").CreateDataSource(tp)
    ly = dv.CreateLayer("p", s, ogr.wkbPolygon)
    ly.CreateField(ogr.FieldDefn("val", ogr.OFTInteger))
    gdal.Polygonize(mem.GetRasterBand(1), mem.GetRasterBand(1), ly, 0)
    dv = None
    g = gpd.read_file(tp); os.remove(tp)
    g = g[g.val == 1].dissolve()
    for k, v in campos.items(): g[k] = v
    return g[list(campos) + ["geometry"]]

log("exportando bacias...")
bs = [poligoniza(e["_mask"], dict(eixo=e["codigo"], area_km2=e["area_km2"],
                                  cota_eixo_m=e["cota_eixo_m"])) for e in info]
gpd.GeoDataFrame(pd.concat(bs, ignore_index=True), crs=UTM22).to_file(
    os.path.join(D_GIS, "bacias_todas.gpkg"), layer="bacias", driver="GPKG")
eixos.to_file(os.path.join(D_GIS, "bacias_todas.gpkg"), layer="eixos", driver="GPKG")

pd.set_option("display.width", 220)
print("\n" + "=" * 100)
print("EIXOS")
print("=" * 100)
print(res.drop(columns=["no", "r", "c", "_mask"], errors="ignore").to_string(index=False))
print("\n" + "=" * 100)
print("TOPOLOGIA (aninhamento)")
print("=" * 100)
print(topo.to_string(index=False) if len(topo) else "  todos independentes")
log("FIM")
