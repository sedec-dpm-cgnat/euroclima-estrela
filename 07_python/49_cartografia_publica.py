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
    "Bom Princípio", "Sério", "Guaporé",
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
    city_offsets=None,
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
    city_offsets = city_offsets or {}
    for _, row in municipalities[municipalities["NM_MUN"].isin(municipality_names)].iterrows():
        pt = row.geometry.representative_point()
        ax.scatter(pt.x, pt.y, s=8, color="#374151", zorder=15)
        ax.annotate(
            row["NM_MUN"],
            (pt.x, pt.y),
            xytext=city_offsets.get(row["NM_MUN"], (4, 4)),
            textcoords="offset points",
            fontsize=7.5,
            color="#1f2937",
            zorder=16,
        )

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
    add_map_context(ax, layers, structures, municipality_names=KEY_CITIES + ["Guaporé"], scale_x=0.78)
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


def save_tr_start_map(layers, structures):
    """Planta esquemática, limpa e numerada do conjunto inicial do TR."""
    base = layers["municipios"]
    extent_objects = gpd.GeoDataFrame(
        pd.concat(
            [
                base,
                structures["eixos"][structures["eixos"]["codigo"].isin(["E02", "E04", "E08", "E12"])],
                structures["guapore"],
                structures["forqueta"],
            ],
            ignore_index=True,
        ),
        geometry="geometry",
        crs=CRS_MAP,
    )
    fig = plt.figure(figsize=(17, 9.5), dpi=320)
    gs = fig.add_gridspec(1, 2, width_ratios=[4.65, 1.35], wspace=0.02)
    ax = fig.add_subplot(gs[0])
    info = fig.add_subplot(gs[1])
    fig.subplots_adjust(left=0.015, right=0.985, bottom=0.08, top=0.85)

    city_offsets = {
        "Muçum": (-28, 4),
        "Roca Sales": (5, 5),
        "Encantado": (5, -14),
        "Arroio do Meio": (5, 4),
        "Lajeado": (5, -14),
        "Estrela": (5, 5),
        "Bom Retiro do Sul": (5, -14),
        "Taquari": (5, 5),
        "Guaporé": (5, -14),
    }
    add_map_context(
        ax,
        layers,
        structures,
        municipality_names=KEY_CITIES + ["Guaporé"],
        scale_x=0.05,
        plot_structures=False,
        city_offsets=city_offsets,
    )
    xmin, xmax, ymin, ymax = map_extent(extent_objects, 19000)
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.set_aspect("equal")

    # Identificadores curtos no mapa; a composição completa fica no painel lateral.
    colors = {"E02": "#00897b", "E04": "#00897b", "E08": "#2563eb", "E12": "#d97706"}
    marker_labels = {"E02": "1a", "E04": "1b", "E08": "2", "E12": "3"}
    main = structures["eixos"][structures["eixos"]["codigo"].isin(colors)].copy()
    for _, row in main.iterrows():
        color = colors[row["codigo"]]
        ax.scatter(row.geometry.x, row.geometry.y, s=180, color=color, edgecolor="white", linewidth=1.0, zorder=24)
        ax.annotate(
            marker_labels[row["codigo"]],
            (row.geometry.x, row.geometry.y),
            ha="center",
            va="center",
            fontsize=8.5,
            fontweight="bold",
            color="white",
            zorder=25,
        )

    lateral = pd.concat(
        [
            structures["guapore"].assign(hec="4"),
            structures["forqueta"][structures["forqueta"]["codigo"].isin(["FQ2-PROPOSTO", "FQ1-PROPOSTO"])].assign(
                hec=structures["forqueta"][structures["forqueta"]["codigo"].isin(["FQ2-PROPOSTO", "FQ1-PROPOSTO"])]
                ["codigo"].map({"FQ2-PROPOSTO": "5", "FQ1-PROPOSTO": "6"})
            ),
        ],
        ignore_index=True,
    )
    lateral = gpd.GeoDataFrame(lateral, geometry="geometry", crs=CRS_MAP)
    lateral_colors = {"GU1-PROPOSTO": "#7c3aed", "FQ2-PROPOSTO": "#db2777", "FQ1-PROPOSTO": "#b45309"}
    for _, row in lateral.iterrows():
        color = lateral_colors[row["codigo"]]
        ax.scatter(row.geometry.x, row.geometry.y, s=190, color=color, marker="D", edgecolor="white", linewidth=1.0, zorder=25)
        ax.annotate(row["hec"], (row.geometry.x, row.geometry.y), ha="center", va="center", fontsize=8.5, fontweight="bold", color="white", zorder=26)

    existing = structures["usinas"][structures["usinas"]["nome"].isin(["Monte Claro", "Castro Alves", "14 de Julho"])].copy()
    existing_offsets = {"Monte Claro": (7, -16), "Castro Alves": (7, 5), "14 de Julho": (7, 5)}
    for _, row in existing.iterrows():
        ax.scatter(row.geometry.x, row.geometry.y, s=100, color="#111827", marker="^", edgecolor="white", linewidth=0.9, zorder=27)
        ax.annotate(row["nome"], (row.geometry.x, row.geometry.y), xytext=existing_offsets.get(row["nome"], (6, -14)), textcoords="offset points", fontsize=8.2, color="#111827", zorder=28)

    # Rótulos dos três rios principais são derivados da própria geometria BHO.
    principal = layers["hidrografia"][layers["hidrografia"]["principal"]]
    river_colors = {"Rio Taquari": "#0b5fa5", "Rio Forqueta": "#117a65", "Rio Guaporé": "#7c3aed"}
    for name, subset in principal.groupby("nome_mapa"):
        if name not in river_colors:
            continue
        pt = subset.geometry.unary_union.representative_point()
        ax.annotate(name, (pt.x, pt.y), xytext=(5, 0), textcoords="offset points", fontsize=8.5, fontstyle="italic", color=river_colors[name], zorder=12)

    ax.set_title("Alternativas de partida para o Termo de Referência — planta esquemática", fontsize=16.5, fontweight="bold", pad=13)
    fig.text(0.34, 0.925, "As marcações numeradas correspondem aos grupos que podem ser ativados no mapa dinâmico", ha="center", fontsize=10.5, color="#4b5563")

    info.axis("off")
    info.set_xlim(0, 1)
    info.set_ylim(0, 1)
    info.text(0.02, 0.97, "LEITURA DO MAPA", fontsize=12, fontweight="bold", color="#1f2937", va="top")
    info.text(0.02, 0.925, "Casos finais de partida", fontsize=9, color="#4b5563", va="top")
    blocks = [
        (0.84, "1 · HEC-01", "E02 + E04\narranjo-base", "#00897b"),
        (0.72, "2 · HEC-02", "E02 + E04 + E08\nganho incremental", "#2563eb"),
        (0.60, "3 · HEC-03", "E02 + E04 + E12\ncobertura terminal", "#d97706"),
        (0.48, "4 · HEC-04", "ALT-J + GU1\nramo do Guaporé", "#7c3aed"),
        (0.36, "5 · HEC-05", "ALT-J + FQ2\nramo do Forqueta", "#db2777"),
        (0.24, "6 · HEC-06", "ALT-J + FQ1 / comportas\nsensibilidade operacional", "#b45309"),
    ]
    for y, title, desc, color in blocks:
        info.scatter(0.045, y + 0.005, s=85, color=color, edgecolor="white", linewidth=0.7, zorder=2)
        info.text(0.105, y + 0.022, title, fontsize=9.5, fontweight="bold", color=color, va="top")
        info.text(0.105, y - 0.012, desc, fontsize=8.4, color="#374151", va="top", linespacing=1.25)
    info.text(0.02, 0.125, "Referências", fontsize=9.5, fontweight="bold", color="#1f2937", va="top")
    info.text(0.02, 0.095, "▲ usina existente / restrição\n● eixo principal   ◆ contribuição lateral", fontsize=8.2, color="#374151", va="top", linespacing=1.35)
    info.text(0.02, 0.035, "HEC-00: referência sem novos eixos.", fontsize=8.0, color="#6b7280", va="top")
    fig.text(0.34, 0.018, "Base: BHO/ANA, malha municipal e rodovias do acervo. Para ruas e seleção individual de alternativas, consulte o mapa Leaflet.", ha="center", fontsize=8.3, color="#4b5563")
    fig.savefig(OUT / "MAPA_ALTERNATIVAS_PONTO_PARTIDA_TR.png", facecolor="white")
    plt.close(fig)


def _profile_projection(profile, latitudes, longitudes):
    xy = profile[["x_utm", "y_utm"]].to_numpy(float)
    points = gpd.GeoDataFrame(
        geometry=gpd.points_from_xy(longitudes, latitudes),
        crs=CRS_WGS,
    ).to_crs(CRS_MAP)
    arr = np.column_stack([points.geometry.x, points.geometry.y])
    d2 = ((arr[:, None, :] - xy[None, :, :]) ** 2).sum(axis=2)
    idx = d2.argmin(axis=1)
    nearest = profile.iloc[idx].reset_index(drop=True)
    return nearest["dist_km"].to_numpy(float), nearest["cota_m"].to_numpy(float)


def save_tr_start_profile(structures):
    """Perfil longitudinal focado na cascata e na ordem da matriz HEC."""
    profile = pd.read_csv(ROOT / "06_resultados" / "CLAUDE" / "claude_perfil_principal.csv", sep=";", decimal=",")
    profile = profile.sort_values("dist_km").reset_index(drop=True)
    selected_codes = ["E02", "E04", "E08", "E12"]
    axes = structures["eixos"][structures["eixos"]["codigo"].isin(selected_codes)].copy().reset_index(drop=True)
    axes["dist_km"], axes["cota_perfil_m"] = _profile_projection(profile, axes["lat"], axes["lon"])
    revised = pd.read_csv(ROOT / "06_resultados" / "CLAUDE" / "claude_altura_admissivel_revisada.csv", sep=";", decimal=",")
    axes = axes.merge(revised[["eixo", "altura_max_m"]], left_on="codigo", right_on="eixo", how="left")
    axes["cota_topo_triagem_m"] = axes["cota_eixo_m"] + axes["altura_max_m"]

    existing = structures["usinas"][structures["usinas"]["nome"].isin(["Monte Claro", "Castro Alves", "14 de Julho"])].copy().reset_index(drop=True)
    existing["dist_km"], existing["cota_perfil_m"] = _profile_projection(profile, existing["lat"], existing["lon"])
    existing["cota_inventario_m"] = pd.to_numeric(existing["cota_terreno_m"], errors="coerce").fillna(existing["cota_perfil_m"])

    focus = profile[(profile["dist_km"] >= 225) & (profile["dist_km"] <= 390)]
    fig = plt.figure(figsize=(16, 11), dpi=300)
    gs = fig.add_gridspec(2, 1, height_ratios=[3.9, 1.35], hspace=0.16)
    ax = fig.add_subplot(gs[0])
    ax.fill_between(focus["dist_km"], focus["cota_m"], 0, color="#eadfcd", alpha=0.9)
    ax.plot(focus["dist_km"], focus["cota_m"], color="#5b4a34", lw=2.2, label="talvegue / perfil do MDE")

    for _, row in existing.iterrows():
        ax.vlines(row["dist_km"], row["cota_perfil_m"], row["cota_inventario_m"], color="#475569", lw=3.2, alpha=0.9)
        ax.scatter(row["dist_km"], row["cota_inventario_m"], marker="^", s=70, color="#111827", edgecolor="white", linewidth=0.7, zorder=8)
        ax.annotate(row["nome"], (row["dist_km"], row["cota_inventario_m"]), xytext=(0, 8), textcoords="offset points", ha="center", va="bottom", rotation=90, fontsize=8.5, color="#334155")

    colors = {"E02": "#00897b", "E04": "#00897b", "E08": "#2563eb", "E12": "#d97706"}
    case = {"E02": "HEC-01", "E04": "HEC-01", "E08": "HEC-02", "E12": "HEC-03"}
    for _, row in axes.sort_values("dist_km").iterrows():
        color = colors[row["codigo"]]
        ax.vlines(row["dist_km"], row["cota_perfil_m"], row["cota_topo_triagem_m"], color=color, lw=5, alpha=0.76, zorder=7)
        ax.scatter(row["dist_km"], row["cota_eixo_m"], marker="o", s=45, color=color, edgecolor="white", linewidth=0.7, zorder=9)
        ax.scatter(row["dist_km"], row["cota_topo_triagem_m"], marker="D", s=55, color=color, edgecolor="white", linewidth=0.7, zorder=9)
        ax.annotate(
            f"{row['codigo']} · {case[row['codigo']]}\naltura máx. triagem = {row['altura_max_m']:.1f} m",
            (row["dist_km"], row["cota_topo_triagem_m"]),
            xytext=(0, 8),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8.5,
            color=color,
            fontweight="bold",
        )

    legend = [
        Line2D([0], [0], color="#5b4a34", lw=2.2, label="Talvegue / perfil do MDE"),
        Line2D([0], [0], color="#475569", lw=3, marker="^", markerfacecolor="#111827", markeredgecolor="white", label="Usina existente / restrição"),
        Line2D([0], [0], color="#00897b", lw=4, marker="D", markerfacecolor="#00897b", markeredgecolor="white", label="E02 + E04 — HEC-01"),
        Line2D([0], [0], color="#2563eb", lw=4, marker="D", markerfacecolor="#2563eb", markeredgecolor="white", label="E08 — extensão HEC-02"),
        Line2D([0], [0], color="#d97706", lw=4, marker="D", markerfacecolor="#d97706", markeredgecolor="white", label="E12 — extensão HEC-03"),
    ]
    ax.legend(handles=legend, loc="upper right", fontsize=9, framealpha=0.95)
    ax.set_xlim(225, 390)
    ax.set_ylim(0, 455)
    ax.grid(axis="y", color="#d6d3d1", lw=0.7)
    ax.set_xlabel("Distância ao longo do perfil principal (km), montante → jusante")
    ax.set_ylabel("Cota (m)")
    ax.set_title("Conjunto inicial de alternativas para o Termo de Referência — perfil", fontsize=17, fontweight="bold", pad=14)

    tab = fig.add_subplot(gs[1])
    tab.axis("off")
    rows = [
        ["1", "HEC-00 / REF", "situação atual", "calibração do modelo e curva cota–dano"],
        ["2", "HEC-01", "E02 + E04", "1º arranjo com obra no eixo principal"],
        ["3", "HEC-02", "E02 + E04 + E08", "ganho incremental; verificar cascata"],
        ["4", "HEC-03", "E02 + E04 + E12", "cobertura terminal; verificar 14 de Julho"],
        ["5", "HEC-04", "ALT-J + GU1", "ramo lateral independente do Guaporé"],
        ["6", "HEC-05 / HEC-06", "Forqueta FQ2; FQ1/comportas", "sensibilidades laterais e operação"],
    ]
    table = tab.table(cellText=rows, colLabels=["Ordem", "Plano", "Composição", "Por que entra no TR"], loc="center", cellLoc="left", colLoc="center", colWidths=[0.07, 0.19, 0.28, 0.46], bbox=[0.015, 0.03, 0.97, 0.92])
    table.auto_set_font_size(False)
    table.set_fontsize(8.6)
    table.scale(1, 1.4)
    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_facecolor("#3f536b")
            cell.set_text_props(color="white", weight="bold")
        elif row % 2 == 0:
            cell.set_facecolor("#f1f4f7")
    tab.set_title("Sequência de partida — GU1 e Forqueta entram como afluências laterais e não aparecem como eixos no perfil principal", fontsize=10, pad=5)
    fig.text(0.5, 0.012, "A definição final depende do HEC-RAS 1D calibrado, topobatimetria, operação, remanso, segurança, impactos e análise custo-benefício.", ha="center", fontsize=8.5, color="#4b5563")
    fig.savefig(OUT / "PERFIL_ALTERNATIVAS_PONTO_PARTIDA_TR.png", bbox_inches="tight", facecolor="white")
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
    city = municipalities[municipalities["NM_MUN"].isin(KEY_CITIES + ["Guaporé"])].copy()
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
    html = '''<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Mapa interativo — alternativas finais HEC-RAS 1D</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" crossorigin="">
  <style>
    html, body { margin:0; padding:0; font-family: Arial, sans-serif; background:#f7f8fa; color:#1f2937; }
    .wrap { max-width: 1450px; margin: 0 auto; padding: 18px; }
    h1 { margin:0 0 4px; font-size: 24px; }
    p { margin: 0 0 12px; color:#4b5563; }
    #map { height: 760px; min-height: 520px; border:1px solid #d1d5db; }
    .north { background:rgba(255,255,255,.93); padding:7px 8px; font-weight:bold; font-size:20px; border:1px solid #9ca3af; line-height:1; text-align:center; }
    .legend { background:rgba(255,255,255,.95); padding:8px 10px; line-height:1.45; border:1px solid #d1d5db; font-size:12px; }
    .swatch { display:inline-block; width:20px; border-top:3px solid; margin-right:5px; vertical-align:middle; }
    .dot { display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:5px; vertical-align:middle; }
    .alt-control { background:rgba(255,255,255,.97); padding:10px 12px; line-height:1.25; border:1px solid #9ca3af; width:275px; max-height:500px; overflow:auto; box-shadow:0 1px 4px rgba(0,0,0,.18); }
    .alt-title { font-weight:bold; font-size:14px; margin-bottom:3px; }
    .alt-help { color:#4b5563; font-size:11px; margin-bottom:8px; }
    .alt-row { display:flex; align-items:flex-start; gap:7px; padding:5px 0; border-top:1px solid #e5e7eb; }
    .alt-row input { margin-top:2px; accent-color:#2563eb; }
    .alt-mark { flex:0 0 11px; width:11px; height:11px; border-radius:50%; margin-top:3px; border:1px solid rgba(0,0,0,.25); }
    .alt-text { font-size:12px; }
    .alt-text strong { display:block; }
    .alt-text span { color:#4b5563; font-size:11px; }
    .alt-detail { background:#f3f4f6; border-top:1px solid #d1d5db; margin:7px -12px -10px; padding:7px 12px; color:#374151; font-size:11px; }
    .source { font-size: 12px; margin-top: 8px; }
    @media (max-width: 720px) { .wrap { padding:8px; } h1 { font-size:19px; } #map { height:650px; } .alt-control { width:235px; max-height:390px; } }
  </style>
</head>
<body>
<div class="wrap">
  <h1>Alternativas finais de partida — mapa interativo</h1>
  <p>Marque uma ou mais alternativas no painel superior direito para visualizar os eixos e contribuições laterais que devem iniciar os estudos contratados no Termo de Referência.</p>
  <div id="map" aria-label="Mapa interativo de alternativas de barragens no Taquari–Antas"></div>
  <p class="source">Fontes locais: BHO/ANA, malha municipal e rodovias do acervo do projeto. A base OSM é apenas cartográfica e pode depender de conexão com a internet. Os pontos são hipóteses de estudo; a seleção final depende de HEC-RAS 1D, topografia, operação, segurança, ambiente e custo-benefício.</p>
</div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
<script>
const DATA = __DATA__;
const map = L.map('map', { zoomControl: true }).setView([-29.27, -51.75], 9);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 18, attribution: '&copy; OpenStreetMap contributors' }).addTo(map);
const styles = {
  municipalities: { color:'#6b7280', weight:1, fillColor:'#e5e7eb', fillOpacity:.13 },
  hydro: f => f.properties.classe === 'rio principal' ? { color: f.properties.nome === 'Rio Forqueta' ? '#117a65' : (f.properties.nome === 'Rio Guaporé' ? '#7c3aed' : '#0b5fa5'), weight:2.8, opacity:.92 } : { color:'#8bbbd3', weight:.8, opacity:.65 },
  state: { color:'#6b7280', weight:1.0, opacity:.50 },
  federal: { color:'#d97706', weight:1.7, opacity:.72 },
  dam: { radius:8, color:'#111827', fillColor:'#111827', fillOpacity:.95, weight:1 }
};
function esc(value) { return String(value ?? 'n/d').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
function lineLayer(data, style, tooltip) { return L.geoJSON(data, { style, onEachFeature:(f,l)=>l.bindTooltip(tooltip(f)) }); }
const mun = L.geoJSON(DATA.municipios, { style:styles.municipalities, onEachFeature:(f,l)=>l.bindPopup('<b>'+esc(f.properties.NM_MUN)+'</b><br>Município do corredor de estudo') }).addTo(map);
const city = L.geoJSON(DATA.cidades, { pointToLayer:(f,latlng)=>L.marker(latlng, { icon:L.divIcon({ className:'city-label', html:'<span style="font-size:12px;font-weight:600;color:#1f2937;text-shadow:0 0 3px white,0 0 3px white;">'+esc(f.properties.cidade)+'</span>', iconAnchor:[0,0] }) }), onEachFeature:(f,l)=>l.bindTooltip(f.properties.cidade) }).addTo(map);
const hydro = lineLayer(DATA.hidrografia, styles.hydro, f => f.properties.nome || 'Afluente BHO').addTo(map);
const roadsState = lineLayer(DATA.rodovias_estaduais, styles.state, f => f.properties.rota || 'Rodovia estadual');
const roadsFederal = lineLayer(DATA.rodovias_federais, styles.federal, f => f.properties.rota || 'Rodovia federal');
const dams = L.geoJSON(DATA.usinas, { pointToLayer:(f,ll)=>L.circleMarker(ll,styles.dam), onEachFeature:(f,l)=>l.bindPopup('<b>'+esc(f.properties.nome)+'</b><br>Usina existente / restrição<br>Potência: '+esc(f.properties.potencia_kW)+' kW') }).addTo(map);

const byCode = {};
for (const collection of [DATA.eixos, DATA.exploratorios]) {
  for (const feature of collection.features) byCode[feature.properties.codigo] = feature;
}
const ALT_J = ['E01','E02','E04','E05','E08','E12'];
const ALT_DEFS = [
  { id:'hec00', label:'HEC-00 · referência', subtitle:'Situação atual — sem novos eixos', codes:[], color:'#64748b', shape:'circle' },
  { id:'hec01', label:'Alternativa 1 · HEC-01', subtitle:'E02 + E04 — arranjo-base', codes:['E02','E04'], color:'#00897b', shape:'circle' },
  { id:'hec02', label:'Alternativa 2 · HEC-02', subtitle:'E02 + E04 + E08 — extensão incremental', codes:['E02','E04','E08'], color:'#2563eb', shape:'circle' },
  { id:'hec03', label:'Alternativa 3 · HEC-03', subtitle:'E02 + E04 + E12 — cobertura terminal', codes:['E02','E04','E12'], color:'#d97706', shape:'circle' },
  { id:'hec04', label:'Alternativa 4 · HEC-04', subtitle:'ALT-J + GU1 — ramo do Guaporé', codes:ALT_J.concat(['GU1-PROPOSTO']), color:'#7c3aed', shape:'diamond' },
  { id:'hec05', label:'Alternativa 5 · HEC-05', subtitle:'ALT-J + FQ2 — ramo do Forqueta', codes:ALT_J.concat(['FQ2-PROPOSTO']), color:'#db2777', shape:'diamond' },
  { id:'hec06', label:'Alternativa 6 · HEC-06', subtitle:'ALT-J + FQ1 / comportas — sensibilidade', codes:ALT_J.concat(['FQ1-PROPOSTO']), color:'#b45309', shape:'diamond' },
  { id:'extra', label:'Sensibilidades adicionais', subtitle:'MC2 · CA2 · 14J2 · EST1', codes:['MC2-PROPOSTO','CA2-PROPOSTO','14J2-PROPOSTO','EST1-PROPOSTO'], color:'#475569', shape:'diamond' }
];
const altLayers = {};
function markerFor(feature, def) {
  const p = feature.properties;
  const lateral = p.codigo && p.codigo.includes('-PROPOSTO');
  const marker = L.circleMarker([feature.geometry.coordinates[1], feature.geometry.coordinates[0]], { radius:lateral ? 8 : 7, color:def.color, fillColor:def.color, fillOpacity:.92, weight:2 });
  marker.bindPopup('<b>'+esc(def.label)+'</b><br><b>'+esc(p.codigo)+'</b> — '+esc(p.nome || 'eixo da carteira')+'<br>'+esc(p.classe || p.grupo || 'Eixo de estudo')+'<br><span style="color:#4b5563">Ponto de triagem; não é projeto executivo.</span>');
  marker.bindTooltip(esc(p.codigo), { direction:'top', offset:[0,-5] });
  return marker;
}
for (const def of ALT_DEFS) {
  const group = L.layerGroup();
  for (const code of def.codes) if (byCode[code]) group.addLayer(markerFor(byCode[code], def));
  altLayers[def.id] = group;
}
const selected = new Set();
function updateDetail() {
  const detail = document.getElementById('alt-detail');
  if (!selected.size) { detail.textContent = 'Nenhuma alternativa adicional marcada. As usinas existentes permanecem visíveis como referência.'; return; }
  const names = ALT_DEFS.filter(d => selected.has(d.id)).map(d => d.id === 'hec00' ? 'HEC-00: situação atual' : d.label.replace(/^Alternativa [0-9]+ · /,''));
  detail.textContent = 'Ativas: ' + names.join(' | ');
}
const altControl = L.control({ position:'topright' });
altControl.onAdd = () => {
  const box = L.DomUtil.create('div','alt-control');
  box.innerHTML = '<div class="alt-title">Alternativas finais / TR</div><div class="alt-help">Marque para ligar os marcadores. É possível comparar mais de um caso.</div>';
  for (const def of ALT_DEFS) {
    const row = document.createElement('label'); row.className='alt-row';
    const input = document.createElement('input'); input.type='checkbox'; input.id='check-'+def.id; input.setAttribute('aria-label', def.label);
    const swatch = document.createElement('span'); swatch.className='alt-mark'; swatch.style.background=def.color; swatch.style.borderRadius=def.shape==='diamond' ? '1px' : '50%'; if (def.shape==='diamond') swatch.style.transform='rotate(45deg)';
    const text = document.createElement('span'); text.className='alt-text'; text.innerHTML='<strong>'+esc(def.label)+'</strong><span>'+esc(def.subtitle)+'</span>';
    row.append(input, swatch, text); box.appendChild(row);
    input.addEventListener('change', () => { if (input.checked) { selected.add(def.id); altLayers[def.id].addTo(map); } else { selected.delete(def.id); map.removeLayer(altLayers[def.id]); } updateDetail(); });
  }
  const detail = document.createElement('div'); detail.id='alt-detail'; detail.className='alt-detail'; detail.setAttribute('aria-live','polite'); detail.textContent='Nenhuma alternativa adicional marcada. As usinas existentes permanecem visíveis como referência.'; box.appendChild(detail);
  L.DomEvent.disableClickPropagation(box); L.DomEvent.disableScrollPropagation(box); return box;
};
altControl.addTo(map);
const legend = L.control({position:'bottomleft'}); legend.onAdd=()=>{ const d=L.DomUtil.create('div','legend'); d.innerHTML='<b>Referências</b><br><span class="swatch" style="border-color:#0b5fa5"></span>Rio Taquari / Antas<br><span class="swatch" style="border-color:#117a65"></span>Rio Forqueta<br><span class="swatch" style="border-color:#7c3aed"></span>Rio Guaporé<br><span class="swatch" style="border-color:#8bbbd3"></span>Afluentes BHO<br><span class="dot" style="background:#111827"></span>Usina existente / restrição<br><span class="dot" style="background:#2563eb"></span>Alternativa marcada'; return d; }; legend.addTo(map);
L.control.layers(null, { 'Municípios':mun, 'Rótulos das cidades':city, 'Hidrografia BHO':hydro, 'Rodovias estaduais':roadsState, 'Rodovias federais':roadsFederal, 'Usinas existentes':dams }, {collapsed:false, position:'topleft'}).addTo(map);
const focus = L.featureGroup([dams, L.geoJSON(DATA.eixos), L.geoJSON(DATA.exploratorios)]);
map.fitBounds(focus.getBounds().pad(.16));
</script>
</body>
</html>'''
    html = html.replace("__DATA__", text_payload)
    (ROOT / "06_resultados" / "GIS").mkdir(parents=True, exist_ok=True)
    (ROOT / "06_resultados" / "GIS" / "mapa_interativo_alternativas.html").write_text(html, encoding="utf-8")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    layers = load_layers()
    structures = load_structures()
    save_regional_map(layers, structures)
    save_forqueta_map(layers, structures)
    save_guapore_map(layers, structures)
    save_tr_start_map(layers, structures)
    save_tr_start_profile(structures)
    save_hand_maps(layers, structures)
    save_leaflet(layers, structures)
    print("Cartografia atualizada:")
    for p in [
        OUT / "MAPA_ALTERNATIVAS_HEC_PLANTA.png",
        OUT / "MAPA_EIXOS_FORQUETA.png",
        OUT / "MAPA_EIXO_GUAPORE_TRIAGEM.png",
        OUT / "MAPA_ALTERNATIVAS_PONTO_PARTIDA_TR.png",
        OUT / "PERFIL_ALTERNATIVAS_PONTO_PARTIDA_TR.png",
        OUT / "MAPA_HAND_SEM_VS_ALTJ.png",
        OUT / "MAPA_HAND_DIFERENCA_ALTJ.png",
        OUT / "REDUCAO_MANCHA_HAND_ALTJ_MUNICIPIOS.png",
        ROOT / "06_resultados" / "GIS" / "mapa_interativo_alternativas.html",
    ]:
        print(p)


if __name__ == "__main__":
    main()
