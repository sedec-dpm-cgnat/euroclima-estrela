# -*- coding: utf-8 -*-
"""Propõe um eixo exploratório preliminar no rio Guaporé.

O eixo é uma geometria de triagem perpendicular ao talvegue BHO. A finalidade
é testar área contribuinte, CAV, interferências e roteamento; não é uma locação
de engenharia nem uma recomendação de obra.
"""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
import html

import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString, Point


ROOT = Path(__file__).resolve().parents[1]
GIS = ROOT / "06_resultados" / "GIS"
TAB = ROOT / "06_resultados" / "tabelas"
SHP_DIR = GIS / "SHP"
SRC = (
    ROOT.parent
    / "Documentos EUROCLIMA+"
    / "Espanha"
    / "GIS"
    / "shapefiles"
    / "Drenagem_Bacia_Taquari.shp"
)
OUT_REDE = GIS / "guapore_rede_principal.gpkg"
OUT_KMZ = GIS / "eixo_guapore_proposto.kmz"
OUT_CSV = TAB / "eixo_guapore_proposto.csv"

if not SRC.exists():
    raise FileNotFoundError(f"Rede BHO não encontrada: {SRC}")

rede = gpd.read_file(SRC)
guapore = rede[
    rede["noriocomp"].astype(str).str.contains("Guapore", case=False, na=False)
].copy().drop(columns=["fid"], errors="ignore")
if guapore.empty:
    raise RuntimeError("Nenhum trecho do rio Guaporé foi localizado na BHO")

# Segmento inferior disponível no recorte BHO, com aproximadamente 1.994 km²
# a montante e 2.487 km² de área total da bacia do Guaporé.
COTRECHO = 2681952
sel = guapore[guapore["cotrecho"] == COTRECHO]
if sel.empty:
    raise RuntimeError(f"Trecho Guaporé {COTRECHO} não encontrado")

rede_utm = guapore.to_crs(31982)
GIS.mkdir(parents=True, exist_ok=True)
TAB.mkdir(parents=True, exist_ok=True)
SHP_DIR.mkdir(parents=True, exist_ok=True)
rede_utm.to_file(OUT_REDE, layer="guapore_principal", driver="GPKG")
row = rede_utm[rede_utm["cotrecho"] == COTRECHO].iloc[0]
line = row.geometry
mid = line.interpolate(0.5, normalized=True)
p0 = line.interpolate(0.40, normalized=True)
p1 = line.interpolate(0.60, normalized=True)
dx, dy = p1.x - p0.x, p1.y - p0.y
norm = (dx * dx + dy * dy) ** 0.5
if norm == 0:
    raise RuntimeError("Trecho BHO sem direção geométrica válida")
nx, ny = -dy / norm, dx / norm
comprimento = 1800.0
a = Point(mid.x - nx * comprimento / 2, mid.y - ny * comprimento / 2)
b = Point(mid.x + nx * comprimento / 2, mid.y + ny * comprimento / 2)
eixo = LineString([a, b])
mid_ll = gpd.GeoSeries([mid], crs=31982).to_crs(4326).iloc[0]
eixo_ll = gpd.GeoSeries([eixo], crs=31982).to_crs(4326).iloc[0]

area_mont = float(row["nuareamont"])
area_total = float(row["nuareabacc"])
rec = {
    "codigo": "GU1-PROPOSTO",
    "nome": "Guaporé inferior — triagem a montante",
    "cotrecho_bho": COTRECHO,
    "cocursodag": int(row["cocursodag"]),
    "lon": mid_ll.x,
    "lat": mid_ll.y,
    "area_montante_km2": area_mont,
    "area_total_guapore_km2": area_total,
    "fracao_guapore_controlada": area_mont / area_total,
    "cota_eixo_m": None,
    "comprimento_eixo_triagem_m": comprimento,
    "distancia_foz_bho_km": float(row["nudistbact"]),
    "classe": "eixo exploratório de controle de cheias",
    "status": "triagem; não selecionado",
    "fonte": "BHO Drenagem_Bacia_Taquari; geometria normal ao talvegue",
}

pd.DataFrame([rec]).to_csv(OUT_CSV, sep=";", decimal=",", index=False, encoding="utf-8-sig")
eixo_gdf = gpd.GeoDataFrame(pd.DataFrame([rec]), geometry=[eixo], crs=31982)
eixo_gdf.to_file(
    GIS / "eixo_guapore_proposto.gpkg", layer="eixo_guapore", driver="GPKG"
)
eixo_gdf.to_file(SHP_DIR / "eixo_guapore_proposto.shp", driver="ESRI Shapefile", encoding="UTF-8")

desc = (
    f"<b>GU1-PROPOSTO</b><br/>Guaporé inferior — triagem a montante<br/>"
    f"Área BHO a montante: {area_mont:.1f} km² ({area_mont / area_total:.1%})<br/>"
    f"Trecho BHO: {COTRECHO}<br/>"
    "Eixo geométrico preliminar; não é locação de engenharia. Validar MDE, geologia, "
    "remanso, ocupação, licenciamento, CAV e interferência com aproveitamentos existentes."
)
coords = " ".join(f"{x},{y},0" for x, y in eixo_ll.coords)
kml = f'''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2"><Document>
<name>Eixo exploratório no rio Guaporé</name>
<Style id="eixo"><LineStyle><color>ff00ffff</color><width>5</width></LineStyle></Style>
<Style id="ponto"><IconStyle><scale>1.2</scale><Icon><href>http://maps.google.com/mapfiles/kml/pushpin/blu-pushpin.png</href></Icon></IconStyle></Style>
<Placemark><name>EIXO-GU1-PROPOSTO</name><description><![CDATA[{html.escape(desc)}]]></description>
<styleUrl>#eixo</styleUrl><LineString><tessellate>1</tessellate><coordinates>{coords}</coordinates></LineString></Placemark>
<Placemark><name>EIXO-GU1-PROPOSTO — ponto médio</name><styleUrl>#ponto</styleUrl>
<Point><coordinates>{mid_ll.x},{mid_ll.y},0</coordinates></Point></Placemark>
</Document></kml>'''
kml_path = GIS / "eixo_guapore_proposto.kml"
kml_path.write_text(kml, encoding="utf-8")
with ZipFile(OUT_KMZ, "w", ZIP_DEFLATED) as z:
    z.write(kml_path, "doc.kml")
kml_path.unlink()

print(f"KMZ: {OUT_KMZ}")
print(f"CSV: {OUT_CSV}")
print(pd.DataFrame([rec]).to_string(index=False))
