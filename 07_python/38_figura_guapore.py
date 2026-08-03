# -*- coding: utf-8 -*-
"""Gera mapa de conferência do eixo exploratório GU1."""

from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
GIS = ROOT / "06_resultados" / "GIS"
TAB = ROOT / "06_resultados" / "tabelas"
OUT = ROOT / "06_resultados" / "VALIDACAO" / "MAPA_EIXO_GUAPORE_TRIAGEM.png"

rede = gpd.read_file(GIS / "guapore_rede_principal.gpkg", layer="guapore_principal").to_crs(4326)
eixo = gpd.read_file(GIS / "eixo_guapore_proposto.gpkg", layer="eixo_guapore").to_crs(4326)

usinas = pd.read_csv(TAB / "aproveitamentos_existentes.csv", sep=";", decimal=",")
usinas = usinas[usinas["curso_dagua"].astype(str).str.startswith("7864")].copy()
usinas_geo = gpd.GeoDataFrame(
    usinas,
    geometry=gpd.points_from_xy(usinas["lon"], usinas["lat"]),
    crs=4326,
)

fig, ax = plt.subplots(figsize=(12, 8), dpi=180)
rede.plot(ax=ax, color="#5b7c99", linewidth=0.55, alpha=0.8, label="Rede BHO — Guaporé")
eixo.plot(ax=ax, color="#d62728", linewidth=3.2, label="GU1-PROPOSTO")
usinas_geo.plot(ax=ax, color="#f2a900", edgecolor="#6b4f00", markersize=42, zorder=5, label="Aproveitamentos")

for _, row in usinas_geo.iterrows():
    if str(row["nome"]).lower() in {"guaporé", "monte cuco"}:
        ax.annotate(str(row["nome"]), (row.geometry.x, row.geometry.y), xytext=(5, 5), textcoords="offset points", fontsize=8)

mid = eixo.geometry.iloc[0].interpolate(0.5, normalized=True)
ax.annotate("GU1-PROPOSTO\n−28,902566; −51,981445", (mid.x, mid.y), xytext=(8, -20), textcoords="offset points", fontsize=9, color="#8b0000", weight="bold", arrowprops={"arrowstyle": "->", "color": "#8b0000"})
ax.set_title("Guaporé — eixo exploratório preliminar e aproveitamentos existentes", fontsize=13, weight="bold")
ax.set_xlabel("Longitude (°)")
ax.set_ylabel("Latitude (°)")
ax.grid(True, alpha=0.25)
ax.legend(loc="best")
fig.text(0.01, 0.01, "Triagem BHO/D8; não é locação de engenharia. Validar remanso, CAV, cota e interferências.", fontsize=8)
fig.tight_layout()
OUT.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT, bbox_inches="tight")
plt.close(fig)
print(OUT)
