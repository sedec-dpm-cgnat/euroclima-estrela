# -*- coding: utf-8 -*-
"""Propõe eixos de triagem no rio Forqueta e exporta KMZ/CSV.

Os eixos são geometrias exploratórias perpendiculares ao talvegue da BHO. Não
são locações de engenharia: servem para testar CAV, área contribuinte,
interferência e roteamento antes do levantamento topográfico.
"""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import html
import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString, Point

ROOT = Path(__file__).resolve().parents[1]
GIS = ROOT / "06_resultados" / "GIS"
TAB = ROOT / "06_resultados" / "tabelas"
SRC = GIS / "forqueta_rede_principal.gpkg"
OUT_KML = GIS / "eixos_forqueta_propostos.kml"
OUT_KMZ = GIS / "eixos_forqueta_propostos.kmz"
OUT_CSV = TAB / "eixos_forqueta_propostos.csv"

if not SRC.exists():
    raise FileNotFoundError(SRC)

rede = gpd.read_file(SRC, layer="forqueta_principal").to_crs(31982)

# FQ1: eixo inferior, próximo à seção de controle do Forqueta, capturando
# aproximadamente 82,7% da área total do tributário.
# FQ2: eixo intermediário, mantido como sensibilidade para comparar retenção e
# impactos territoriais com uma solução mais a montante.
escolhas = [
    (1244196, "FQ1-PROPOSTO", "Forqueta inferior", 1600.0, "opção condicionada; fora da referência"),
    (4219458, "FQ2-PROPOSTO", "Forqueta intermediário", 1300.0, "sensibilidade exclusiva; fora da referência"),
]

registros = []
geometrias = []
placemarks = []
for cotrecho, codigo, nome, comprimento, status in escolhas:
    sel = rede[rede["cotrecho"] == cotrecho]
    if sel.empty:
        raise ValueError(f"Trecho BHO não encontrado: {cotrecho}")
    row = sel.iloc[0]
    line = row.geometry
    mid = line.interpolate(0.5, normalized=True)
    # Tangente local em torno do ponto médio; o eixo é normal ao talvegue.
    p0 = line.interpolate(0.45, normalized=True)
    p1 = line.interpolate(0.55, normalized=True)
    dx, dy = p1.x - p0.x, p1.y - p0.y
    norm = (dx * dx + dy * dy) ** 0.5
    nx, ny = -dy / norm, dx / norm
    a = Point(mid.x - nx * comprimento / 2, mid.y - ny * comprimento / 2)
    b = Point(mid.x + nx * comprimento / 2, mid.y + ny * comprimento / 2)
    eixo = LineString([a, b])
    ll = gpd.GeoSeries([mid], crs=31982).to_crs(4326).iloc[0]
    eixo_ll = gpd.GeoSeries([eixo], crs=31982).to_crs(4326).iloc[0]
    area_total = float(row["nuareabacc"])
    area_mont = float(row["nuareamont"])
    registros.append({
        "codigo": codigo,
        "nome": nome,
        "cotrecho_bho": int(cotrecho),
        "lon": ll.x,
        "lat": ll.y,
        "x_utm": mid.x,
        "y_utm": mid.y,
        "area_montante_km2": area_mont,
        "area_total_forqueta_km2": area_total,
        "fracao_forqueta_controlada": area_mont / area_total if area_total else None,
        "comprimento_eixo_triagem_m": comprimento,
        "nucomp_trecho_bho_km": float(row["nucomptrec"]),
        "distancia_foz_bho_km": float(row["nudistbact"]),
        "classe": "controle de cheias / retenção de tributário",
        "status": status,
        "fonte": "BHO Drenagem_Bacia_Taquari; geometria normal ao talvegue",
    })
    geometrias.append(eixo)
    desc = (
        f"<b>{codigo}</b><br/>{nome}<br/>"
        f"Área a montante BHO: {area_mont:.1f} km² ({area_mont/area_total:.1%} do Forqueta)<br/>"
        f"Trecho BHO: {int(cotrecho)}<br/>Status: {status}<br/>"
        "Eixo geométrico de triagem; não é locação de engenharia. Validar MDE, geologia, "
        "remanso, reassentamento, licenciamento e CAV antes de qualquer recomendação."
    )
    coords = " ".join(f"{x},{y},0" for x, y in eixo_ll.coords)
    placemarks.append(
        f"<Placemark><name>EIXO-{codigo} — {html.escape(nome)}</name>"
        f"<description><![CDATA[{desc}]]></description>"
        f"<styleUrl>#eixo</styleUrl><LineString><tessellate>1</tessellate>"
        f"<coordinates>{coords}</coordinates></LineString></Placemark>"
    )
    placemarks.append(
        f"<Placemark><name>EIXO-{codigo} — ponto médio</name><styleUrl>#ponto</styleUrl>"
        f"<Point><coordinates>{ll.x},{ll.y},0</coordinates></Point></Placemark>"
    )

pd.DataFrame(registros).to_csv(OUT_CSV, sep=";", decimal=",", index=False, encoding="utf-8-sig")
gpd.GeoDataFrame(pd.DataFrame(registros), geometry=geometrias, crs=31982).to_file(
    GIS / "eixos_forqueta_propostos.gpkg", layer="eixos_forqueta", driver="GPKG"
)

kml = f'''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2"><Document>
<name>Eixos exploratórios no rio Forqueta</name>
<Style id="eixo"><LineStyle><color>ff00a5ff</color><width>5</width></LineStyle></Style>
<Style id="ponto"><IconStyle><scale>1.2</scale><Icon><href>http://maps.google.com/mapfiles/kml/pushpin/ylw-pushpin.png</href></Icon></IconStyle></Style>
<Folder><name>Eixos de triagem Forqueta</name>{''.join(placemarks)}</Folder>
</Document></kml>'''
OUT_KML.write_text(kml, encoding="utf-8")
with ZipFile(OUT_KMZ, "w", ZIP_DEFLATED) as z:
    z.write(OUT_KML, "doc.kml")
OUT_KML.unlink()

print(f"KMZ: {OUT_KMZ}")
print(f"CSV: {OUT_CSV}")
print(pd.DataFrame(registros).to_string(index=False))
