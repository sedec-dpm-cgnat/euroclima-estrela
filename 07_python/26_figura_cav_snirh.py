# -*- coding: utf-8 -*-
"""Gera uma figura SVG de controle das curvas CAV oficiais do SNIRH.

O projeto não exige uma biblioteca gráfica para esta figura: o SVG é escrito
diretamente para permanecer reproduzível também no ambiente mínimo usado na
rotina de processamento.
"""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd


def main() -> None:
    repo = Path(__file__).resolve().parents[2]
    root = Path(os.environ.get("EURO", repo))
    data = root / "05_MODELAGEM" / "01_dados" / "cav_snirh" / "curvas" / "cav_snirh_consolidada.csv"
    ficha = root / "05_MODELAGEM" / "01_dados" / "cav_snirh" / "cav_snirh_ficha_tecnica.csv"
    output = root / "05_MODELAGEM" / "06_resultados" / "VALIDACAO" / "CAV_SNIRH_CURVAS.svg"
    output.parent.mkdir(parents=True, exist_ok=True)

    curves = pd.read_csv(data, sep=";", decimal=",", encoding="utf-8-sig")
    meta = pd.read_csv(ficha, sep=";", decimal=",", encoding="utf-8-sig")

    width, height = 1200, 930
    margin_x, margin_y = 92, 62
    panel_w, panel_h = 500, 235
    gap_x, gap_y = 80, 58
    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        '<style>text{font-family:Arial,sans-serif;fill:#263238} '
        '.grid{stroke:#d8e0e4;stroke-width:1}.axis{stroke:#65747c;stroke-width:1.2} '
        '.title{font-size:16px;font-weight:bold}.label{font-size:12px} '
        '.tick{font-size:10px}.note{font-size:11px;fill:#8a2525}</style>',
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="600" y="29" text-anchor="middle" font-size="20" font-weight="bold">'
        'Curvas Cota × Área × Volume — SNIRH/ANA | CERAN</text>',
    ]

    def esc(value: object) -> str:
        return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def line(points: list[tuple[float, float]], color: str, width_: float = 2.0) -> str:
        pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
        return f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="{width_}"/>'

    for row, usina in enumerate(["14 de Julho", "Castro Alves", "Monte Claro"]):
        c = curves[curves.usina == usina].sort_values("cota_sl_m")
        m = meta[meta.usina == usina].iloc[0]
        normal = float(m.cota_normal_sl_m)
        x_min, x_max = float(c.cota_sl_m.min()), float(c.cota_sl_m.max())
        x_range = x_max - x_min
        for col, title, color, ylabel in [
            ("area_km2", "área", "#1976a5", "Área (km²)"),
            ("volume_hm3", "volume", "#2f8f5b", "Volume acumulado (hm³)"),
        ]:
            col_idx = 0 if col == "area_km2" else 1
            x0 = margin_x + col_idx * (panel_w + gap_x)
            y0 = margin_y + row * (panel_h + gap_y)
            values = c[col].astype(float)
            y_min, y_max = 0.0, float(values.max()) * 1.08
            plot_left, plot_right = x0 + 60, x0 + panel_w - 12
            plot_top, plot_bottom = y0 + 28, y0 + panel_h - 37
            sx = lambda v: plot_left + (v - x_min) / x_range * (plot_right - plot_left)
            sy = lambda v: plot_bottom - (v - y_min) / (y_max - y_min) * (plot_bottom - plot_top)
            elements.append(f'<text class="title" x="{x0 + 8}" y="{y0 + 17}">{esc(usina)} — {title}</text>')
            for frac in (0, 0.5, 1):
                xx = plot_left + frac * (plot_right - plot_left)
                yy = plot_bottom - frac * (plot_bottom - plot_top)
                elements.append(f'<line class="grid" x1="{xx:.1f}" y1="{plot_top}" x2="{xx:.1f}" y2="{plot_bottom}"/>')
                elements.append(f'<line class="grid" x1="{plot_left}" y1="{yy:.1f}" x2="{plot_right}" y2="{yy:.1f}"/>')
                elements.append(f'<text class="tick" x="{xx:.1f}" y="{plot_bottom + 16}" text-anchor="middle">{x_min + frac * x_range:.1f}</text>')
                elements.append(f'<text class="tick" x="{plot_left - 8}" y="{yy + 3:.1f}" text-anchor="end">{y_min + frac * (y_max - y_min):.1f}</text>')
            elements.append(f'<line class="axis" x1="{plot_left}" y1="{plot_bottom}" x2="{plot_right}" y2="{plot_bottom}"/>')
            elements.append(f'<line class="axis" x1="{plot_left}" y1="{plot_top}" x2="{plot_left}" y2="{plot_bottom}"/>')
            elements.append(f'<line x1="{sx(normal):.1f}" y1="{plot_top}" x2="{sx(normal):.1f}" y2="{plot_bottom}" stroke="#b33a3a" stroke-dasharray="5,4"/>')
            elements.append(line([(sx(x), sy(y)) for x, y in zip(c.cota_sl_m, values)], color))
            elements.append(f'<text class="label" x="{(plot_left + plot_right) / 2:.1f}" y="{y0 + panel_h - 8}" text-anchor="middle">Cota no sistema local (m)</text>')
            elements.append(f'<text class="label" transform="translate({x0 + 13},{(plot_top + plot_bottom) / 2:.1f}) rotate(-90)" text-anchor="middle">{ylabel}</text>')
            if col == "volume_hm3":
                elements.append(f'<text class="note" x="{plot_left + 7}" y="{plot_top + 16}">NA normal = {normal:.2f} m</text>')
    elements.append('</svg>')
    output.write_text("\n".join(elements), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
