"""Gera figuras da triagem HAND sem obra versus ALT-J.

Os rasters são produzidos por 08_manchas_hand.py. A figura não é uma mancha
hidráulica final: é uma comparação espacial de triagem baseada em HAND.
"""

from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch


ROOT = Path(__file__).resolve().parents[1]
GIS = ROOT / "01_dados" / "gis_derivado"
OUT = ROOT / "06_resultados" / "VALIDACAO"
SHP = Path(
    r"C:\Users\cassi\OneDrive\Documents\SEDEC\PROJETO_EUROCLIMA"
    r"\Documentos EUROCLIMA+\Espanha\GIS\shapefiles\Municipios_RS.shp"
)
CORREDOR = [
    "Muçum", "Roca Sales", "Encantado", "Colinas", "Arroio do Meio",
    "Cruzeiro do Sul", "Lajeado", "Estrela", "Bom Retiro do Sul",
    "Fazenda Vilanova", "Taquari", "Venâncio Aires", "Mato Leitão",
    "Santa Clara do Sul", "Marques de Souza", "Travesseiro", "Capitão",
    "Bom Princípio", "Sério",
]


def ler_raster(nome: str):
    with rasterio.open(GIS / nome) as src:
        arr = src.read(1).astype(float)
        transform = src.transform
        bounds = src.bounds
        crs = src.crs
    arr[arr <= 0] = np.nan
    return arr, transform, bounds, crs


def plot_limites(ax):
    if not SHP.exists():
        return
    mun = gpd.read_file(SHP).to_crs("EPSG:31982")
    mun = mun[mun["NM_MUN"].isin(CORREDOR)]
    mun.boundary.plot(ax=ax, color="#555555", linewidth=0.35, alpha=0.7)


def configurar(ax, bounds):
    ax.set_xlim(bounds.left, bounds.right)
    ax.set_ylim(bounds.bottom, bounds.top)
    ax.set_aspect("equal")
    ax.set_xlabel("Easting UTM 22S (m)")
    ax.set_ylabel("Northing UTM 22S (m)")
    ax.grid(color="#999999", linewidth=0.25, alpha=0.3)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    natural, transform, bounds, _ = ler_raster("mancha_sem_barragem_ALTJ_seca.tif")
    altj, _, _, _ = ler_raster("mancha_ALTJ_seca_triagem_ALTJ_seca.tif")

    vmax = np.nanpercentile(np.concatenate([natural[np.isfinite(natural)], altj[np.isfinite(altj)]]), 99)
    vmax = max(1.0, float(np.ceil(vmax)))
    extent = [bounds.left, bounds.right, bounds.bottom, bounds.top]

    fig, axes = plt.subplots(1, 2, figsize=(13.5, 7.4), constrained_layout=True)
    for ax, arr, title in [
        (axes[0], natural, "Sem novas barragens"),
        (axes[1], altj, "ALT-J — triagem seca; Qp = 6.213 m³/s"),
    ]:
        im = ax.imshow(arr, extent=extent, origin="upper", cmap="YlOrRd", vmin=0, vmax=vmax)
        plot_limites(ax)
        configurar(ax, bounds)
        ax.set_title(title)
    cb = fig.colorbar(im, ax=axes, shrink=0.75, pad=0.02)
    cb.set_label("Profundidade HAND estimada (m)")
    fig.suptitle(
        "Triagem espacial de inundação — evento de referência\n"
        "Comparação sem obra e com carteira ALT-J",
        fontsize=14,
    )
    fig.savefig(OUT / "MAPA_HAND_SEM_VS_ALTJ.png", dpi=220, bbox_inches="tight")
    plt.close(fig)

    # Mapa categórico da diferença espacial.
    diff, _, _, _ = ler_raster("mancha_diferenca_ALTJ_seca.tif")
    # ler_raster transforma o código 1/2 em nan apenas quando <=0; recuperar a
    # classificação original para garantir que o código seja exibido.
    with rasterio.open(GIS / "mancha_diferenca_ALTJ_seca.tif") as src:
        diff = src.read(1)
        bounds_diff = src.bounds
    masked = np.ma.masked_where(diff < 1, diff)
    cmap = ListedColormap(["#2ca25f", "#fdae6b"])
    fig, ax = plt.subplots(figsize=(8.6, 7.4), constrained_layout=True)
    ax.imshow(masked, extent=[bounds_diff.left, bounds_diff.right, bounds_diff.bottom, bounds_diff.top],
              origin="upper", cmap=cmap, vmin=1, vmax=2)
    plot_limites(ax)
    configurar(ax, bounds_diff)
    ax.set_title("Diferença espacial da mancha HAND — ALT-J")
    ax.legend(
        handles=[
            Patch(facecolor="#2ca25f", label="Área inundável retirada na triagem"),
            Patch(facecolor="#fdae6b", label="Área ainda inundável na triagem"),
        ],
        loc="lower left",
        frameon=True,
    )
    fig.savefig(OUT / "MAPA_HAND_DIFERENCA_ALTJ.png", dpi=220, bbox_inches="tight")
    plt.close(fig)

    # Redução por município — ordenada pelo ganho em área.
    tabela = pd.read_csv(GIS.parent.parent / "06_resultados" / "tabelas" / "manchas_por_municipio_ALTJ_seca.csv",
                         sep=";", decimal=",")
    tabela = tabela.sort_values("reducao_km2", ascending=True)
    fig, ax = plt.subplots(figsize=(9.5, 7.4), constrained_layout=True)
    ax.barh(tabela["municipio"], tabela["reducao_km2"], color="#3182bd")
    for y, (_, row) in enumerate(tabela.iterrows()):
        ax.text(row["reducao_km2"] + 0.08, y, f"{row['reducao_pct']:.1f}%", va="center", fontsize=8)
    ax.set_xlabel("Redução de área inundável na triagem (km²)")
    ax.set_ylabel("Município")
    ax.set_title("Efeito preliminar da ALT-J nas manchas HAND por município")
    ax.grid(axis="x", alpha=0.25)
    fig.savefig(OUT / "REDUCAO_MANCHA_HAND_ALTJ_MUNICIPIOS.png", dpi=220, bbox_inches="tight")
    plt.close(fig)

    print("Figuras geradas:")
    for name in [
        "MAPA_HAND_SEM_VS_ALTJ.png",
        "MAPA_HAND_DIFERENCA_ALTJ.png",
        "REDUCAO_MANCHA_HAND_ALTJ_MUNICIPIOS.png",
    ]:
        print(OUT / name)


if __name__ == "__main__":
    main()
