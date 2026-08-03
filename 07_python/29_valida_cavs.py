# -*- coding: utf-8 -*-
"""Valida monotonicidade e consistência básica das CAVs consolidadas."""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd


def read(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, sep=";", decimal=",", encoding="utf-8-sig")


def main() -> None:
    root = Path(os.environ.get("EURO", Path(__file__).resolve().parents[2]))
    out = root / "05_MODELAGEM" / "06_resultados" / "tabelas"
    curves = read(out / "cav_base_unica.csv")
    rows: list[dict[str, object]] = []
    for (category, name), g in curves.groupby(["categoria", "nome"], sort=True):
        g = g.sort_values("cota_referencial_m")
        cota = g.cota_referencial_m.to_numpy(float)
        area = g.area_km2.to_numpy(float)
        volume = g.volume_hm3.to_numpy(float)
        dc = np.diff(cota)
        da = np.diff(area)
        dv = np.diff(volume)
        valid = np.isfinite(cota) & np.isfinite(area) & np.isfinite(volume)
        # Para os eixos novos, a razão dV/dc ~ A é uma verificação de ordem
        # de grandeza; para CAV oficial, o mesmo teste deve ser praticamente
        # exato, sujeito à discretização da tabela.
        expected = (area[:-1] + area[1:]) * dc / 2
        rel = np.abs(dv - expected) / (np.abs(expected) + 1e-9)
        rows.append({
            "categoria": category,
            "nome": name,
            "n_pontos": int(len(g)),
            "cota_min_m": float(np.nanmin(cota)),
            "cota_max_m": float(np.nanmax(cota)),
            "area_monotona": bool(np.all(da >= -1e-10)),
            "volume_monotono": bool(np.all(dv >= -1e-10)),
            "cota_regular": bool(np.all(dc > 0)),
            "erro_rel_mediano_dv_area": float(np.nanmedian(rel[valid[:-1] & valid[1:]])) if len(rel) else np.nan,
            "erro_rel_maximo_dv_area": float(np.nanmax(rel[valid[:-1] & valid[1:]])) if len(rel) else np.nan,
        })
    report = pd.DataFrame(rows)
    report.to_csv(out / "validacao_cavs.csv", sep=";", decimal=",", index=False, encoding="utf-8-sig")
    headers = list(report.columns)
    md_table = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for _, row in report.iterrows():
        vals = []
        for col in headers:
            value = row[col]
            if isinstance(value, float):
                value = f"{value:.4g}"
            vals.append(str(value))
        md_table.append("| " + " | ".join(vals) + " |")
    md = [
        "# Validação das CAVs consolidadas",
        "",
        "A verificação testa cota crescente, área crescente, volume crescente e a relação de ordem de grandeza `dV/dc ≈ A`.",
        "A última relação não é um teste de precisão batimétrica; ela identifica inconsistências de unidade, sinal ou interpolação.",
        "",
        "\n".join(md_table),
        "",
        "As curvas que falharem monotonicidade não devem ser usadas para interpolação operacional.",
    ]
    (out / "VALIDACAO_CAVS.md").write_text("\n".join(md), encoding="utf-8")
    print(report.to_string(index=False))


if __name__ == "__main__":
    main()
