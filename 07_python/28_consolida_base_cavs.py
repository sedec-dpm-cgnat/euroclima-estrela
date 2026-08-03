# -*- coding: utf-8 -*-
"""Consolida em uma base única as CAVs oficiais e as CAVs dos eixos novos.

Não mistura os referenciais verticais silenciosamente: cada linha traz o
referencial da cota, a categoria da curva e a confiabilidade da fonte.
"""

from __future__ import annotations

import os
import re
import unicodedata
from pathlib import Path

import pandas as pd


def read(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, sep=";", decimal=",", encoding="utf-8-sig")


def slug(value: object) -> str:
    text = "".join(
        c for c in unicodedata.normalize("NFKD", str(value))
        if not unicodedata.combining(c)
    ).upper()
    return re.sub(r"[^A-Z0-9]+", "_", text).strip("_")


def main() -> None:
    repo = Path(__file__).resolve().parents[2]
    root = Path(os.environ.get("EURO", repo))
    cav_root = root / "05_MODELAGEM" / "01_dados" / "cav_snirh"
    curves_official = read(cav_root / "curvas" / "cav_snirh_consolidada.csv")
    ficha = read(cav_root / "cav_snirh_ficha_tecnica.csv")
    curves_new = read(root / "05_MODELAGEM" / "06_resultados" / "tabelas" / "cav_eixos_novos_interpolada_1m.csv")
    out_dir = root / "05_MODELAGEM" / "06_resultados" / "tabelas"
    out_dir.mkdir(parents=True, exist_ok=True)

    official = curves_official.merge(
        ficha[[
            "usina", "data_atualizacao_cav", "cota_normal_sl_m",
            "cota_normal_sgb_m", "volume_normal_hm3",
        ]], on="usina", how="left",
    )
    official_base = pd.DataFrame({
        "id_curva": "UHE_" + official.usina.map(slug),
        "nome": official.usina,
        "categoria": "UHE existente",
        "confiabilidade": "A - CAV oficial SNIRH/ANA",
        "referencial_cota": "Sistema Local; SGB preservado em coluna própria",
        "cota_referencial_m": official.cota_sl_m,
        "cota_sgb_m": official.cota_sgb_m,
        "altura_relativa_m": pd.NA,
        "area_km2": official.area_km2,
        "volume_hm3": official.volume_hm3,
        "cota_normal_m": official.cota_normal_sl_m,
        "cota_normal_sgb_m": official.cota_normal_sgb_m,
        "volume_normal_hm3": official.volume_normal_hm3,
        "metodo": "CAV oficial atualizada; planilha SNIRH/ANA",
        "arquivo_fonte": official.arquivo_fonte,
    })

    new_base = pd.DataFrame({
        "id_curva": "EIXO_" + curves_new.eixo,
        "nome": curves_new.eixo,
        "categoria": "Eixo novo sem reservatório existente",
        "confiabilidade": "B - Derivada do MDE natural; triagem",
        "referencial_cota": "MDE mdr.tif; datum vertical a confirmar",
        "cota_referencial_m": curves_new.cota_NA_m,
        "cota_sgb_m": pd.NA,
        "altura_relativa_m": curves_new.altura_m,
        "area_km2": curves_new.area_alagada_km2,
        "volume_hm3": curves_new.volume_hm3,
        "cota_normal_m": pd.NA,
        "cota_normal_sgb_m": pd.NA,
        "volume_normal_hm3": pd.NA,
        "metodo": curves_new.metodo,
        "arquivo_fonte": curves_new.fonte,
    })

    base = pd.concat([official_base, new_base], ignore_index=True)
    base = base.sort_values(["categoria", "nome", "cota_referencial_m"]).reset_index(drop=True)
    base.to_csv(
        out_dir / "cav_base_unica.csv", sep=";", decimal=",",
        index=False, encoding="utf-8-sig",
    )

    catalog = pd.DataFrame([
        {
            "id_curva": f"UHE_{slug(row.usina)}",
            "nome": row.usina,
            "categoria": "UHE existente",
            "confiabilidade": "A - CAV oficial SNIRH/ANA",
            "n_pontos": int((curves_official.usina == row.usina).sum()),
            "cota_min_m": float(curves_official[curves_official.usina == row.usina].cota_sl_m.min()),
            "cota_max_m": float(curves_official[curves_official.usina == row.usina].cota_sl_m.max()),
            "arquivo": "01_dados/cav_snirh/curvas/cav_snirh_consolidada.csv",
        }
        for _, row in ficha.iterrows()
    ] + [
        {
            "id_curva": f"EIXO_{eixo}",
            "nome": eixo,
            "categoria": "Eixo novo sem reservatório existente",
            "confiabilidade": "B - Derivada do MDE natural; triagem",
            "n_pontos": int((curves_new.eixo == eixo).sum()),
            "cota_min_m": float(curves_new[curves_new.eixo == eixo].cota_NA_m.min()),
            "cota_max_m": float(curves_new[curves_new.eixo == eixo].cota_NA_m.max()),
            "arquivo": "06_resultados/tabelas/cav_eixos_novos_interpolada_1m.csv",
        }
        for eixo in sorted(curves_new.eixo.unique())
    ])
    catalog.to_csv(
        out_dir / "catalogo_cavs.csv", sep=";", decimal=",",
        index=False, encoding="utf-8-sig",
    )
    print(f"Base única: {len(base):,} pontos | {len(catalog)} curvas")
    print(catalog[["id_curva", "confiabilidade", "n_pontos", "cota_min_m", "cota_max_m"]].to_string(index=False))


if __name__ == "__main__":
    main()
