"""Gera cartografia técnica contextualizada para o relatório público.

Produtos:
* mapas PNG em alta resolução, com norte, escala, municípios, hidrografia e rodovias;
* planta regional das alternativas que irão ao HEC-RAS 1D;
* mapa Leaflet com camadas ativáveis e base de ruas OpenStreetMap.

As geometrias hidrográficas, municipais e rodoviárias são fontes locais do projeto.
O mapa Leaflet usa tiles públicos apenas como base visual; os dados analíticos ficam
embutidos no HTML para que o mapa continue auditável e não dependa de uma API externa.
"""

from __future__ import annotations

import json
import math
import unicodedata
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from pyproj import Transformer
from shapely.geometry import Point
from shapely.ops import unary_union


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "06_resultados" / "VALIDACAO"
GIS = ROOT / "01_dados" / "gis_derivado"
TAB = ROOT / "06_resultados" / "tabelas"
EXTERNAL = Path(
    r"C:\Users\cassi\OneDrive\Documents\SEDEC\PROJETO_EUROCLIMA"
    r"\Documentos EUROCLIMA+\Espanha\GIS\shapefiles"
)
CRS_MAP = "EPSG:31982"
CRS_WGS = "EPSG:4326"
REGIONAL_BBOX = (-52.35, -29.75, -51.20, -28.75)
CORREDOR = [
    "Muçum", "Roca Sales", "Encantado", "Colinas", "Arroio do Meio",
    "Cruzeiro do Sul", "Lajeado", "Estrela", "Bom Retiro do Sul",
    "Fazenda Vilanova", "Taquari", "Venâncio Aires", "Mato Leitão",
    "Santa Clara do Sul", "Marques de Souza", "Travesseiro", "Capitão",
    "Bom Princípio", "Sério",
]
KEY_CITIES = [
    "Muçum", "Roca Sales", "Encantado", "Colinas", "Arroio do Meio",
    "Lajeado", "Estrela", "Bom Retiro do Sul", "Taquari", "Venâncio Aires",
]
MAIN_RIVERS = {
    52627: "Rio Taquari",
    48764: "Rio Forqueta",
    48985: "Rio Guaporé",
    48818: "Rio Fão",
    47923: "Rio Carreiro",
}


def norm(text: object) -> str:
    value = unicodedata.normalize("NFKD", str(text))
    return "".join(c for c in value if not unicodedata.combining(c)).lower()


def read_vector(name: str, bbox=REGIONAL_BBOX, columns=None) -> gpd.GeoDataFrame:
    path = EXTERNAL / f"{name}.shp"
    return gpd.read_file(path, bbox=bbox, columns=columns)


def load_layers() -> dict[str, gpd.GeoDataFrame]:
    municipalities = read_vector("Municipios_RS")
    municipalities = municipalities[municipalities["NM_MUN"].isin(CORREDOR)].copy()
    municipalities = municipalities.to_crs(CRS_MAP)

    hydro = read_vector("geoft_bho_rio")
    hydro = hydro[hydro.geometry.notna()].copy()
    hydro["rio_nome"] = hydro.apply(
        lambda row: MAIN_RIVERS.get(int(row["IDRIO"]), str(row["NORIOCOMP"]).replace("�", "ó")),
        axis=1,
    )
    hydro["principal"] = hydro["IDRIO"].isin(MAIN_RIVERS)
    hydro["nome_mapa"] = hydro["rio_nome"].map(
        lambda x: "Rio Guaporé" if "Guapor" in x else x
    )
    hydro = hydro.to_crs(CRS_MAP)

    state_roads = read_vector("Rodovia_Estadual")
    federal_roads = read_vector("Rodovia_Federal")
    state_roads = state_roads.to_crs(CRS_MAP)
    federal_roads = federal_roads.to_crs(CRS_MAP)
    state_roads["rota"] = state_roads["ROD_CODIGO"].fillna("Rodovia estadual").astype(str)
    federal_roads["rota"] = "BR-" + federal_roads["vl_br"].fillna("").astype(str)

    return {
        "municipios": municipalities,
        "hidrografia": hydro,
        "rodovias_estaduais": state_roads,
        "rodovias_federais": federal_roads,
    }


def point_gdf(rows: list[dict], name: str) -> gpd.GeoDataFrame:
    frame = pd.DataFrame(rows)
    return gpd.GeoDataFrame(
        frame,
        geometry=gpd.points_from_xy(frame["lon"], frame["lat"]),
        crs=CRS_WGS,
    ).to_crs(CRS_MAP)


def load_structures() -> dict[str, gpd.GeoDataFrame]:
    axes = pd.read_csv(ROOT / "01_dados" / "cav" / "eixos_todos.csv", sep=";", decimal=",")
    axes = axes.rename(columns={"lat": "lat", "lon": "lon"})
    axes = axes[["codigo", "lat", "lon", "cota_eixo_m", "area_km2"]].copy()
    axes["tipo"] = "Eixo da carteira E01–E12"
    axes = gpd.GeoDataFrame(
        axes,
        geometry=gpd.points_from_xy(axes["lon"], axes["lat"]),
        crs=CRS_WGS,
    ).to_crs(CRS_MAP)

    existing = pd.read_csv(TAB / "aproveitamentos_existentes.csv", sep=";", decimal=",")
    names = ["Monte Claro", "Castro Alves", "14 de Julho", "Monte Cuco", "Guaporé"]
    existing = existing[existing["nome"].isin(names)].copy()
    existing["tipo"] = "Usina existente"
    existing = gpd.GeoDataFrame(
        existing,
        geometry=gpd.points_from_xy(existing["lon"], existing["lat"]),
        crs=CRS_WGS,
    ).to_crs(CRS_MAP)

    explor = pd.read_csv(TAB / "eixos_exploratorios_propostos.csv", sep=";", decimal=",")
    explor = explor[["codigo", "nome", "lat", "lon", "classe", "status"]].copy()
    explor["tipo"] = "Eixo exploratório"
    explor = gpd.GeoDataFrame(
        explor,
        geometry=gpd.points_from_xy(explor["lon"], explor["lat"]),
        crs=CRS_WGS,
    ).to_crs(CRS_MAP)

    guapore = pd.read_csv(TAB / "eixo_guapore_proposto.csv", sep=";", decimal=",")
    guapore["tipo"] = "Eixo exploratório"
    guapore = gpd.GeoDataFrame(
        guapore,
        geometry=gpd.points_from_xy(guapore["lon"], guapore["lat"]),
        crs=CRS_WGS,
    ).to_crs(CRS_MAP)

    forqueta = pd.read_csv(TAB / "eixos_forqueta_propostos.csv", sep=";", decimal=",")
    forqueta["tipo"] = "Eixo exploratório"
    forqueta = gpd.GeoDataFrame(
        forqueta,
        geometry=gpd.points_from_xy(forqueta["lon"], forqueta["lat"]),
        crs=CRS_WGS,
    ).to_crs(CRS_MAP)

    return {"eixos": axes, "usinas": existing, "exploratorios": explor, "guapore": guapore, "forqueta": forqueta}


def add_north_arrow(ax, x=0.08, y=0.90):
    ax.annotate(
        "N",
        xy=(x, y),
        xytext=(x, y - 0.10),
        xycoords="axes fraction",
        ha="center",
        va="center",
        fontsize=14,
        fontweight="bold",
        arrowprops={"arrowstyle": "-|>", "lw": 1.6, "color": "#263238"},
        zorder=30,
    )


def add_scale_bar(ax, length_km=20, x=0.06, y=0.045):
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    x0 = xmin + (xmax - xmin) * x
    y0 = ymin + (ymax - ymin) * y
    length = length_km * 1000
    ax.plot([x0, x0 + length], [y0, y0], color="#263238", lw=3, zorder=30)
    ax.plot([x0, x0], [y0 - (ymax - ymin) * 0.008, y0 + (ymax - ymin) * 0.008], color="#263238", lw=1.2, zorder=30)
    ax.plot([x0 + length, x0 + length], [y0 - (ymax - ymin) * 0.008, y0 + (ymax - ymin) * 0.008], color="#263238", lw=1.2, zorder=30)
    ax.text(x0 + length / 2, y0 + (ymax - ymin) * 0.014, f"{length_km} km", ha="center", va="bottom", fontsize=9, zorder=30)


def add_map_context(
    ax,
    layers,
    structures,
    labels=True,
    hydro=True,
    roads=True,
    municipality_names=None,
    scale_x=0.78,
    plot_structures=True,
):
    municipalities = layers["municipios"]
    municipalities.boundary.plot(ax=ax, color="#6b7280", linewidth=0.6, alpha=0.75, zorder=4)
    municipalities.plot(ax=ax, facecolor="#eef2f3", edgecolor="none", alpha=0.23, zorder=1)

    if roads:
        layers["rodovias_federais"].plot(ax=ax, color="#d97706", linewidth=1.15, alpha=0.75, zorder=5)
        layers["rodovias_estaduais"].plot(ax=ax, color="#6b7280", linewidth=0.75, alpha=0.55, zorder=5)

    if hydro:
        h = layers["hidrografia"]
        h[~h["principal"]].plot(ax=ax, color="#8bbbd3", linewidth=0.45, alpha=0.60, zorder=6)
        colors = {"Rio Taquari": "#0b5fa5", "Rio Forqueta": "#117a65", "Rio Guaporé": "#7c3aed", "Rio Fão": "#2563eb", "Rio Carreiro": "#2563eb"}
        for name, subset in h[h["principal"]].groupby("nome_mapa"):
            subset.plot(ax=ax, color=colors.get(name, "#0b5fa5"), linewidth=1.45, alpha=0.92, zorder=8)

    if municipality_names is None:
        municipality_names = KEY_CITIES
    for _, row in municipalities[municipalities["NM_MUN"].isin(municipality_names)].iterrows():
        pt = row.geometry.representative_point()
        ax.scatter(pt.x, pt.y, s=8, color="#374151", zorder=15)
        ax.annotate(row["NM_MUN"], (pt.x, pt.y), xytext=(4, 4), textcoords="offset points", fontsize=7.5, color="#1f2937", zorder=16)

    if plot_structures:
        # Eixos da carteira completa, com ALT-J em destaque.
        axes = structures["eixos"]
        selected = axes[axes["codigo"].isin(["E01", "E02", "E04", "E05", "E08", "E12"])]
        other = axes[~axes.index.isin(selected.index)]
        other.plot(ax=ax, color="#9ca3af", markersize=15, alpha=0.55, zorder=17)
        selected.plot(ax=ax, color="#dc2626", markersize=38, edgecolor="white", linewidth=0.55, zorder=18)
        for _, row in selected.iterrows():
            ax.annotate(row["codigo"], (row.geometry.x, row.geometry.y), xytext=(4, 5), textcoords="offset points", fontsize=8, fontweight="bold", color="#991b1b", zorder=19)

        usinas = structures["usinas"]
        usinas.plot(ax=ax, color="#111827", marker="^", markersize=42, edgecolor="white", linewidth=0.55, zorder=20)
        for _, row in usinas.iterrows():
            if row["nome"] in {"Monte Claro", "Castro Alves", "14 de Julho"}:
                ax.annotate(row["nome"], (row.geometry.x, row.geometry.y), xytext=(4, -12), textcoords="offset points", fontsize=7.5, color="#111827", zorder=21)

        explor = pd.concat([structures["exploratorios"], structures["guapore"], structures["forqueta"]], ignore_index=True)
        explor = gpd.GeoDataFrame(explor, geometry="geometry", crs=CRS_MAP)
        explor.plot(ax=ax, color="#f59e0b", marker="D", markersize=34, edgecolor="white", linewidth=0.55, zorder=20)
        for _, row in explor.iterrows():
            ax.annotate(str(row["codigo"]).replace("-PROPOSTO", ""), (row.geometry.x, row.geometry.y), xytext=(4, 4), textcoords="offset points", fontsize=7, color="#92400e", zorder=21)

    add_north_arrow(ax)
    add_scale_bar(ax, length_km=20, x=scale_x)
    ax.set_axis_off()


def add_legend(ax, include_exploratory=True, include_altj=True, include_existing=True):
    handles = [
        Line2D([0], [0], color="#0b5fa5", lw=2, label="Rio Taquari"),
        Line2D([0], [0], color="#117a65", lw=2, label="Rio Forqueta"),
        Line2D([0], [0], color="#7c3aed", lw=2, label="Rio Guaporé"),
        Line2D([0], [0], color="#8bbbd3", lw=1, label="Afluentes BHO"),
        Line2D([0], [0], color="#d97706", lw=2, label="Rodovia federal"),
        Line2D([0], [0], color="#6b7280", lw=1.5, label="Rodovia estadual"),
    ]
    if include_altj:
        handles.append(Line2D([0], [0], marker="o", color="w", markerfacecolor="#dc2626", markersize=8, label="ALT-J: E01/E02/E04/E05/E08/E12"))
    if include_existing:
        handles.append(Line2D([0], [0], marker="^", color="w", markerfacecolor="#111827", markersize=8, label="Usina existente"))
    if include_exploratory:
        handles.append(Line2D([0], [0], marker="D", color="w", markerfacecolor="#f59e0b", markersize=7, label="Eixo exploratório / sensibilidade"))
    ax.legend(handles=handles, loc="lower left", fontsize=8, framealpha=0.94, ncol=1)


def map_extent(gdf, pad=15000):
    xmin, ymin, xmax, ymax = gdf.total_bounds
    return xmin - pad, xmax + pad, ymin - pad, ymax + pad


def save_regional_map(layers, structures):
    base = layers["municipios"]
    fig, ax = plt.subplots(figsize=(14, 9), dpi=320)
    fig.subplots_adjust(left=0.01, right=0.99, bottom=0.085, top=0.86)
    add_map_context(ax, layers, structures, municipality_names=CORREDOR, scale_x=0.78)
    xmin, xmax, ymin, ymax = map_extent(base, 20000)
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    add_legend(ax)
    ax.set_title("Alternativas e rede hidrográfica — visão regional", fontsize=17, fontweight="bold", pad=16)
    fig.text(0.5, 0.935, "Taquari–Antas, Forqueta e Guaporé | eixos que serão verificados no HEC-RAS 1D", ha="center", fontsize=10.5, color="#4b5563")
    fig.text(0.5, 0.018, "Base: BHO/ANA, malha municipal e rodovias do acervo do projeto. Pontos exploratórios não são obras selecionadas.", ha="center", fontsize=8.5, color="#4b5563")
    fig.savefig(OUT / "MAPA_ALTERNATIVAS_HEC_PLANTA.png", facecolor="white")
    plt.close(fig)


def save_forqueta_map(layers, structures):
    f = structures["forqueta"].to_crs(CRS_MAP)
    focus = gpd.GeoDataFrame(pd.concat([layers["municipios"], f], ignore_index=True), crs=CRS_MAP)
    xmin, xmax, ymin, ymax = map_extent(f, 28000)
    fig, ax = plt.subplots(figsize=(13.5, 8.5), dpi=320)
    fig.subplots_adjust(left=0.01, right=0.99, bottom=0.085, top=0.86)
    add_map_context(ax, layers, structures, municipality_names=["Lajeado", "Estrela", "Arroio do Meio", "Roca Sales", "Encantado", "Cruzeiro do Sul"], scale_x=0.78, plot_structures=False)
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    f.plot(ax=ax, color="#f59e0b", marker="D", markersize=58, edgecolor="white", linewidth=0.7, zorder=24)
    for _, row in f.iterrows():
        ax.annotate(row["codigo"].replace("-PROPOSTO", ""), (row.geometry.x, row.geometry.y), xytext=(7, 6), textcoords="offset points", fontsize=10, fontweight="bold", color="#92400e", zorder=25)
    add_legend(ax, include_altj=False, include_existing=False)
    ax.set_title("Eixos exploratórios de retenção no rio Forqueta", fontsize=17, fontweight="bold", pad=16)
    fig.text(0.5, 0.935, "Contribuição lateral antes de Estrela | FQ1 e FQ2 são alternativas mutuamente exclusivas", ha="center", fontsize=10.5, color="#4b5563")
    fig.text(0.5, 0.018, "A rede hidrográfica e as rodovias servem à localização. As manchas e alturas permanecem preliminares.", ha="center", fontsize=8.5, color="#4b5563")
    fig.savefig(OUT / "MAPA_EIXOS_FORQUETA.png", facecolor="white")
    plt.close(fig)


def save_guapore_map(layers, structures):
    g = structures["guapore"]
    xmin, xmax, ymin, ymax = map_extent(g, 30000)
    fig, ax = plt.subplots(figsize=(13.5, 8.5), dpi=320)
    fig.subplots_adjust(left=0.01, right=0.99, bottom=0.085, top=0.86)
    add_map_context(ax, layers, structures, municipality_names=["Encantado", "Roca Sales", "Muçum", "Arroio do Meio", "Lajeado", "Estrela"], scale_x=0.78, plot_structures=False)
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    g.plot(ax=ax, color="#f59e0b", marker="D", markersize=58, edgecolor="white", linewidth=0.7, zorder=24)
    for _, row in g.iterrows():
        ax.annotate(row["codigo"].replace("-PROPOSTO", ""), (row.geometry.x, row.geometry.y), xytext=(7, 6), textcoords="offset points", fontsize=10, fontweight="bold", color="#92400e", zorder=25)
    add_legend(ax, include_altj=False, include_existing=False)
    ax.set_title("Eixo exploratório GU1 e rede do rio Guaporé", fontsize=17, fontweight="bold", pad=16)
    fig.text(0.5, 0.935, "Hipótese estrutural a montante do ponto de análise | contribuição independente a separar do Antas", ha="center", fontsize=10.5, color="#4b5563")
    fig.text(0.5, 0.018, "A posição de GU1 é de triagem e deve ser confirmada com geometria, CAV, remanso, energia e segurança.", ha="center", fontsize=8.5, color="#4b5563")
    fig.savefig(OUT / "MAPA_EIXO_GUAPORE_TRIAGEM.png", facecolor="white")
    plt.close(fig)


def raster_bounds_wgs(path: Path):
    with rasterio.open(path) as src:
        bounds = src.bounds
        transformer = Transformer.from_crs(src.crs, CRS_WGS, always_xy=True)
        corners = [
            transformer.transform(bounds.left, bounds.bottom),
            transformer.transform(bounds.right, bounds.top),
        ]
    return min(p[0] for p in corners), min(p[1] for p in corners), max(p[0] for p in corners), max(p[1] for p in corners)


def save_hand_maps(layers, structures):
    natural_path = GIS / "mancha_sem_barragem_ALTJ_seca.tif"
    altj_path = GIS / "mancha_ALTJ_seca_triagem_ALTJ_seca.tif"
    with rasterio.open(natural_path) as src:
        natural = src.read(1).astype(float)
        bounds = src.bounds
        extent = [bounds.left, bounds.right, bounds.bottom, bounds.top]
    with rasterio.open(altj_path) as src:
        altj = src.read(1).astype(float)
    natural[natural <= 0] = np.nan
    altj[altj <= 0] = np.nan
    vmax = np.nanpercentile(np.concatenate([natural[np.isfinite(natural)], altj[np.isfinite(altj)]]), 99)
    vmax = max(1.0, float(np.ceil(vmax)))
    bbox = raster_bounds_wgs(natural_path)
    to_map = Transformer.from_crs(CRS_WGS, CRS_MAP, always_xy=True)
    x0, y0 = to_map.transform(bbox[0] - 0.04, bbox[1] - 0.04)
    x1, y1 = to_map.transform(bbox[2] + 0.04, bbox[3] + 0.04)
    local_layers = {k: v.cx[x0:x1, y0:y1] if k != "municipios" else v for k, v in layers.items()}

    fig, axes = plt.subplots(1, 2, figsize=(16, 9), dpi=320, constrained_layout=True)
    for ax, arr, title in [(axes[0], natural, "Sem novas barragens"), (axes[1], altj, "ALT-J seca — Qp residual = 6.213 m³/s")]:
        ax.imshow(arr, extent=extent, origin="upper", cmap="YlOrRd", vmin=0, vmax=vmax, zorder=1)
        add_map_context(ax, local_layers, structures, municipality_names=["Roca Sales", "Arroio do Meio", "Estrela", "Lajeado", "Encantado", "Colinas"], scale_x=0.06)
        ax.set_xlim(bounds.left, bounds.right)
        ax.set_ylim(bounds.bottom, bounds.top)
        ax.set_title(title, fontsize=13, fontweight="bold")
    sm = plt.cm.ScalarMappable(cmap="YlOrRd", norm=plt.Normalize(vmin=0, vmax=vmax))
    sm.set_array([])
    cb = fig.colorbar(sm, ax=axes, shrink=0.72, pad=0.02)
    cb.set_label("Profundidade HAND estimada (m)")
    fig.suptitle("Triagem espacial de inundação — comparação sem obra e com ALT-J", fontsize=16, fontweight="bold")
    fig.text(0.5, 0.005, "HAND + curva de vazão de triagem; não é mancha hidráulica HEC-RAS. Norte e escala são comuns aos dois painéis.", ha="center", fontsize=8.5, color="#4b5563")
    fig.savefig(OUT / "MAPA_HAND_SEM_VS_ALTJ.png", bbox_inches="tight", facecolor="white")
    plt.close(fig)

    with rasterio.open(GIS / "mancha_diferenca_ALTJ_seca.tif") as src:
        diff = src.read(1)
        bounds_diff = src.bounds
    fig, ax = plt.subplots(figsize=(12, 9), dpi=320, constrained_layout=True)
    masked = np.ma.masked_where(diff < 1, diff)
    cmap_diff = plt.matplotlib.colors.ListedColormap(["#2ca25f", "#fdae6b"])
    ax.imshow(masked, extent=[bounds_diff.left, bounds_diff.right, bounds_diff.bottom, bounds_diff.top], origin="upper", cmap=cmap_diff, vmin=1, vmax=2, zorder=1)
    add_map_context(ax, local_layers, structures, municipality_names=["Roca Sales", "Arroio do Meio", "Estrela", "Lajeado", "Encantado", "Colinas"], scale_x=0.06)
    ax.set_xlim(bounds_diff.left, bounds_diff.right)
    ax.set_ylim(bounds_diff.bottom, bounds_diff.top)
    ax.set_title("Diferença espacial da mancha HAND — ALT-J", fontsize=16, fontweight="bold")
    ax.legend(handles=[Patch(facecolor="#2ca25f", label="Área retirada na triagem"), Patch(facecolor="#fdae6b", label="Área ainda inundável")], loc="lower left", fontsize=9, framealpha=0.94)
    fig.text(0.5, 0.012, "A retirada espacial não equivale diretamente à redução de dano; profundidade, duração, pontes, remanso e diques exigem HEC-RAS 1D.", ha="center", fontsize=8.5, color="#4b5563")
    fig.savefig(OUT / "MAPA_HAND_DIFERENCA_ALTJ.png", bbox_inches="tight", facecolor="white")
    plt.close(fig)

    tabela = pd.read_csv(TAB / "manchas_por_municipio_ALTJ_seca.csv", sep=";", decimal=",").sort_values("reducao_km2", ascending=True)
    fig, ax = plt.subplots(figsize=(10.5, 8.5), dpi=320, constrained_layout=True)
    ax.barh(tabela["municipio"], tabela["reducao_km2"], color="#2563a6")
    for y, (_, row) in enumerate(tabela.iterrows()):
        ax.text(row["reducao_km2"] + 0.08, y, f"{row['reducao_pct']:.1f}%", va="center", fontsize=8)
    ax.set_xlabel("Redução de área inundável na triagem (km²)")
    ax.set_ylabel("Município")
    ax.set_title("Efeito preliminar da ALT-J nas manchas HAND por município", fontsize=15, fontweight="bold")
    ax.grid(axis="x", alpha=0.25)
    fig.text(0.5, 0.005, "Fonte: tabela municipal da triagem HAND; percentuais não são redução final de danos.", ha="center", fontsize=8.5, color="#4b5563")
    fig.savefig(OUT / "REDUCAO_MANCHA_HAND_ALTJ_MUNICIPIOS.png", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def geojson(gdf: gpd.GeoDataFrame, properties: list[str], simplify: float = 0.0002) -> dict:
    data = gdf.to_crs(CRS_WGS).copy()
    if simplify:
        data["geometry"] = data.geometry.simplify(simplify, preserve_topology=True)
    keep = [c for c in properties if c in data.columns] + ["geometry"]
    data = data[keep]
    return json.loads(data.to_json(drop_id=True, na="drop"))


def save_leaflet(layers, structures):
    municipalities = layers["municipios"].copy()
    municipalities["rotulo"] = municipalities["NM_MUN"]
    hydro = layers["hidrografia"].copy()
    hydro["nome"] = hydro["nome_mapa"]
    hydro["classe"] = np.where(hydro["principal"], "rio principal", "afluente")
    state = layers["rodovias_estaduais"].copy()
    federal = layers["rodovias_federais"].copy()
    axes = structures["eixos"].copy()
    axes["grupo"] = np.where(axes["codigo"].isin(["E01", "E02", "E04", "E05", "E08", "E12"]), "ALT-J", "Carteira E01–E12")
    axes["descricao"] = axes["codigo"] + " — eixo de triagem"
    dams = structures["usinas"].copy()
    dams["descricao"] = dams["nome"] + " — usina existente"
    explor = pd.concat([structures["exploratorios"], structures["guapore"], structures["forqueta"]], ignore_index=True)
    explor = gpd.GeoDataFrame(explor, geometry="geometry", crs=CRS_MAP)
    explor["descricao"] = explor["codigo"] + " — exploratório/sensibilidade"

    # Pontos representativos de municípios para rótulos persistentes.
    city = municipalities.copy()
    city["geometry"] = city.geometry.representative_point()
    city["cidade"] = city["NM_MUN"]

    payload = {
        "municipios": geojson(municipalities, ["NM_MUN", "CD_MUN", "rotulo"], 0.00015),
        "cidades": geojson(city, ["cidade"], 0),
        "hidrografia": geojson(hydro, ["nome", "classe"], 0.00015),
        "rodovias_estaduais": geojson(state, ["rota"], 0.00008),
        "rodovias_federais": geojson(federal, ["rota"], 0.00008),
        "eixos": geojson(axes, ["codigo", "grupo", "descricao", "cota_eixo_m", "area_km2"], 0),
        "usinas": geojson(dams, ["nome", "descricao", "potencia_kW"], 0),
        "exploratorios": geojson(explor, ["codigo", "nome", "descricao", "classe", "status"], 0),
    }
    text_payload = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    html = f'''<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Mapa interativo — alternativas HEC-RAS 1D</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" crossorigin="">
  <style>
    html, body {{ margin:0; padding:0; font-family: Arial, sans-serif; background:#f7f8fa; color:#1f2937; }}
    .wrap {{ max-width: 1400px; margin: 0 auto; padding: 18px; }}
    h1 {{ margin:0 0 4px; font-size: 24px; }}
    p {{ margin: 0 0 12px; color:#4b5563; }}
    #map {{ height: 760px; min-height: 520px; border:1px solid #d1d5db; }}
    .north {{ background:rgba(255,255,255,.9); padding:7px 8px; font-weight:bold; font-size:20px; border:1px solid #9ca3af; line-height:1; }}
    .legend {{ background:rgba(255,255,255,.95); padding:8px 10px; line-height:1.45; border:1px solid #d1d5db; font-size:12px; }}
    .swatch {{ display:inline-block; width:20px; border-top:3px solid; margin-right:5px; vertical-align:middle; }}
    .dot {{ display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:5px; vertical-align:middle; }}
    .source {{ font-size: 12px; margin-top: 8px; }}
  </style>
</head>
<body>
<div class="wrap">
  <h1>Alternativas e rede hidrográfica — planta interativa</h1>
  <p>Camadas para conferir a posição dos eixos ALT-J, GU1, Forqueta, usinas existentes, municípios, rios e rodovias antes da modelagem HEC-RAS 1D.</p>
  <div id="map" aria-label="Mapa interativo de alternativas de barragens no Taquari–Antas"></div>
  <p class="source">Fontes locais: BHO/ANA, malha municipal e rodovias do acervo do projeto. A base OSM é apenas cartográfica e pode depender de conexão com a internet. Pontos exploratórios não são obras selecionadas.</p>
</div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
<script>
const DATA = {text_payload};
const map = L.map('map', {{ zoomControl: true }}).setView([-29.27, -51.75], 9);
L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{ maxZoom: 18, attribution: '&copy; OpenStreetMap contributors' }}).addTo(map);
const styles = {{
  municipalities: {{ color:'#6b7280', weight:1, fillColor:'#e5e7eb', fillOpacity:.16 }},
  hydro: f => f.properties.classe === 'rio principal' ? {{ color: f.properties.nome === 'Rio Forqueta' ? '#117a65' : (f.properties.nome === 'Rio Guaporé' ? '#7c3aed' : '#0b5fa5'), weight:2.8, opacity:.92 }} : {{ color:'#8bbbd3', weight:.8, opacity:.65 }},
  state: {{ color:'#6b7280', weight:1.2, opacity:.58 }},
  federal: {{ color:'#d97706', weight:1.8, opacity:.75 }},
  altj: {{ radius:7, color:'#991b1b', fillColor:'#dc2626', fillOpacity:.92, weight:1 }},
  other: {{ radius:5, color:'#6b7280', fillColor:'#9ca3af', fillOpacity:.72, weight:1 }},
  dam: {{ radius:8, color:'#111827', fillColor:'#111827', fillOpacity:.95, weight:1 }},
  exploratory: {{ radius:7, color:'#92400e', fillColor:'#f59e0b', fillOpacity:.94, weight:1 }}
}};
function lineLayer(data, style, tooltip) {{ return L.geoJSON(data, {{ style, onEachFeature:(f,l)=>l.bindTooltip(tooltip(f)) }}); }}
const mun = L.geoJSON(DATA.municipios, {{ style:styles.municipalities, onEachFeature:(f,l)=>l.bindPopup('<b>'+f.properties.NM_MUN+'</b><br>Município do corredor de estudo') }}).addTo(map);
const city = L.geoJSON(DATA.cidades, {{ pointToLayer:(f,latlng)=>L.marker(latlng, {{ icon:L.divIcon({{ className:'city-label', html:'<span style="font-size:12px;font-weight:600;color:#1f2937;text-shadow:0 0 3px white,0 0 3px white;">'+f.properties.cidade+'</span>', iconAnchor:[0,0] }}) }}), onEachFeature:(f,l)=>l.bindTooltip(f.properties.cidade) }}).addTo(map);
const hydro = lineLayer(DATA.hidrografia, styles.hydro, f => f.properties.nome || 'Afluente BHO').addTo(map);
const roadsState = lineLayer(DATA.rodovias_estaduais, styles.state, f => f.properties.rota || 'Rodovia estadual');
const roadsFederal = lineLayer(DATA.rodovias_federais, styles.federal, f => f.properties.rota || 'Rodovia federal');
const axes = L.geoJSON(DATA.eixos, {{ pointToLayer:(f,ll)=>L.circleMarker(ll, f.properties.grupo === 'ALT-J' ? styles.altj : styles.other), onEachFeature:(f,l)=>l.bindPopup('<b>'+f.properties.codigo+'</b><br>'+f.properties.grupo+'<br>Cota de eixo: '+(f.properties.cota_eixo_m ?? 'n/d')+' m') }}).addTo(map);
const dams = L.geoJSON(DATA.usinas, {{ pointToLayer:(f,ll)=>L.circleMarker(ll,styles.dam), onEachFeature:(f,l)=>l.bindPopup('<b>'+f.properties.nome+'</b><br>Usina existente<br>Potência: '+(f.properties.potencia_kW ?? 'n/d')+' kW') }}).addTo(map);
const exploratory = L.geoJSON(DATA.exploratorios, {{ pointToLayer:(f,ll)=>L.circleMarker(ll,styles.exploratory), onEachFeature:(f,l)=>l.bindPopup('<b>'+f.properties.codigo+'</b><br>'+ (f.properties.nome || '') +'<br>'+ (f.properties.classe || 'Eixo exploratório') +'<br><i>Não selecionado; ponto de triagem/sensibilidade.</i>') }}).addTo(map);
const north = L.control({{position:'topright'}}); north.onAdd=()=>{{ const d=L.DomUtil.create('div','north'); d.innerHTML='↑<br><span style="font-size:12px">N</span>'; return d; }}; north.addTo(map);
const legend = L.control({{position:'bottomleft'}}); legend.onAdd=()=>{{ const d=L.DomUtil.create('div','legend'); d.innerHTML='<b>Legenda</b><br><span class="swatch" style="border-color:#0b5fa5"></span>Rio Taquari / rede principal<br><span class="swatch" style="border-color:#117a65"></span>Rio Forqueta<br><span class="swatch" style="border-color:#7c3aed"></span>Rio Guaporé<br><span class="swatch" style="border-color:#8bbbd3"></span>Afluentes BHO<br><span class="dot" style="background:#dc2626"></span>ALT-J<br><span class="dot" style="background:#111827"></span>Usina existente<br><span class="dot" style="background:#f59e0b"></span>Exploratório/sensibilidade'; return d; }}; legend.addTo(map);
L.control.layers(null, {{ 'Municípios':mun, 'Rótulos das cidades':city, 'Hidrografia BHO':hydro, 'Rodovias estaduais':roadsState, 'Rodovias federais':roadsFederal, 'Eixos E01–E12':axes, 'Usinas existentes':dams, 'Exploratórios GU1/FQ/FQ2/MC2':exploratory }}, {{collapsed:false}}).addTo(map);
const all = L.featureGroup([mun, hydro, axes, dams, exploratory]); map.fitBounds(all.getBounds().pad(.04));
</script>
</body>
</html>'''
    (ROOT / "06_resultados" / "GIS").mkdir(parents=True, exist_ok=True)
    (ROOT / "06_resultados" / "GIS" / "mapa_interativo_alternativas.html").write_text(html, encoding="utf-8")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    layers = load_layers()
    structures = load_structures()
    save_regional_map(layers, structures)
    save_forqueta_map(layers, structures)
    save_guapore_map(layers, structures)
    save_hand_maps(layers, structures)
    save_leaflet(layers, structures)
    print("Cartografia atualizada:")
    for p in [
        OUT / "MAPA_ALTERNATIVAS_HEC_PLANTA.png",
        OUT / "MAPA_EIXOS_FORQUETA.png",
        OUT / "MAPA_EIXO_GUAPORE_TRIAGEM.png",
        OUT / "MAPA_HAND_SEM_VS_ALTJ.png",
        OUT / "MAPA_HAND_DIFERENCA_ALTJ.png",
        OUT / "REDUCAO_MANCHA_HAND_ALTJ_MUNICIPIOS.png",
        ROOT / "06_resultados" / "GIS" / "mapa_interativo_alternativas.html",
    ]:
        print(p)


if __name__ == "__main__":
    main()
