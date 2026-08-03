# -*- coding: utf-8 -*-
"""Organiza produtos GIS e gera GeoPackage mestre, SHP e KMZ de intercâmbio."""
from pathlib import Path
from shutil import copy2
import json
import zipfile
import tempfile
import xml.etree.ElementTree as ET
import geopandas as gpd
import pandas as pd

RAIZ = Path(r"C:\Users\cassi\OneDrive\Documents\SEDEC\PROJETO_EUROCLIMA")
ESP = RAIZ / "Documentos EUROCLIMA+" / "Espanha"
GIS = ESP / "GIS"
DER = RAIZ / "05_MODELAGEM" / "01_dados" / "gis_derivado"
DIRS = {
    "catalogo": GIS / "00_CATALOGO",
    "fontes": GIS / "01_FONTES_ORIGINAIS",
    "gpkg": GIS / "02_GPKG_MESTRE",
    "shp": GIS / "03_SHP_ENTREGA",
    "kmz": GIS / "04_KMZ_ENTREGA",
    "raster": GIS / "05_RASTERS_REFERENCIA",
    "qgis": GIS / "06_PROJETOS_QGIS",
    "socio": GIS / "07_SOCIOECONOMICO",
}
for p in DIRS.values():
    p.mkdir(parents=True, exist_ok=True)

CAMADAS = [
    ("bacias_todas.gpkg", "eixos", "eixos_propostos"),
    ("bacias_todas.gpkg", "bacias", "bacias_propostas"),
    ("bacias_barragens.gpkg", "bacias", "bacias_barragens"),
    ("aproveitamentos.gpkg", "aneel", "usinas_existentes"),
    ("reservatorios_barragens.gpkg", "reservatorios", "reservatorios_existentes"),
    ("manchas.gpkg", "manchas", "manchas_inundacao"),
    ("perfil_talvegue.gpkg", "estacas", "perfil_estacas"),
    ("perfil_talvegue.gpkg", "traco", "perfil_talvegue"),
]


def carregar(src, layer):
    p = DER / src
    if not p.exists():
        print("[AUSENTE]", p)
        return None
    g = gpd.read_file(p, layer=layer)
    if g.crs is None:
        g = g.set_crs(31982, allow_override=True)
    return g.to_crs(31982)


def nomes_shp(g):
    usados = set()
    ren = {}
    for c in g.columns:
        if c == g.geometry.name:
            continue
        base = "".join(x for x in str(c) if x.isalnum() or x == "_")[:10] or "campo"
        nome = base
        n = 1
        while nome.lower() in usados:
            sufixo = str(n)
            nome = (base[:10-len(sufixo)] + sufixo)[:10]
            n += 1
        usados.add(nome.lower())
        ren[c] = nome
    return g.rename(columns=ren)


def exportar_shp(g, nome):
    out = DIRS["shp"] / f"{nome}.shp"
    nomes_shp(g).to_file(out, driver="ESRI Shapefile", encoding="UTF-8")
    return out


def exportar_kmz(gdf_por_nome, out_kmz):
    ns = "http://www.opengis.net/kml/2.2"
    root = ET.Element(f"{{{ns}}}kml")
    doc = ET.SubElement(root, f"{{{ns}}}Document")
    ET.SubElement(doc, f"{{{ns}}}name").text = out_kmz.stem
    with tempfile.TemporaryDirectory() as td:
        for nome, g in gdf_por_nome.items():
            if g is None or g.empty:
                continue
            kml = Path(td) / f"{nome}.kml"
            g.to_crs(4326).to_file(kml, driver="KML", layer=nome)
            subroot = ET.parse(kml).getroot()
            subdoc = next((x for x in subroot.iter() if x.tag.endswith("Document")), None)
            if subdoc is None:
                continue
            for child in list(subdoc):
                if not child.tag.endswith("name"):
                    doc.append(child)
    kml = out_kmz.with_suffix(".kml")
    ET.ElementTree(root).write(kml, encoding="utf-8", xml_declaration=True)
    with zipfile.ZipFile(out_kmz, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(kml, "doc.kml")
    kml.unlink()


# Preserva os KMZ recebidos dentro da árvore GIS, sem alterar a fonte.
kmz_src = ESP / "kmz"
font_kmz = DIRS["fontes"] / "KMZ_ORIGINAIS"
font_kmz.mkdir(parents=True, exist_ok=True)
if kmz_src.exists():
    for p in kmz_src.glob("*.kmz"):
        copy2(p, font_kmz / p.name)

# Copia os GeoPackages derivados e constrói um único GeoPackage de trabalho.
for p in DER.glob("*.gpkg"):
    copy2(p, DIRS["gpkg"] / p.name)
master = DIRS["gpkg"] / "euroclima_master.gpkg"
if master.exists():
    master.unlink()
camadas = {}
catalogo = []
for src, layer, nome in CAMADAS:
    g = carregar(src, layer)
    if g is None or g.empty:
        continue
    camadas[nome] = g
    modo = "w" if not master.exists() else "a"
    g.to_file(master, layer=nome, driver="GPKG", mode=modo)
    shp = exportar_shp(g, nome)
    catalogo.append({
        "camada": nome,
        "fonte": f"{src}:{layer}",
        "crs": "EPSG:31982",
        "feicoes": int(len(g)),
        "shapefile": str(shp.relative_to(GIS)),
        "gpkg": str(master.relative_to(GIS)),
    })

# Junta perdas observadas do Atlas à malha municipal do corredor. Estas duas
# camadas tornam a base espacial utilizável para a curva preliminar cota–dano.
atlas_csv = RAIZ / "05_MODELAGEM" / "06_resultados" / "tabelas" / "atlas_danos_municipios.csv"
mun_shp = GIS / "shapefiles" / "Municipios_RS.shp"
if atlas_csv.exists() and mun_shp.exists():
    corredor = pd.read_csv(atlas_csv, sep=";", decimal=",", encoding="utf-8")
    mun = gpd.read_file(mun_shp).to_crs(31982)
    mun = mun[mun["NM_MUN"].isin(corredor["Nome_Municipio"].unique())].copy()
    for recorte, nome in (
        ("maio_2024_hidrologico", "danos_municipios_maio24"),
        ("2024_hidrologico", "danos_municipios_2024"),
    ):
        a = corredor[corredor["recorte"] == recorte].drop(columns=["recorte"])
        g = mun.merge(a, left_on="NM_MUN", right_on="Nome_Municipio", how="left")
        g.to_file(master, layer=nome, driver="GPKG", mode="a")
        shp = exportar_shp(g, nome)
        camadas[nome] = g
        catalogo.append({
            "camada": nome,
            "fonte": f"Municipios_RS.shp + atlas_danos_municipios.csv:{recorte}",
            "crs": "EPSG:31982",
            "feicoes": int(len(g)),
            "shapefile": str(shp.relative_to(GIS)),
            "gpkg": str(master.relative_to(GIS)),
        })
else:
    print("[AVISO] Atlas ou malha municipal não encontrado; camadas de danos não geradas")

exportar_kmz(
    {k: camadas.get(k) for k in ("eixos_propostos", "bacias_propostas")},
    DIRS["kmz"] / "alternativas_barragens.kmz",
)
exportar_kmz(
    {k: camadas.get(k) for k in ("manchas_inundacao", "perfil_talvegue", "danos_municipios_2024")},
    DIRS["kmz"] / "risco_e_perfil.kmz",
)
exportar_kmz(
    {k: camadas.get(k) for k in ("usinas_existentes", "reservatorios_existentes")},
    DIRS["kmz"] / "infraestrutura_existente.kmz",
)

(DIRS["catalogo"] / "catalogo_camadas.json").write_text(
    json.dumps(catalogo, ensure_ascii=False, indent=2), encoding="utf-8"
)
(DIRS["catalogo"] / "README.md").write_text(
    """# Organização GIS do Projeto EUROCLIMA+

- `01_FONTES_ORIGINAIS/KMZ_ORIGINAIS`: cópia de preservação dos KMZ recebidos.
- `GIS/shapefiles` e `GIS/raster`: fontes legadas mantidas no lugar para não quebrar scripts.
- `02_GPKG_MESTRE`: GeoPackage consolidado `euroclima_master.gpkg` e cópias dos derivados.
- `03_SHP_ENTREGA`: shapefiles das camadas-chave, em EPSG:31982.
- `04_KMZ_ENTREGA`: temas prontos para Google Earth/QGIS.
- `05_RASTERS_REFERENCIA`: documentação dos rasters; os arquivos grandes permanecem em `GIS/raster`.
- `06_PROJETOS_QGIS`: espaço para projetos QGIS finais.
- `07_SOCIOECONOMICO`: Atlas, IBGE e Ipea para exposição e curva cota–dano.

O GeoPackage é o formato mestre de trabalho. SHP e KMZ são exportações de intercâmbio.
""", encoding="utf-8"
)
(DIRS["raster"] / "README.md").write_text(
    "Os rasters grandes permanecem em GIS/raster para preservar os caminhos dos scripts (mdr.tif e Fdr.tif).\n",
    encoding="utf-8",
)
(DIRS["socio"] / "README.md").write_text(
    """# Base socioeconômica e de danos

- Atlas: `05_MODELAGEM/01_dados/atlas`.
- IBGE: malha definitiva de setores censitários 2022 e agregados de população/domicílios.
- IpeaGEO: contexto socioeconômico e territorial.

A curva preliminar usará exposição IBGE e custo de reposição/estoque calibrável. Valor de mercado só entra quando houver cadastro municipal, transações ou outra fonte espacialmente compatível.
""", encoding="utf-8"
)
print("GeoPackage mestre:", master)
print("Camadas:", len(catalogo))
print(json.dumps(catalogo, ensure_ascii=False, indent=2))
