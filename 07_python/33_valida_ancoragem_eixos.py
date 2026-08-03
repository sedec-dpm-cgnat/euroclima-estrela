# -*- coding: utf-8 -*-
"""Compara a carteira canônica com a rodada isolada de ancoragem BHO/D8."""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
old_path = ROOT / "01_dados" / "cav" / "eixos_todos.csv"
new_path = ROOT / "01_dados" / "cav_anchor_check2" / "eixos_todos.csv"
out_path = ROOT / "06_resultados" / "VALIDACAO" / "validacao_ancoragem_eixos.csv"
out_path.parent.mkdir(parents=True, exist_ok=True)

old = pd.read_csv(old_path, sep=";", decimal=",", encoding="utf-8-sig")
new = pd.read_csv(new_path, sep=";", decimal=",", encoding="utf-8-sig")
old = old.add_suffix("_anterior").rename(columns={"codigo_anterior": "codigo"})
new = new.add_suffix("_intersecao").rename(columns={"codigo_intersecao": "codigo"})
df = old.merge(new, on="codigo", how="outer", validate="one_to_one")

for c in ["area_km2", "area_BHO_km2", "cota_eixo_m", "lat", "lon"]:
    df[f"{c}_anterior"] = pd.to_numeric(df[f"{c}_anterior"], errors="coerce")
    df[f"{c}_intersecao"] = pd.to_numeric(df[f"{c}_intersecao"], errors="coerce")
df["delta_area_km2"] = df["area_km2_intersecao"] - df["area_km2_anterior"]
df["delta_cota_m"] = df["cota_eixo_m_intersecao"] - df["cota_eixo_m_anterior"]
df["delta_lat"] = df["lat_intersecao"] - df["lat_anterior"]
df["delta_lon"] = df["lon_intersecao"] - df["lon_anterior"]
df["aderencia_nova"] = df["aderencia_D8_BHO_intersecao"]
df["intersectou_BHO"] = df["ancoragem_por_intersecao_intersecao"]
df["status"] = np.where(
    df["aderencia_nova"].between(0.9, 1.1) & (df["delta_area_km2"].abs() <= 5),
    "aderência dentro do intervalo; conferir pequenas mudanças de ponto/cota",
    "revisar antes de atualizar a carteira canônica",
)
cols = [
    "codigo", "area_km2_anterior", "area_km2_intersecao", "delta_area_km2",
    "area_BHO_km2_intersecao", "aderencia_nova", "cota_eixo_m_anterior",
    "cota_eixo_m_intersecao", "delta_cota_m", "lat_anterior", "lat_intersecao",
    "lon_anterior", "lon_intersecao", "intersectou_BHO", "status",
]
df[cols].sort_values("codigo").to_csv(out_path, sep=";", decimal=",", index=False, encoding="utf-8-sig")
print(out_path)
print(df[cols].sort_values("codigo").to_string(index=False))
