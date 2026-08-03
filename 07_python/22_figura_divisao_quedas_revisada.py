"""Gera uma figura legível da divisão de quedas revisada."""

from __future__ import annotations

import os
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

EURO = Path(os.environ["EURO"])
MODELAGEM = EURO / "05_MODELAGEM"
OUT = MODELAGEM / "06_resultados" / "VALIDACAO"
OUT.mkdir(parents=True, exist_ok=True)

pf = pd.read_csv(MODELAGEM / "06_resultados" / "CLAUDE" / "claude_perfil_principal.csv", sep=";", decimal=",")
rev = pd.read_csv(MODELAGEM / "06_resultados" / "CLAUDE" / "claude_altura_admissivel_revisada.csv", sep=";", decimal=",")
eix = pd.read_csv(MODELAGEM / "01_dados" / "cav" / "eixos_todos.csv", sep=";", decimal=",")
apr = pd.read_csv(MODELAGEM / "06_resultados" / "tabelas" / "aproveitamentos_existentes.csv", sep=";", decimal=",")
apr["potencia_MW"] = pd.to_numeric(apr["potencia_kW"], errors="coerce") / 1000.0
apr = apr[(apr.situacao == "operacao") & (apr.potencia_MW >= 15)].copy()

xy = pf[["x_utm", "y_utm"]].to_numpy(float)

def posicoes(lat, lon):
    pts = gpd.GeoDataFrame(geometry=gpd.points_from_xy(lon, lat), crs=4674).to_crs(31982)
    arr = np.column_stack([pts.geometry.x, pts.geometry.y])
    d2 = ((arr[:, None, :] - xy[None, :, :]) ** 2).sum(axis=2)
    ii = d2.argmin(axis=1)
    return pf.iloc[ii]["dist_km"].to_numpy(), np.sqrt(d2[np.arange(len(ii)), ii]), pf.iloc[ii]["cota_m"].to_numpy()

apr["dist_km"], apr["dist_canal_m"], apr["talveg_m"] = posicoes(apr.lat, apr.lon)
eix["dist_km"], eix["dist_canal_m"], eix["talveg_m"] = posicoes(eix.lat, eix.lon)
rev = rev.merge(eix[["codigo", "dist_km", "talveg_m"]], left_on="eixo", right_on="codigo", how="left")
rev["cota_crista_m"] = rev.cota_eixo_m + rev.altura_max_m + 3.0

fig = plt.figure(figsize=(18, 12), dpi=160)
gs = fig.add_gridspec(2, 1, height_ratios=[3.5, 1.35], hspace=0.14)
ax = fig.add_subplot(gs[0])
ax.fill_between(pf.dist_km, pf.cota_m, 0, color="#e9dfcf", alpha=0.9)
ax.plot(pf.dist_km, pf.cota_m, color="#5b4a34", lw=1.5, label="talvegue")

for _, a in apr.iterrows():
    ax.plot([a.dist_km, a.dist_km], [a.talveg_m, a.cota_terreno_m], color="#2f6fa3", lw=2.3, alpha=0.85)
for _, r in rev.iterrows():
    color = "#238b45" if r.eixo in {"E02", "E04"} else ("#d07a00" if r.eixo == "E01" else "#9d2739")
    ax.plot([r.dist_km, r.dist_km], [r.talveg_m, r.cota_crista_m], color=color, lw=2.2, alpha=0.9)
    ax.plot(r.dist_km, r.cota_eixo_m + r.altura_max_m, "o", ms=4, color=color)
    ax.text(r.dist_km, r.cota_crista_m + 8, r.eixo, ha="center", va="bottom", fontsize=8, color=color, fontweight="bold")

for nome in ["Serra dos Cavalinhos II", "Castro Alves", "Monte Claro", "14 de Julho"]:
    q = apr[apr.nome.str.contains(nome[:12], na=False)]
    if len(q):
        a = q.iloc[0]
        ax.text(a.dist_km, a.cota_terreno_m + 9, nome, rotation=90, ha="center", va="bottom", fontsize=7, color="#2f6fa3")

legend = [
    Line2D([0], [0], color="#5b4a34", lw=1.5, label="talvegue"),
    Line2D([0], [0], color="#2f6fa3", lw=2.3, label="usinas existentes >=15 MW"),
    Line2D([0], [0], color="#238b45", lw=2.3, label="E02/E04 — baixa interferência na triagem"),
    Line2D([0], [0], color="#d07a00", lw=2.3, label="E01 — tributário, confirmar conexão"),
    Line2D([0], [0], color="#9d2739", lw=2.3, label="limitado por usina existente"),
]
ax.legend(handles=legend, loc="upper right", fontsize=9, frameon=True)
ax.set_title("Divisão de quedas revisada — rio das Antas/Taquari", fontsize=16, weight="bold", pad=12)
ax.set_xlabel("distância ao longo do talvegue (km), de montante para jusante")
ax.set_ylabel("cota (m)")
ax.set_xlim(0, pf.dist_km.max())
ax.set_ylim(0, max(pf.cota_m.max(), rev.cota_crista_m.max()) * 1.12)
ax.grid(axis="y", color="#dddddd", lw=0.7)

tab = fig.add_subplot(gs[1])
tab.axis("off")
show = rev.sort_values("dist_km")[["eixo", "dist_km", "altura_max_m", "volume_max_hm3", "restricao", "limitante"]].copy()
show.columns = ["Eixo", "Estaca (km)", "Altura (m)", "Volume (hm³)", "Restrição imediata", "Limitante"]
show["Estaca (km)"] = show["Estaca (km)"].map(lambda x: f"{x:.1f}")
show["Altura (m)"] = show["Altura (m)"].map(lambda x: f"{x:.1f}")
show["Volume (hm³)"] = show["Volume (hm³)"].map(lambda x: f"{x:.0f}")
table = tab.table(cellText=show.values, colLabels=show.columns, loc="center", cellLoc="center", colLoc="center", bbox=[0, 0, 1, 0.95])
table.auto_set_font_size(False)
table.set_fontsize(8.2)
table.scale(1, 1.45)
for (row, col), cell in table.get_celld().items():
    if row == 0:
        cell.set_facecolor("#3f536b")
        cell.set_text_props(color="white", weight="bold")
    elif row % 2 == 0:
        cell.set_facecolor("#f1f4f7")
tab.set_title("Tabela de controle — alturas revisadas; teto de 120 m é hipótese de triagem", fontsize=10, pad=4)

fig.savefig(OUT / "DIVISAO_QUEDAS_REVISADA.png", bbox_inches="tight")
print("gravado:", OUT / "DIVISAO_QUEDAS_REVISADA.png")


# ---------------------------------------------------------------------------
# Zooms para leitura das alternativas no relatório/site.
# A figura geral preserva o contexto longitudinal; os recortes permitem ler
# cotas, rótulos e restrições na cascata principal sem aumentar artificialmente
# a escala de todo o perfil.
def cor_eixo(eixo):
    return "#238b45" if eixo in {"E02", "E04"} else ("#d07a00" if eixo == "E01" else "#9d2739")


def zoom_divisao(xmin, xmax, ymin, ymax, nome_saida, titulo):
    figz, axz = plt.subplots(figsize=(16, 8), dpi=220)
    axz.fill_between(pf.dist_km, pf.cota_m, 0, color="#e9dfcf", alpha=0.9)
    axz.plot(pf.dist_km, pf.cota_m, color="#5b4a34", lw=2.0, label="talvegue")
    for _, a in apr.iterrows():
        if xmin - 5 <= a.dist_km <= xmax + 5:
            axz.plot([a.dist_km, a.dist_km], [a.talveg_m, a.cota_terreno_m],
                     color="#2f6fa3", lw=3.0, alpha=0.9)
    sub = rev[(rev.dist_km >= xmin - 5) & (rev.dist_km <= xmax + 5)].copy()
    # Os eixos E03/E06/E07/E08 ficam a poucos quilômetros uns dos outros;
    # deslocamentos em pontos separam os rótulos sem alterar suas posições.
    label_offsets = {
        "E03": (-20, 23), "E06": (-25, 8),
        "E07": (18, 23), "E08": (34, 8),
    }
    for _, r in sub.iterrows():
        color = cor_eixo(r.eixo)
        axz.plot([r.dist_km, r.dist_km], [r.talveg_m, r.cota_crista_m],
                 color=color, lw=3.0, alpha=0.95)
        axz.plot(r.dist_km, r.cota_eixo_m + r.altura_max_m, "o", ms=7, color=color)
        axz.annotate(r.eixo, (r.dist_km, r.cota_crista_m),
                     xytext=label_offsets.get(r.eixo, (0, 9)),
                     textcoords="offset points", ha="center", fontsize=13,
                     color=color, fontweight="bold")
    for nome in ["Serra dos Cavalinhos II", "Castro Alves", "Monte Claro", "14 de Julho"]:
        q = apr[(apr.nome.str.contains(nome[:12], na=False)) &
                (apr.dist_km >= xmin - 5) & (apr.dist_km <= xmax + 5)]
        if len(q):
            a = q.iloc[0]
            axz.annotate(nome, (a.dist_km, a.cota_terreno_m), xytext=(0, 10),
                         textcoords="offset points", rotation=90,
                         ha="center", va="bottom", fontsize=11, color="#2f6fa3")
    axz.set_xlim(xmin, xmax); axz.set_ylim(ymin, ymax)
    axz.set_title(titulo, fontsize=18, weight="bold", pad=12)
    axz.set_xlabel("Distância ao longo do talvegue (km), montante → jusante", fontsize=13)
    axz.set_ylabel("Cota (m)", fontsize=13)
    axz.tick_params(labelsize=11)
    axz.grid(axis="y", color="#dddddd", lw=0.8)
    axz.legend(handles=legend, loc="upper right", fontsize=10, frameon=True)
    figz.tight_layout()
    figz.savefig(OUT / nome_saida, bbox_inches="tight")
    plt.close(figz)
    print("gravado:", OUT / nome_saida)


zoom_divisao(
    225, 290, 180, 455,
    "DIVISAO_QUEDAS_ZOOM_E02_E04_CASTRO.png",
    "Zoom — E02/E04, Castro Alves e alternativas do trecho intermediário",
)
zoom_divisao(
    250, 385, 25, 300,
    "DIVISAO_QUEDAS_ZOOM_CASCATA_ANTAS.png",
    "Zoom — cascata Monte Claro–Castro Alves–14 de Julho e eixos jusante",
)
