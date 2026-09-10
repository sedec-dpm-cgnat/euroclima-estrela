# -*- coding: utf-8 -*-
"""Gera o hidrograma comparativo dos casos HEC-00 a HEC-06.

As séries HEC-00, HEC-01, HEC-02, HEC-03, HEC-05 e HEC-06 vêm da rodada
combinada Antas + Forqueta, sempre na seção de Estrela e sob a regra seca.
O HEC-04 vem da rodada específica do Guaporé, também corrigida para manter a
contribuição natural do Forqueta até Estrela quando não há eixo nesse ramo.

São resultados de triagem hidrológica/volumétrica; não substituem as séries
calibradas e os hidrogramas de saída a serem produzidos no HEC-RAS 1D.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
D_RES = ROOT / "06_resultados"
D_TAB = D_RES / "tabelas"
D_FIG = D_RES / "figuras"
D_FIG.mkdir(parents=True, exist_ok=True)

RD = dict(sep=";", decimal=",", encoding="utf-8-sig")
WR = dict(sep=";", decimal=",", encoding="utf-8-sig", index=False)

COMBINADO = pd.read_csv(D_TAB / "hidrogramas_combinados_antas_forqueta.csv", **RD)
GUAPORE = pd.read_csv(D_TAB / "hidrogramas_guapore_antas.csv", **RD)


def buscar(df: pd.DataFrame, cenario: str, regra: str) -> pd.DataFrame:
    out = df[(df["cenario"] == cenario) & (df["regra"] == regra)].copy()
    if out.empty:
        raise ValueError(f"Série não encontrada: {cenario} / {regra}")
    return out.sort_values("tempo_h").reset_index(drop=True)


def buscar_guapore(cenario: str) -> pd.DataFrame:
    out = GUAPORE[GUAPORE["cenario"] == cenario].copy()
    if out.empty:
        raise ValueError(f"Série do Guaporé não encontrada: {cenario}")
    return out.sort_values("tempo_h").reset_index(drop=True)


# A nomenclatura é a mesma usada no mapa Leaflet e na matriz do HEC-RAS.
DEFS = [
    ("HEC-00", "SEM_OBRA", "natural", "situação atual", "#334155"),
    ("HEC-01", "ALT-A+SEM_FORQUETA+seca", "seca", "E02 + E04", "#00897b"),
    ("HEC-02", "ALT-D+SEM_FORQUETA+seca", "seca", "E02 + E04 + E08", "#2563eb"),
    ("HEC-03", "ALT-E+SEM_FORQUETA+seca", "seca", "E02 + E04 + E12", "#d97706"),
    ("HEC-05", "ALT-J+FQ2+seca", "seca", "ALT-J + FQ2", "#db2777"),
    ("HEC-06", "ALT-J+FQ1+seca", "seca", "ALT-J + FQ1", "#b45309"),
]

series = {}
labels = {}
colors = {}
for codigo, cenario, regra, descricao, color in DEFS:
    s = buscar(COMBINADO, cenario, regra)
    series[codigo] = s
    labels[codigo] = descricao
    colors[codigo] = color

# O HEC-04 usa o pico histórico do posto Santa Lúcia e GU1 com 100 m,
# altura ainda exploratória. A série já foi exportada pelo script 42.
s_gu = buscar_guapore("HEC-04")
series["HEC-04"] = s_gu
labels["HEC-04"] = "ALT-J + GU1 (100 m)"
colors["HEC-04"] = "#7c3aed"

referencia = series["HEC-00"]
t = referencia["tempo_h"].to_numpy(float)
for codigo, s in series.items():
    if len(s) != len(referencia) or not (s["tempo_h"].to_numpy(float) == t).all():
        raise ValueError(f"A série {codigo} não está na mesma malha temporal do HEC-00.")

peaks = []
for codigo, s in series.items():
    i = s["pico_m3s"].astype(float).idxmax()
    peaks.append(
        {
            "cenario": codigo,
            "descricao": labels[codigo],
            "pico_m3s": float(s.loc[i, "pico_m3s"]),
            "tempo_pico_h": float(s.loc[i, "tempo_h"]),
        }
    )
peaks_df = pd.DataFrame(peaks)
peaks_df.to_csv(D_TAB / "17_hidrogramas_alternativas_tr_picos.csv", **WR)

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9.5})
fig, (ax, ax_zoom) = plt.subplots(
    2,
    1,
    figsize=(13.4, 9.2),
    dpi=220,
    gridspec_kw={"height_ratios": [1.12, 1.0]},
)

for codigo in ["HEC-00", "HEC-01", "HEC-02", "HEC-03", "HEC-04", "HEC-05", "HEC-06"]:
    s = series[codigo]
    peak = peaks_df.loc[peaks_df["cenario"] == codigo, "pico_m3s"].iloc[0]
    lw = 2.8 if codigo == "HEC-00" else 1.85
    alpha = 0.96 if codigo == "HEC-00" else 0.9
    ax.plot(t, s["pico_m3s"], color=colors[codigo], lw=lw, alpha=alpha, label=f"{codigo} — {labels[codigo]} ({peak:,.0f} m³/s)")
    ax_zoom.plot(t, s["pico_m3s"], color=colors[codigo], lw=lw, alpha=alpha)

limiar = 4000.0
for a in (ax, ax_zoom):
    a.axhline(limiar, color="#9467bd", ls="--", lw=1.35, alpha=0.95)
    a.grid(True, color="#cbd5e1", alpha=0.5, linewidth=0.7)
    a.set_ylabel("Vazão em Estrela (m³/s)")
    a.set_ylim(bottom=0)

ax.set_xlim(float(t.min()), float(t.max()))
ax.set_title("Evento completo — comparação das vazões resultantes", loc="left", fontsize=11.5, fontweight="bold")
ax.text(
    float(t.max()) - 2.0,
    limiar + 180,
    "limiar preliminar: 4.000 m³/s",
    ha="right",
    va="bottom",
    color="#6a3d9a",
    fontsize=8.5,
)

peak_t = float(peaks_df.loc[peaks_df["cenario"] == "HEC-00", "tempo_pico_h"].iloc[0])
zoom_min = max(float(t.min()), peak_t - 85.0)
zoom_max = min(float(t.max()), peak_t + 175.0)
ax_zoom.set_xlim(zoom_min, zoom_max)
ax_zoom.set_title("Detalhe da janela de pico", loc="left", fontsize=11.5, fontweight="bold")
ax_zoom.set_xlabel("Tempo desde o início do hidrograma (h)")
ax_zoom.text(
    zoom_max - 2.0,
    limiar + 120,
    "limiar preliminar: 4.000 m³/s",
    ha="right",
    va="bottom",
    color="#6a3d9a",
    fontsize=8.5,
)

handles, legend_labels = ax.get_legend_handles_labels()
fig.legend(
    handles,
    legend_labels,
    loc="lower center",
    bbox_to_anchor=(0.5, 0.028),
    ncol=2,
    frameon=True,
    framealpha=0.97,
    edgecolor="#cbd5e1",
    fontsize=8.7,
)
fig.suptitle(
    "Hidrogramas associados às alternativas de partida do Termo de Referência",
    fontsize=16,
    fontweight="bold",
    y=0.985,
)
fig.text(
    0.5,
    0.005,
    "Triagem na seção de Estrela; regra seca. HEC-04: ALT-J + GU1 a 100 m, altura exploratória. "
    "As séries devem ser substituídas/validadas no HEC-RAS 1D com operação, remanso e dados observados.",
    ha="center",
    va="bottom",
    fontsize=8.0,
    color="#475569",
)
fig.tight_layout(rect=(0.02, 0.105, 0.985, 0.95))
fig.savefig(D_FIG / "17_hidrogramas_alternativas_tr.png", dpi=300, bbox_inches="tight", facecolor="white")
fig.savefig(D_FIG / "17_hidrogramas_alternativas_tr.svg", bbox_inches="tight", facecolor="white")
plt.close(fig)

print("Figura gerada:", D_FIG / "17_hidrogramas_alternativas_tr.png")
print(peaks_df.to_string(index=False, formatters={"pico_m3s": "{:,.1f}".format, "tempo_pico_h": "{:,.1f}".format}))
