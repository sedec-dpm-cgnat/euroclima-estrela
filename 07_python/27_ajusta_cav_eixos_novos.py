# -*- coding: utf-8 -*-
"""Densifica e ajusta as CAVs dos eixos novos.

Para os eixos ainda sem reservatório, a CAV vem do relevo natural do MDE:
área conectada inundada e volume acumulado acima da cota do eixo. O pipeline
principal já calculou esses valores a cada 5 m entre 10 e 120 m em
``01_dados/cav/cav_todos.csv``. Este script não recalcula o relevo nem altera
os pontos originais; ele:

1. gera uma curva monotônica PCHIP em passos de 1 m, sem extrapolar;
2. ajusta polinômios de graus 2, 3 e 4 apenas para comparação/interpolação;
3. mede erro e monotonicidade dos polinômios;
4. recomenda a curva monotônica por trechos como modelo operacional da
   triagem, deixando o polinômio como forma compacta de documentação.

Os volumes continuam sendo estimativas de projeto baseadas no MDE, não CAV
batimétrica medida. A ausência de reservatório existente torna o método mais
defensável que a tentativa de reconstruir volume abaixo de um espelho d'água,
mas não elimina incertezas de resolução, conectividade e datum vertical.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pandas as pd


def pchip_slopes(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Derivadas PCHIP de Fritsch-Carlson, sem dependência do SciPy."""
    h = np.diff(x)
    delta = np.diff(y) / h
    d = np.zeros_like(y, dtype=float)
    if len(x) == 2:
        d[:] = delta[0]
        return d
    for k in range(1, len(x) - 1):
        if delta[k - 1] * delta[k] > 0:
            w1 = 2 * h[k] + h[k - 1]
            w2 = h[k] + 2 * h[k - 1]
            d[k] = (w1 + w2) / (w1 / delta[k - 1] + w2 / delta[k])
    d[0] = ((2 * h[0] + h[1]) * delta[0] - h[0] * delta[1]) / (h[0] + h[1])
    if d[0] * delta[0] <= 0:
        d[0] = 0.0
    elif delta[0] * delta[1] < 0 and abs(d[0]) > abs(3 * delta[0]):
        d[0] = 3 * delta[0]
    d[-1] = ((2 * h[-1] + h[-2]) * delta[-1] - h[-1] * delta[-2]) / (h[-1] + h[-2])
    if d[-1] * delta[-1] <= 0:
        d[-1] = 0.0
    elif delta[-1] * delta[-2] < 0 and abs(d[-1]) > abs(3 * delta[-1]):
        d[-1] = 3 * delta[-1]
    return d


def pchip_eval(x: np.ndarray, y: np.ndarray, query: np.ndarray) -> np.ndarray:
    slopes = pchip_slopes(x, y)
    q = np.asarray(query, dtype=float)
    idx = np.searchsorted(x, q, side="right") - 1
    idx = np.clip(idx, 0, len(x) - 2)
    h = x[idx + 1] - x[idx]
    t = (q - x[idx]) / h
    t2, t3 = t * t, t * t * t
    return (
        (2 * t3 - 3 * t2 + 1) * y[idx]
        + (t3 - 2 * t2 + t) * h * slopes[idx]
        + (-2 * t3 + 3 * t2) * y[idx + 1]
        + (t3 - t2) * h * slopes[idx + 1]
    )


def polyfit_scaled(x: np.ndarray, y: np.ndarray, degree: int) -> tuple[np.ndarray, float, float, bool]:
    center = float((x.min() + x.max()) / 2)
    scale = float((x.max() - x.min()) / 2)
    u = (x - center) / scale
    coef = np.polynomial.polynomial.polyfit(u, y, degree)
    pred = np.polynomial.polynomial.polyval(u, coef)
    dense = np.linspace(x.min(), x.max(), 1001)
    ud = (dense - center) / scale
    dense_pred = np.polynomial.polynomial.polyval(ud, coef)
    rmse = float(np.sqrt(np.mean((pred - y) ** 2)))
    max_abs = float(np.max(np.abs(pred - y)))
    monotonic = bool(np.all(np.diff(dense_pred) >= -1e-8))
    return coef, rmse, max_abs, monotonic


def write_csv(frame: pd.DataFrame, path: Path) -> None:
    frame.to_csv(path, sep=";", decimal=",", index=False, encoding="utf-8-sig")


def main() -> None:
    repo = Path(__file__).resolve().parents[2]
    root = Path(os.environ.get("EURO", repo))
    data_dir = root / "05_MODELAGEM" / "01_dados" / "cav"
    out_dir = root / "05_MODELAGEM" / "06_resultados" / "tabelas"
    out_dir.mkdir(parents=True, exist_ok=True)

    source = pd.read_csv(
        data_dir / "cav_todos.csv", sep=";", decimal=",", encoding="utf-8-sig"
    )
    required = {"eixo", "altura_m", "cota_NA_m", "area_alagada_km2", "volume_hm3"}
    missing = required - set(source.columns)
    if missing:
        raise ValueError(f"Colunas ausentes em cav_todos.csv: {sorted(missing)}")

    dense_rows: list[dict[str, object]] = []
    fit_rows: list[dict[str, object]] = []
    polynomial_json: dict[str, dict[str, object]] = {}

    for eixo, group in source.groupby("eixo", sort=True):
        g = group.sort_values("altura_m").drop_duplicates("altura_m")
        x = g.altura_m.to_numpy(dtype=float)
        area = g.area_alagada_km2.to_numpy(dtype=float)
        volume = g.volume_hm3.to_numpy(dtype=float)
        if len(g) < 4:
            raise ValueError(f"Poucos pontos para ajustar {eixo}: {len(g)}")
        if np.any(np.diff(area) < -1e-8) or np.any(np.diff(volume) < -1e-8):
            raise ValueError(f"CAV não monotônica na origem: {eixo}")

        query = np.arange(int(np.ceil(x.min())), int(np.floor(x.max())) + 1, 1.0)
        a_dense = pchip_eval(x, area, query)
        v_dense = pchip_eval(x, volume, query)
        cota_eixo = float(g.cota_NA_m.iloc[0] - g.altura_m.iloc[0])
        for h, a, v in zip(query, a_dense, v_dense):
            dense_rows.append({
                "eixo": eixo,
                "altura_m": h,
                "cota_NA_m": cota_eixo + h,
                "area_alagada_km2": a,
                "volume_hm3": v,
                "metodo": "PCHIP monotônica entre pontos MDE de 5 m",
                "fonte": "01_dados/cav/cav_todos.csv",
            })

        model_entry: dict[str, object] = {
            "altura_min_m": float(x.min()),
            "altura_max_m": float(x.max()),
            "cota_eixo_m": cota_eixo,
            "modelos": {},
        }
        for field, values in [("area", area), ("volume", volume)]:
            for degree in (2, 3, 4):
                coef, rmse, max_abs, monotonic = polyfit_scaled(x, values, degree)
                fit_rows.append({
                    "eixo": eixo,
                    "variavel": field,
                    "grau": degree,
                    "altura_centro_m": (x.min() + x.max()) / 2,
                    "meia_amplitude_m": (x.max() - x.min()) / 2,
                    "rmse_unidade": rmse,
                    "erro_max_abs_unidade": max_abs,
                    "monotono_no_intervalo": monotonic,
                    **{f"coef_c{i}": float(value) for i, value in enumerate(coef)},
                })
                model_entry["modelos"][f"{field}_grau_{degree}"] = {
                    "centro_m": float((x.min() + x.max()) / 2),
                    "meia_amplitude_m": float((x.max() - x.min()) / 2),
                    "coeficientes_potencia_crescente": [float(v) for v in coef],
                    "rmse": rmse,
                    "erro_maximo": max_abs,
                    "monotono_no_intervalo": monotonic,
                }
        polynomial_json[str(eixo)] = model_entry

    dense = pd.DataFrame(dense_rows)
    fits = pd.DataFrame(fit_rows)
    write_csv(dense, out_dir / "cav_eixos_novos_interpolada_1m.csv")
    write_csv(fits, out_dir / "cav_eixos_novos_ajustes_polinomiais.csv")
    (out_dir / "cav_eixos_novos_modelos.json").write_text(
        json.dumps(polynomial_json, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    summary = fits[fits.grau == 3].pivot(index="eixo", columns="variavel")
    print(f"Pontos originais: {len(source)} | pontos interpolados: {len(dense)}")
    print("\nValidação do polinômio cúbico (grau 3):")
    print(fits[fits.grau == 3][[
        "eixo", "variavel", "rmse_unidade", "erro_max_abs_unidade",
        "monotono_no_intervalo",
    ]].to_string(index=False))
    print("\nArquivos gravados em:", out_dir)


if __name__ == "__main__":
    main()
