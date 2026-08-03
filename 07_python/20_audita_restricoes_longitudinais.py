"""Audita a localização geométrica das usinas e restrições de remanso.

Este é um controle independente da revisão de alturas do Claude. Ele não
altera nenhuma tabela de decisão: apenas explicita estaca, distância ao canal,
diferença de cota e a usina operacional imediatamente a montante.
"""

from __future__ import annotations

import os
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

EURO = Path(os.environ["EURO"])
MODELAGEM = EURO / "05_MODELAGEM"
SHP = Path(os.environ["SHP"])
OUT = MODELAGEM / "06_resultados" / "VALIDACAO"
OUT.mkdir(parents=True, exist_ok=True)

PROFILE = MODELAGEM / "06_resultados" / "CLAUDE" / "claude_perfil_principal.csv"
APR = MODELAGEM / "06_resultados" / "tabelas" / "aproveitamentos_existentes.csv"
EIX = MODELAGEM / "01_dados" / "cav" / "eixos_todos.csv"

DIST_CANAL_M = 1500.0
TOL_COTA_M = 40.0

pf = pd.read_csv(PROFILE, sep=";", decimal=",").sort_values("dist_km").reset_index(drop=True)
xy = pf[["x_utm", "y_utm"]].to_numpy(float)

apr = pd.read_csv(APR, sep=";", decimal=",")
apr["potencia_MW"] = pd.to_numeric(apr["potencia_kW"], errors="coerce") / 1000.0
apr = apr[(apr["situacao"] == "operacao") & (apr["potencia_MW"] >= 15)].copy()

g = gpd.GeoDataFrame(apr, geometry=gpd.points_from_xy(apr["lon"], apr["lat"]), crs=4674).to_crs(31982)
coords = np.column_stack([g.geometry.x.to_numpy(), g.geometry.y.to_numpy()])
d2 = ((coords[:, None, :] - xy[None, :, :]) ** 2).sum(axis=2)
nearest = d2.argmin(axis=1)
apr["estaca_km"] = pf.iloc[nearest]["dist_km"].to_numpy()
apr["cota_talvegue_m"] = pf.iloc[nearest]["cota_m"].to_numpy()
apr["dist_canal_m"] = np.sqrt(d2[np.arange(len(apr)), nearest])
apr["no_canal_1500m"] = apr["dist_canal_m"] <= DIST_CANAL_M
apr["dif_cota_m"] = apr["cota_terreno_m"] - apr["cota_talvegue_m"]
apr["cota_coerente_40m"] = apr["dif_cota_m"].abs() <= TOL_COTA_M
apr["restricao_valida"] = apr["no_canal_1500m"] & apr["cota_coerente_40m"]

eix = pd.read_csv(EIX, sep=";", decimal=",")
ge = gpd.GeoDataFrame(eix, geometry=gpd.points_from_xy(eix["lon"], eix["lat"]), crs=4326).to_crs(31982)
ecoords = np.column_stack([ge.geometry.x.to_numpy(), ge.geometry.y.to_numpy()])
ed2 = ((ecoords[:, None, :] - xy[None, :, :]) ** 2).sum(axis=2)
enearest = ed2.argmin(axis=1)
eix["estaca_km"] = pf.iloc[enearest]["dist_km"].to_numpy()
eix["cota_talvegue_m"] = pf.iloc[enearest]["cota_m"].to_numpy()
eix["dist_canal_m"] = np.sqrt(ed2[np.arange(len(eix)), enearest])
eix["no_canal_1500m"] = eix["dist_canal_m"] <= DIST_CANAL_M

valid = apr[apr["restricao_valida"]].copy()
rows = []
for _, e in eix.sort_values("estaca_km").iterrows():
    cand = valid[(valid["estaca_km"] < e["estaca_km"]) & (valid["cota_terreno_m"] > e["cota_eixo_m"])]
    lim = cand.sort_values("estaca_km").iloc[-1] if len(cand) else None
    rows.append({
        "eixo": e["codigo"],
        "estaca_eixo_km": round(e["estaca_km"], 2),
        "dist_eixo_canal_m": round(e["dist_canal_m"], 1),
        "no_canal_1500m": bool(e["no_canal_1500m"]),
        "cota_eixo_m": e["cota_eixo_m"],
        "restricao_imediata_validada": lim["nome"] if lim is not None else "",
        "estaca_restricao_km": round(lim["estaca_km"], 2) if lim is not None else "",
        "dist_restricao_canal_m": round(lim["dist_canal_m"], 1) if lim is not None else "",
        "dif_cota_restricao_m": round(lim["dif_cota_m"], 1) if lim is not None else "",
    })

apr_cols = [
    "nome", "potencia_MW", "lat", "lon", "estaca_km", "dist_canal_m",
    "cota_terreno_m", "cota_talvegue_m", "dif_cota_m", "no_canal_1500m",
    "cota_coerente_40m", "restricao_valida",
]
apr[apr_cols].sort_values("estaca_km").to_csv(
    OUT / "auditoria_usinas_restricoes.csv", index=False, sep=";", decimal=","
)
pd.DataFrame(rows).to_csv(OUT / "auditoria_eixos_restricoes.csv", index=False, sep=";", decimal=",")

summary = [
    "# Auditoria independente das restrições longitudinais",
    "",
    f"- Usinas operacionais >=15 MW auditadas: **{len(apr)}**.",
    f"- Usinas a até 1.500 m do perfil principal: **{int(apr['no_canal_1500m'].sum())}**.",
    f"- Usinas com diferença de cota <=40 m: **{int(apr['cota_coerente_40m'].sum())}**.",
    f"- Usinas válidas como restrição: **{int(apr['restricao_valida'].sum())}**.",
    "",
    "A auditoria reproduz apenas a localização geométrica e a regra de seleção. A conectividade hidráulica dos eixos em tributários, a cota operacional real e a existência de aproveitamentos não cadastrados ainda exigem confirmação documental/campo.",
    "",
    "Arquivos detalhados: `auditoria_usinas_restricoes.csv` e `auditoria_eixos_restricoes.csv`.",
]
(OUT / "AUDITORIA_RESTRICOES_LONGITUDINAIS.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
print("usinas auditadas:", len(apr))
print("restricoes validas:", int(apr["restricao_valida"].sum()))
print("arquivos:", OUT)
