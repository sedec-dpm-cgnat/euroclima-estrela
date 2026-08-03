# -*- coding: utf-8 -*-
"""
EUROCLIMA / Estrela-RS — INSUMOS DO MODELO HEC-RAS 1D.

Levanta, a partir da base geoespacial, tudo o que o modelo unidimensional
precisa ter representado no trecho contratado de 39,4 km:

  1. eixo do rio (river centerline) e estaqueamento
  2. locacao das secoes transversais, com espacamento diferenciado
  3. travessias — rodovias federais e estaduais que cruzam o trecho
  4. confluencias dos tributarios, com area de drenagem de cada um
  5. limites municipais ao longo do trecho
  6. condicoes de contorno de montante, laterais e jusante
  7. declividade por sub-trecho, para a condicao de normal depth

Decisao fixada: HEC-RAS EXCLUSIVAMENTE 1D.

Saidas (06_resultados/CLAUDE/):
  claude_hecras_eixo_rio.csv         — estaqueamento do eixo
  claude_hecras_secoes.csv           — locacao proposta das secoes
  claude_hecras_travessias.csv       — pontes e travessias
  claude_hecras_confluencias.csv     — afluentes e areas de drenagem
  claude_hecras_contornos.csv        — condicoes de contorno
  claude_hecras_eixo.gpkg            — geometrias para o QGIS/RAS Mapper
"""
import os, re, time, zipfile, warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import geopandas as gpd
from osgeo import gdal
from shapely.geometry import Point, LineString
from shapely.ops import substring

gdal.UseExceptions()

GIS = os.environ["GIS"]; SHP = os.environ["SHP"]; KMZ = os.environ["KMZ"]
DEST = os.path.join(os.environ["EURO"], "05_MODELAGEM")
D_OUT = os.path.join(DEST, "06_resultados", "CLAUDE")
MDE = os.path.join(GIS, "raster", "mdr.tif")
UTM22 = 31982
os.makedirs(D_OUT, exist_ok=True)

t0 = time.time()
def log(*a): print(f"[{time.time()-t0:6.1f}s]", *a, flush=True)

ESP_DETALHE_M = 200.0     # espacamento de secoes no trecho urbano
ESP_GERAL_M   = 500.0     # espacamento no restante
BUF_TRECHO_M  = 400.0     # busca de travessias

# =============================================================================
# 1. EIXO DO RIO — trecho contratado
# =============================================================================
z = zipfile.ZipFile(os.path.join(KMZ, "EUROCLIMA-rev.kmz")
                    if os.path.exists(os.path.join(KMZ, "EUROCLIMA-rev.kmz"))
                    else os.path.join(KMZ, "EUROCLIMA.kmz"))
kml = next(n for n in z.namelist() if n.lower().endswith(".kml"))
txt = z.read(kml).decode("utf-8", "ignore")
trecho = None
for pm in re.findall(r"<Placemark>(.*?)</Placemark>", txt, re.S):
    n = re.search(r"<name>(.*?)</name>", pm, re.S)
    if not n or "Trecho_Modelagem" not in n.group(1): continue
    c = re.search(r"<coordinates>(.*?)</coordinates>", pm, re.S)
    pts = [tuple(map(float, t.split(",")[:2])) for t in c.group(1).split()]
    trecho = LineString(pts)
if trecho is None:
    raise SystemExit("Trecho_Modelagem nao encontrado no KMZ")
eixo = gpd.GeoSeries([trecho], crs=4326).to_crs(UTM22).iloc[0]
L = eixo.length
log(f"trecho de modelagem: {L/1000:.2f} km")

# poligono do levantamento LiDAR delimita o SUB-TRECHO DETALHADO
lidar = None
for pm in re.findall(r"<Placemark>(.*?)</Placemark>", txt, re.S):
    n = re.search(r"<name>(.*?)</name>", pm, re.S)
    if not n or "AreaLIDAR" not in n.group(1): continue
    anel = re.search(r"<outerBoundaryIs>(.*?)</outerBoundaryIs>", pm, re.S)
    c = re.search(r"<coordinates>(.*?)</coordinates>", anel.group(1) if anel else pm, re.S)
    pts = [tuple(map(float, t.split(",")[:2])) for t in c.group(1).split()]
    from shapely.geometry import Polygon
    lidar = gpd.GeoSeries([Polygon(pts)], crs=4326).to_crs(UTM22).iloc[0]
log(f"area LiDAR (sub-trecho detalhado): "
    f"{lidar.area/1e6:.2f} km2" if lidar is not None else "sem area LiDAR")

# =============================================================================
# 2. ESTAQUEAMENTO E COTA DO TALVEGUE
# =============================================================================
ds = gdal.Open(MDE); gt = ds.GetGeoTransform(); band = ds.GetRasterBand(1)
ndv = band.GetNoDataValue()
def cota(x, y):
    c = int((x - gt[0]) / gt[1]); r = int((y - gt[3]) / gt[5])
    if not (0 <= r < ds.RasterYSize and 0 <= c < ds.RasterXSize): return np.nan
    v = band.ReadAsArray(c, r, 1, 1)
    if v is None: return np.nan
    v = float(v[0, 0])
    return np.nan if (ndv is not None and v == ndv) else v

# O estaqueamento do HEC-RAS cresce de JUSANTE para MONTANTE.
# Verifica-se o sentido do tracado pela cota das extremidades.
z_ini, z_fim = cota(*eixo.coords[0]), cota(*eixo.coords[-1])
inverter = np.isfinite(z_ini) and np.isfinite(z_fim) and z_ini < z_fim
if inverter:
    eixo = LineString(list(eixo.coords)[::-1])
    log("tracado invertido: o KMZ vinha de jusante para montante")
log(f"cota nas extremidades: {cota(*eixo.coords[0]):.1f} m -> "
    f"{cota(*eixo.coords[-1]):.1f} m")

passo = 50.0
est = []
for s in np.arange(0, L + passo, passo):
    p = eixo.interpolate(min(s, L))
    est.append(dict(dist_montante_m=round(float(s), 1),
                    estaca_ras_m=round(float(L - s), 1),   # RAS: cresce p/ montante
                    x=p.x, y=p.y, cota_m=cota(p.x, p.y)))
ex = pd.DataFrame(est)
ex["cota_talvegue_m"] = np.minimum.accumulate(
    ex.cota_m.rolling(9, center=True, min_periods=1).min().values)
ex.to_csv(os.path.join(D_OUT, "claude_hecras_eixo_rio.csv"),
          index=False, sep=";", decimal=",")
decliv = (ex.cota_talvegue_m.iloc[0] - ex.cota_talvegue_m.iloc[-1]) / (L / 1000)
log(f"declividade media do trecho: {decliv:.3f} m/km ({decliv/1000:.6f} m/m)")

# =============================================================================
# 3. SECOES TRANSVERSAIS
# =============================================================================
def no_detalhe(p):
    return lidar is not None and lidar.buffer(500).contains(p)

secoes = []
s = 0.0
i = 1
while s <= L:
    p = eixo.interpolate(s)
    det = no_detalhe(p)
    # largura da secao: maior no detalhe urbano (planicie ampla)
    larg = 3000.0 if det else 4000.0
    # direcao local para orientar a secao
    ds_ = min(50.0, L - s) or 1.0
    p2 = eixo.interpolate(min(s + ds_, L))
    dx, dy = p2.x - p.x, p2.y - p.y
    nrm = np.hypot(dx, dy) or 1.0
    nx, ny = -dy / nrm, dx / nrm
    secoes.append(dict(
        id_secao=f"S{i:03d}", estaca_ras_m=round(L - s, 1),
        dist_montante_km=round(s / 1000, 3),
        x=p.x, y=p.y, cota_talvegue_m=cota(p.x, p.y),
        sub_trecho="detalhado (LiDAR)" if det else "estendido",
        largura_secao_m=larg,
        x_esq=p.x + nx * larg / 2, y_esq=p.y + ny * larg / 2,
        x_dir=p.x - nx * larg / 2, y_dir=p.y - ny * larg / 2))
    s += ESP_DETALHE_M if det else ESP_GERAL_M
    i += 1
sec = pd.DataFrame(secoes)
sec.to_csv(os.path.join(D_OUT, "claude_hecras_secoes.csv"),
           index=False, sep=";", decimal=",")
log(f"{len(sec)} secoes propostas "
    f"({int((sec.sub_trecho=='detalhado (LiDAR)').sum())} no sub-trecho detalhado)")

# =============================================================================
# 4. TRAVESSIAS
# =============================================================================
log("procurando travessias...")
buf = eixo.buffer(BUF_TRECHO_M)
trav = []
for arq, tipo, campo in [("Rodovia_Federal.shp", "rodovia federal", "vl_br"),
                         ("Rodovia_Estadual.shp", "rodovia estadual", "ROD_CODIGO")]:
    p = os.path.join(SHP, arq)
    if not os.path.exists(p): continue
    g = gpd.read_file(p).to_crs(UTM22)
    g = g[g.geometry.notna()]
    g = g[g.geometry.intersects(buf)]
    for _, r in g.iterrows():
        inter = r.geometry.intersection(eixo)
        if inter.is_empty: continue
        pts = [inter] if inter.geom_type == "Point" else list(getattr(inter, "geoms", []))
        for pt in pts:
            if pt.geom_type != "Point": continue
            s_ = eixo.project(pt)
            trav.append(dict(
                tipo=tipo, identificacao=str(r.get(campo, ""))[:20],
                estaca_ras_m=round(L - s_, 1),
                dist_montante_km=round(s_ / 1000, 3),
                x=pt.x, y=pt.y, cota_terreno_m=cota(pt.x, pt.y),
                no_sub_trecho_detalhado=bool(no_detalhe(pt))))
tv = pd.DataFrame(trav).drop_duplicates(subset=["dist_montante_km", "tipo"])
tv = tv.sort_values("dist_montante_km")
# sinaliza travessias cuja cota amostrada destoa do talvegue local: indicam
# ponto de intersecao fora do leito, ou greide de aterro sobre a planicie
if len(tv):
    _z = np.interp(tv.dist_montante_km * 1000, ex.dist_montante_m, ex.cota_talvegue_m)
    tv["cota_talvegue_local_m"] = np.round(_z, 1)
    tv["desnivel_sobre_talvegue_m"] = np.round(tv.cota_terreno_m - _z, 1)
    tv["conferir_locacao"] = tv.desnivel_sobre_talvegue_m.abs() > 6.0
tv.to_csv(os.path.join(D_OUT, "claude_hecras_travessias.csv"),
          index=False, sep=";", decimal=",")
log(f"{len(tv)} travessia(s) sobre o eixo")

# =============================================================================
# 5. CONFLUENCIAS DOS TRIBUTARIOS
# =============================================================================
log("localizando confluencias...")
SUBBACIAS = [("Rio Forqueta", "baciadrenagem_forqueta.shp"),
             ("Arroio Boa Vista", "baciadrenagemarroioboa.shp"),
             ("Arroio Estrela", "baciaarroioestrela.shp"),
             ("Arroio Sampaio", "baciaarroiosampaio.shp"),
             ("Arroio do Meio", "baciadrenagemarroiodomeio.shp"),
             ("Arroio Grande", "baciadrenagemarroiogrande.shp")]
conf = []
for nome, arq in SUBBACIAS:
    p = os.path.join(SHP, arq)
    if not os.path.exists(p): continue
    g = gpd.read_file(p).to_crs(UTM22)
    if not len(g): continue
    area = float(g.geometry.area.sum() / 1e6)
    # confluencia: ponto do eixo mais proximo do limite da sub-bacia
    uni = g.geometry.union_all() if hasattr(g.geometry, "union_all") else g.geometry.unary_union
    d = eixo.distance(uni)
    s_ = eixo.project(uni.centroid)
    pt = eixo.interpolate(s_)
    conf.append(dict(
        tributario=nome, area_drenagem_km2=round(area, 1),
        pct_da_bacia_estrela=round(100 * area / 19440.0, 2),
        estaca_ras_m=round(L - s_, 1), dist_montante_km=round(s_ / 1000, 3),
        x=pt.x, y=pt.y, dist_sub_bacia_ao_eixo_m=round(d, 0),
        no_trecho=bool(d < 2000)))
cf = pd.DataFrame(conf).sort_values("area_drenagem_km2", ascending=False)
cf.to_csv(os.path.join(D_OUT, "claude_hecras_confluencias.csv"),
          index=False, sep=";", decimal=",")

# =============================================================================
# 6. CONDICOES DE CONTORNO
# =============================================================================
z_mont = float(ex.cota_talvegue_m.iloc[0])
z_jus = float(ex.cota_talvegue_m.iloc[-1])
# declividade dos ultimos 5 km, para normal depth de jusante
# A declividade de jusante NAO pode ser tirada do talvegue forcado a
# monotonico: num trecho de planicie o MDE de 28,6 m produz patamares e o
# resultado sai ZERO, o que inviabiliza a condicao de normal depth.
# Usa-se regressao linear sobre a cota BRUTA dos ultimos 10 km.
n10 = int(10000 / passo)
seg = ex.tail(min(n10, len(ex)))
seg = seg[np.isfinite(seg.cota_m)]
if len(seg) > 5:
    coef = np.polyfit(seg.dist_montante_m.values, seg.cota_m.values, 1)
    S_jus = float(-coef[0])          # decaimento por metro, positivo
else:
    S_jus = decliv / 1000
if not np.isfinite(S_jus) or S_jus <= 1e-6:
    S_jus = decliv / 1000            # recorre a declividade media do trecho
    obs_jus = ("declividade local indistinguivel de zero no MDE; adotada a "
               "media do trecho. EXIGE secao topobatimetrica ou curva-chave.")
else:
    obs_jus = ("regressao sobre a cota bruta dos ultimos 10 km")

cont = [
    dict(posicao="montante", tipo="flow hydrograph",
         estaca_ras_m=round(L, 1), cota_talvegue_m=round(z_mont, 1),
         area_drenagem_km2=19440.0,
         fonte="hidrograma do evento de referencia; nos cenarios com barragem, "
               "usar o efluente roteado",
         observacao="posto ANA de Mucum/Encantado propagado, quando disponivel"),
    dict(posicao="jusante", tipo="normal depth",
         estaca_ras_m=0.0, cota_talvegue_m=round(z_jus, 1),
         area_drenagem_km2=23699.0,
         fonte=f"normal depth com S = {S_jus:.6f} m/m ({obs_jus})",
         observacao="TESTAR SENSIBILIDADE: com declividade desta ordem o remanso "
                    "do Guaiba pode governar o nivel em eventos extremos"),
]
for _, r in cf[cf.no_trecho].iterrows():
    cont.append(dict(
        posicao="lateral", tipo="lateral inflow",
        estaca_ras_m=r.estaca_ras_m, cota_talvegue_m=np.nan,
        area_drenagem_km2=r.area_drenagem_km2,
        fonte=f"{r.tributario} — hidrograma escalado por area "
              f"({r.pct_da_bacia_estrela:.2f}% da bacia)",
        observacao="verificar defasagem de pico do tributario"))
ct = pd.DataFrame(cont)
ct.to_csv(os.path.join(D_OUT, "claude_hecras_contornos.csv"),
          index=False, sep=";", decimal=",")

# =============================================================================
# 7. GEOMETRIAS PARA O QGIS / RAS MAPPER
# =============================================================================
gp = os.path.join(D_OUT, "claude_hecras_eixo.gpkg")
gpd.GeoDataFrame([{"nome": "eixo_rio", "compr_km": round(L / 1000, 3),
                   "geometry": eixo}], crs=UTM22).to_file(gp, layer="eixo_rio", driver="GPKG")
gpd.GeoDataFrame(sec, geometry=[LineString([(r.x_esq, r.y_esq), (r.x_dir, r.y_dir)])
                                for _, r in sec.iterrows()],
                 crs=UTM22).to_file(gp, layer="secoes", driver="GPKG")
if len(tv):
    gpd.GeoDataFrame(tv, geometry=gpd.points_from_xy(tv.x, tv.y),
                     crs=UTM22).to_file(gp, layer="travessias", driver="GPKG")
if len(cf):
    gpd.GeoDataFrame(cf, geometry=gpd.points_from_xy(cf.x, cf.y),
                     crs=UTM22).to_file(gp, layer="confluencias", driver="GPKG")

pd.set_option("display.width", 200)
print("\n" + "=" * 112)
print("HEC-RAS 1D — INSUMOS LEVANTADOS")
print("=" * 112)
print(f"\nTrecho: {L/1000:.2f} km | declividade media {decliv:.3f} m/km | "
      f"cota {z_mont:.1f} -> {z_jus:.1f} m")
print(f"Secoes propostas: {len(sec)} "
      f"({ESP_DETALHE_M:.0f} m no detalhe, {ESP_GERAL_M:.0f} m no estendido)")
print("\n--- TRAVESSIAS ---")
print(tv[["tipo", "identificacao", "estaca_ras_m", "dist_montante_km",
          "cota_terreno_m", "cota_talvegue_local_m", "desnivel_sobre_talvegue_m",
          "conferir_locacao", "no_sub_trecho_detalhado"]].to_string(index=False)
      if len(tv) else "  nenhuma identificada no buffer")
print("\n--- CONFLUENCIAS ---")
print(cf[["tributario", "area_drenagem_km2", "pct_da_bacia_estrela",
          "estaca_ras_m", "dist_montante_km", "no_trecho"]].to_string(index=False))
print("\n--- CONDICOES DE CONTORNO ---")
print(ct[["posicao", "tipo", "estaca_ras_m", "area_drenagem_km2", "fonte"]].to_string(index=False))
log("FIM")
