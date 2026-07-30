# -*- coding: utf-8 -*-
"""
EUROCLIMA / Estrela-RS — perfil longitudinal do talvegue (divisao de quedas).

Percorre o canal principal a partir do eixo mais a montante ate Bom Retiro do
Sul, seguindo as direcoes de fluxo D8, e registra em cada estaca:
    distancia acumulada, cota do talvegue, area de drenagem, municipio.

Marca a posicao dos eixos de barragem (EIXO-A/B/C do EUROCLIMA.kmz), de modo a
permitir o desenho da divisao de quedas no padrao de inventario hidreletrico:
talvegue, NA maximo normal, NA maximo maximorum e crista de cada barramento.

Saidas: perfil_talvegue.csv, eixos_no_perfil.csv, perfil_talvegue.gpkg
"""
import os, re, time, zipfile, warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import geopandas as gpd
from osgeo import gdal
from shapely.geometry import Point, LineString

gdal.UseExceptions()

GIS = os.environ["GIS"]; SHP = os.environ["SHP"]; KMZ = os.environ["KMZ"]
DEST = os.path.join(os.environ["EURO"], "05_MODELAGEM")
D_GIS = os.path.join(DEST, "01_dados", "gis_derivado")
D_TAB = os.path.join(DEST, "06_resultados", "tabelas")
FDR = os.path.join(GIS, "raster", "Fdr.tif")
MDE = os.path.join(GIS, "raster", "mdr.tif")
UTM22 = 31982

t0 = time.time()
def log(*a): print(f"[{time.time()-t0:7.1f}s]", *a, flush=True)

# --------------------------------------------------------------- 1. contexto
mun = gpd.read_file(os.path.join(SHP, "Municipios_RS.shp")).to_crs(UTM22)
bac = gpd.read_file(os.path.join(SHP, "Bacia_Hidrografica_Taquari.shp")).to_crs(UTM22)

z = zipfile.ZipFile(os.path.join(KMZ, "EUROCLIMA.kmz"))
txt = z.read("doc.kml").decode("utf-8", "ignore")
eixos = []
for pm in re.findall(r"<Placemark>(.*?)</Placemark>", txt, re.S):
    n = re.search(r"<name>(.*?)</name>", pm, re.S)
    if not n: continue
    nome = n.group(1).strip()
    if not nome.startswith("EIXO"): continue
    m = re.search(r"<coordinates>(.*?)</coordinates>", pm, re.S)
    pts = [tuple(map(float, tk.split(",")[:2])) for tk in m.group(1).split()]
    eixos.append(dict(nome=nome, geometry=LineString(pts)))
eixos = gpd.GeoDataFrame(eixos, crs=4326).to_crs(UTM22)
log(f"eixos: {list(eixos.nome)}")

# --------------------------------------------------------------- 2. rasters
bx = bac.total_bounds
cx = mun[mun.NM_MUN.isin(["Bom Retiro do Sul", "Taquari", "Estrela"])].total_bounds
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

log("acumulacao...")
tem = rec >= 0
cnt = np.bincount(rec[tem].astype(np.int64), minlength=N).astype(np.int32)
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

# -------------------------------------------- 3. localiza os eixos no canal
bho = gpd.read_file(os.path.join(SHP, "Drenagem_Bacia_Taquari.shp")).to_crs(UTM22)
bho = bho[bho.geometry.notna()].copy()

def snap_eixo(geom):
    """Ancora o eixo no canal: usa a BHO/ANA como referencia de area de
    drenagem e procura, numa janela do grid D8, a celula cuja area acumulada
    mais se aproxima dela. O snap direto sobre o grid falha quando o canal
    derivado do MDE esta deslocado do rio real."""
    perto = bho[bho.geometry.distance(geom) < 400].copy()
    if len(perto) == 0:
        perto = bho[bho.geometry.distance(geom) < 3000].copy()
    if len(perto) == 0:
        return None
    ln = perto.sort_values("nuareamont", ascending=False).iloc[0]
    alvo = float(ln.get("nuareamont", np.nan))
    # ponto do eixo mais proximo desse trecho da BHO
    d = [(geom.interpolate(s).distance(ln.geometry), s)
         for s in np.arange(0, geom.length, px / 2)]
    s_star = min(d)[1]
    p = geom.interpolate(s_star)
    r0, c0 = rc(p.x, p.y)
    best = None
    for dr in range(-10, 11):
        for dc in range(-10, 11):
            r, c = r0 + dr, c0 + dc
            if not (0 <= r < NY and 0 <= c < NX): continue
            i = r * NX + c
            s = abs(area[i] - alvo) if np.isfinite(alvo) else -area[i]
            if best is None or s < best[0]:
                best = (s, float(area[i]), r, c, i, alvo)
    return best

locs = []
for _, e in eixos.iterrows():
    b = snap_eixo(e.geometry)
    if b is None:
        log(f"  {e.nome}: NAO foi possivel ancorar no canal"); continue
    _, a, r, c, i, alvo = b
    locs.append(dict(eixo=e.nome, no=i, r=r, c=c, area_km2=round(a, 1),
                     area_BHO_km2=round(alvo, 1),
                     cota_talvegue_m=round(float(dem[r, c]), 1),
                     compr_eixo_m=round(e.geometry.length, 1)))
    log(f"  {e.nome}: D8={a:,.1f} km2 (BHO={alvo:,.1f})  cota {dem[r,c]:.1f} m  "
        f"eixo {e.geometry.length:,.0f} m")
locs = pd.DataFrame(locs)

# --------------------------------- 4. percorre o talvegue ate Bom Retiro do Sul
brs = mun[mun.NM_MUN == "Bom Retiro do Sul"].geometry.iloc[0]
# o perfil da divisao de quedas segue o EIXO PRINCIPAL: o eixo mais a jusante
# (maior area) esta sobre o rio principal; a montante dele o talvegue principal
# e' o do maior ramo. Parte-se, portanto, do maior eixo que NAO seja o de jusante.
locs = locs.sort_values("area_km2", ascending=False).reset_index(drop=True)
eixo_jus = locs.iloc[0]
montantes = locs.iloc[1:]
principal = montantes.iloc[0] if len(montantes) else eixo_jus
inicio = int(principal["no"])
log(f"eixo de jusante: {eixo_jus['eixo']} ({eixo_jus['area_km2']:,.0f} km2)")
log(f"perfil principal parte de: {principal['eixo']} ({principal['area_km2']:,.0f} km2)")

perc = []
i = inicio; dist = 0.0; passo = 0
vistos = set()
while i >= 0 and passo < 200000:
    if i in vistos: break
    vistos.add(i)
    r, c = divmod(i, NX)
    x, y = xy(r, c)
    perc.append(dict(no=i, dist_km=dist / 1000.0, x=x, y=y,
                     cota_m=float(dem[r, c]), area_km2=float(area[i])))
    nxt = rec[i]
    if nxt < 0: break
    r2_, c2_ = divmod(nxt, NX)
    dist += px * (1.4142 if (r2_ != r and c2_ != c) else 1.0)
    i = nxt
    passo += 1

pf = pd.DataFrame(perc)
log(f"perfil: {len(pf)} estacas, {pf.dist_km.max():.1f} km, "
    f"cota {pf.cota_m.iloc[0]:.0f} -> {pf.cota_m.iloc[-1]:.0f} m")

# suaviza o talvegue (o MDE tem ruido no leito)
pf["cota_suave_m"] = pf.cota_m.rolling(15, center=True, min_periods=1).min() \
                                .rolling(25, center=True, min_periods=1).mean()
# garante monotonia decrescente para jusante
pf["cota_talvegue_m"] = np.minimum.accumulate(pf.cota_suave_m.values)

# municipio de cada estaca
gp = gpd.GeoDataFrame(pf, geometry=gpd.points_from_xy(pf.x, pf.y), crs=UTM22)
gp = gpd.sjoin(gp, mun[["NM_MUN", "geometry"]], how="left", predicate="within")
pf["municipio"] = gp.NM_MUN.values

# trunca o perfil no limite de jusante de Bom Retiro do Sul
em_brs = pf.index[pf.municipio == "Bom Retiro do Sul"]
if len(em_brs):
    pf = pf.loc[:em_brs.max()].copy().reset_index(drop=True)
    log(f"perfil truncado em Bom Retiro do Sul: {pf.dist_km.max():.1f} km")

# posicao dos eixos ao longo do perfil
locs["dist_km"] = [float(pf.loc[pf.no == n, "dist_km"].iloc[0])
                   if (pf.no == n).any() else np.nan for n in locs.no]
locs["cota_perfil_m"] = [float(pf.loc[pf.no == n, "cota_talvegue_m"].iloc[0])
                         if (pf.no == n).any() else np.nan for n in locs.no]

print("\n" + "=" * 88)
print("EIXOS AO LONGO DO PERFIL")
print("=" * 88)
print(locs.to_string(index=False))

print("\n" + "=" * 88)
print("PERFIL POR MUNICIPIO")
print("=" * 88)
res = pf.groupby("municipio", dropna=True).agg(
    dist_ini_km=("dist_km", "min"), dist_fim_km=("dist_km", "max"),
    cota_mont_m=("cota_talvegue_m", "max"), cota_jus_m=("cota_talvegue_m", "min"),
    area_ini=("area_km2", "min"), area_fim=("area_km2", "max")).reset_index()
res["extensao_km"] = (res.dist_fim_km - res.dist_ini_km).round(1)
res["desnivel_m"] = (res.cota_mont_m - res.cota_jus_m).round(1)
res["decliv_m_km"] = (res.desnivel_m / res.extensao_km.replace(0, np.nan)).round(2)
print(res.sort_values("dist_ini_km").to_string(index=False))

pf.drop(columns=["no", "cota_suave_m"]).to_csv(
    os.path.join(D_TAB, "perfil_talvegue.csv"), index=False, sep=";", decimal=",")
locs.to_csv(os.path.join(D_TAB, "eixos_no_perfil.csv"), index=False, sep=";", decimal=",")

gpd.GeoDataFrame(pf[["dist_km", "cota_talvegue_m", "area_km2", "municipio"]],
                 geometry=gpd.points_from_xy(pf.x, pf.y), crs=UTM22).to_file(
    os.path.join(D_GIS, "perfil_talvegue.gpkg"), layer="estacas", driver="GPKG")
gpd.GeoDataFrame([{"geometry": LineString(list(zip(pf.x, pf.y)))}], crs=UTM22).to_file(
    os.path.join(D_GIS, "perfil_talvegue.gpkg"), layer="traco", driver="GPKG")
log("FIM")
