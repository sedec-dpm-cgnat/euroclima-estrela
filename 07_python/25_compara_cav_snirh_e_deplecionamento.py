# -*- coding: utf-8 -*-
"""Compara as CAV oficiais do SNIRH com a triagem do projeto.

Calcula também o volume de espera que poderia ser obtido por deplecionamento
preventivo dos três reservatórios com curva oficial disponível. A depleção é
calculada na curva em Sistema Local, pois os níveis normais da ficha técnica
estão nesse referencial. A coluna SGB é mantida para rastreabilidade e para a
comparação com o MDE, cujo datum vertical precisa ser confirmado.

Saídas:
  06_resultados/tabelas/comparacao_cav_snirh_projeto.csv
  06_resultados/tabelas/volume_deplecionamento_cav_snirh.csv
"""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd


DEPTHS_M = [1, 2, 3, 5, 8, 10, 15]
USINAS = ["14 de Julho", "Castro Alves", "Monte Claro"]


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, sep=";", decimal=",", encoding="utf-8-sig")


def interp(curve: pd.DataFrame, x: float, column: str) -> float:
    x_min, x_max = float(curve.cota_sl_m.min()), float(curve.cota_sl_m.max())
    if not np.isfinite(x) or x < x_min or x > x_max:
        return float("nan")
    return float(np.interp(x, curve.cota_sl_m, curve[column]))


def main() -> None:
    repo = Path(__file__).resolve().parents[2]
    root = Path(os.environ.get("EURO", repo))
    cav_root = root / "05_MODELAGEM" / "01_dados" / "cav_snirh"
    curve_path = cav_root / "curvas" / "cav_snirh_consolidada.csv"
    ficha_path = cav_root / "cav_snirh_ficha_tecnica.csv"
    project_path = root / "05_MODELAGEM" / "06_resultados" / "tabelas" / "aproveitamentos_existentes.csv"
    synthetic_wait_path = root / "05_MODELAGEM" / "06_resultados" / "tabelas" / "volume_espera_existentes.csv"
    out_dir = root / "05_MODELAGEM" / "06_resultados" / "tabelas"
    out_dir.mkdir(parents=True, exist_ok=True)

    curves = read_csv(curve_path)
    ficha = read_csv(ficha_path)
    project = read_csv(project_path)
    synthetic_wait = read_csv(synthetic_wait_path) if synthetic_wait_path.exists() else pd.DataFrame()
    project["nome_normalizado"] = project.nome.astype(str).str.strip()
    if len(synthetic_wait):
        synthetic_wait["nome_normalizado"] = synthetic_wait.nome.astype(str).str.strip()
    project = project[project.nome_normalizado.isin(USINAS)].copy()

    comparison: list[dict[str, object]] = []
    depletion: list[dict[str, object]] = []

    for usina in USINAS:
        c = curves[curves.usina == usina].sort_values("cota_sl_m").copy()
        f = ficha[ficha.usina == usina].iloc[0]
        p = project[project.nome_normalizado == usina].iloc[0]
        normal_sl = float(f.cota_normal_sl_m)
        normal_sgb = float(f.cota_normal_sgb_m)
        project_cota = float(p.cota_terreno_m)

        # A cota do projeto é comparada nos dois referenciais possíveis. A
        # diferença entre SL e SGB é pequena (~0,07–0,15 m), mas a distinção
        # evita apresentar como exata uma correspondência de datum ainda não
        # documentada no MDE.
        v_project_sl = interp(c, project_cota, "volume_hm3")
        a_project_sl = interp(c, project_cota, "area_km2")
        project_cota_sgb_assumption = project_cota
        v_project_sgb = float("nan")
        a_project_sgb = float("nan")
        if c.cota_sgb_m.min() <= project_cota_sgb_assumption <= c.cota_sgb_m.max():
            v_project_sgb = float(np.interp(
                project_cota_sgb_assumption, c.cota_sgb_m, c.volume_hm3))
            a_project_sgb = float(np.interp(
                project_cota_sgb_assumption, c.cota_sgb_m, c.area_km2))
        official_wait_10 = _official_wait(c, normal_sl, float(f.volume_normal_hm3), 10)
        official_wait_15 = _official_wait(c, normal_sl, float(f.volume_normal_hm3), 15)
        synthetic_wait_10 = _project_wait(synthetic_wait, usina, 10)
        synthetic_wait_15 = _project_wait(synthetic_wait, usina, 15)

        comparison.append({
            "usina": usina,
            "data_atualizacao_cav": f.data_atualizacao_cav,
            "cota_normal_sl_m": normal_sl,
            "cota_normal_sgb_m": normal_sgb,
            "area_normal_oficial_km2": float(f.area_normal_km2),
            "volume_normal_oficial_hm3": float(f.volume_normal_hm3),
            "volume_maximorum_oficial_hm3": float(f.volume_maximorum_hm3),
            "cota_projeto_mde_m": project_cota,
            "delta_cota_projeto_mde_m_vs_normal_sl": project_cota - normal_sl,
            "delta_cota_projeto_mde_m_vs_normal_sgb": project_cota - normal_sgb,
            "area_na_cota_projeto_assumindo_sl_km2": a_project_sl,
            "volume_na_cota_projeto_assumindo_sl_hm3": v_project_sl,
            "area_na_cota_projeto_assumindo_sgb_km2": a_project_sgb,
            "volume_na_cota_projeto_assumindo_sgb_hm3": v_project_sgb,
            "volume_oficial_espera_10m_hm3": official_wait_10,
            "volume_sintetico_espera_10m_hm3": synthetic_wait_10,
            "delta_sintetico_menos_oficial_10m_hm3": synthetic_wait_10 - official_wait_10,
            "razao_sintetico_dividido_oficial_10m": synthetic_wait_10 / official_wait_10,
            "volume_oficial_espera_15m_hm3": official_wait_15,
            "volume_sintetico_espera_15m_hm3": synthetic_wait_15,
            "delta_sintetico_menos_oficial_15m_hm3": synthetic_wait_15 - official_wait_15,
            "razao_sintetico_dividido_oficial_15m": synthetic_wait_15 / official_wait_15,
        })

        row: dict[str, object] = {
            "usina": usina,
            "data_atualizacao_cav": f.data_atualizacao_cav,
            "cota_normal_sl_m": normal_sl,
            "cota_normal_sgb_m": normal_sgb,
            "volume_normal_oficial_hm3": float(f.volume_normal_hm3),
            "area_normal_oficial_km2": float(f.area_normal_km2),
        }
        for depth in DEPTHS_M:
            lower = normal_sl - depth
            volume_lower = interp(c, lower, "volume_hm3")
            area_lower = interp(c, lower, "area_km2")
            row[f"cota_deplecionada_{depth}m_sl_m"] = lower
            row[f"area_na_deplecionada_{depth}m_km2"] = area_lower
            row[f"volume_na_deplecionada_{depth}m_hm3"] = volume_lower
            row[f"volume_espera_{depth}m_hm3"] = (
                float(f.volume_normal_hm3) - volume_lower
                if np.isfinite(volume_lower) else float("nan")
            )
        depletion.append(row)

    comparison_df = pd.DataFrame(comparison)
    depletion_df = pd.DataFrame(depletion)
    comparison_df.to_csv(
        out_dir / "comparacao_cav_snirh_projeto.csv",
        sep=";", decimal=",", index=False, encoding="utf-8-sig",
    )
    depletion_df.to_csv(
        out_dir / "volume_deplecionamento_cav_snirh.csv",
        sep=";", decimal=",", index=False, encoding="utf-8-sig",
    )

    print("COMPARAÇÃO CAV OFICIAL × TRIAGEM DO PROJETO")
    print(comparison_df[[
        "usina", "cota_normal_sl_m", "cota_normal_sgb_m",
        "cota_projeto_mde_m", "delta_cota_projeto_mde_m_vs_normal_sl",
        "volume_normal_oficial_hm3", "volume_sintetico_espera_10m_hm3",
    ]].to_string(index=False))
    print("\nVOLUME DE ESPERA OFICIAL POR DEPLECIONAMENTO")
    print(depletion_df[[
        "usina", "volume_espera_1m_hm3", "volume_espera_3m_hm3",
        "volume_espera_5m_hm3", "volume_espera_10m_hm3",
        "volume_espera_15m_hm3",
    ]].to_string(index=False))


def _project_wait(project: pd.DataFrame, usina: str, depth: int) -> float:
    """Busca a estimativa MDE histórica, se existir; não calcula uma nova."""
    col = f"V_acima_{depth}m_hm3"
    row = project[project.nome_normalizado == usina]
    if len(row) and col in row.columns:
        return float(row.iloc[0][col])
    return float("nan")


def _official_wait(curve: pd.DataFrame, normal_sl: float, normal_volume: float, depth: int) -> float:
    volume_lower = interp(curve, normal_sl - depth, "volume_hm3")
    return normal_volume - volume_lower


if __name__ == "__main__":
    main()
