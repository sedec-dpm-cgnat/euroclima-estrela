# -*- coding: utf-8 -*-
"""Importa as curvas Cota x Área x Volume oficiais do SNIRH/ANA.

Fonte: registro ANA/SNIRH b8f0487a-df73-4f8d-8b22-bb49cf9f3683.

Os pacotes da ANA incluem planilha CAV, relatório batimétrico e geodatabase.
Este módulo trabalha apenas com as planilhas, sem alterar os arquivos ZIP
originais, e produz uma base tabular reproduzível para a análise de
deplecionamento dos três reservatórios da CERAN encontrados no registro.

Saídas:
  01_dados/cav_snirh/curvas/cav_snirh_consolidada.csv
  01_dados/cav_snirh/curvas/cav_<usina>.csv
  01_dados/cav_snirh/cav_snirh_ficha_tecnica.csv
  01_dados/cav_snirh/cav_snirh_ficha_tecnica.json

Os CSV usam ; como separador e vírgula como decimal, padrão do projeto.
"""

from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd


METADATA_URL = (
    "https://metadados.snirh.gov.br/geonetwork/srv/api/records/"
    "b8f0487a-df73-4f8d-8b22-bb49cf9f3683"
)

SOURCES = {
    "14 de Julho": {
        "pattern": "UHE 14 de Julho - CAV SNHIR.xlsx",
        "zip_url": "https://metadados.snirh.gov.br/files/"
        "b8f0487a-df73-4f8d-8b22-bb49cf9f3683/14_de_Julho.zip",
    },
    "Castro Alves": {
        "pattern": "UHE Castro Alves - CAV SNIRH.xlsx",
        "zip_url": "https://metadados.snirh.gov.br/files/"
        "b8f0487a-df73-4f8d-8b22-bb49cf9f3683/Castro_Alves.zip",
    },
    "Monte Claro": {
        "pattern": "UHE Monte Claro - CAV SNIRH.xlsx",
        "zip_url": "https://metadados.snirh.gov.br/files/"
        "b8f0487a-df73-4f8d-8b22-bb49cf9f3683/Monte_Claro.zip",
    },
}


def no_accents(value: object) -> str:
    text = "" if value is None else str(value)
    return "".join(
        c for c in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(c)
    ).lower().strip()


def clean_col(value: object) -> str:
    return re.sub(r"\s+", " ", no_accents(value)).strip()


def numeric(value: object) -> float | None:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    if isinstance(value, (int, float, np.integer, np.floating)):
        return float(value)
    text = str(value).strip().replace(" ", " ")
    match = re.search(r"[-+]?\d+(?:[.,]\d+)?", text)
    if not match:
        return None
    token = match.group(0).replace(",", ".")
    try:
        return float(token)
    except ValueError:
        return None


def ficha_rows(path: Path) -> list[tuple[str, object]]:
    workbook = pd.ExcelFile(path)
    sheet = next(s for s in workbook.sheet_names if no_accents(s).startswith("ficha"))
    raw = pd.read_excel(path, sheet_name=sheet, header=None)
    rows: list[tuple[str, object]] = []
    for _, row in raw.iloc[:, :2].iterrows():
        key = "" if pd.isna(row.iloc[0]) else str(row.iloc[0]).strip()
        value = None if pd.isna(row.iloc[1]) else row.iloc[1]
        rows.append((key, value))
    return rows


def ficha_value(rows: list[tuple[str, object]], contains: str) -> object:
    wanted = no_accents(contains)
    for key, value in rows:
        if wanted in no_accents(key) and value is not None:
            return value
    return None


def ficha_level(rows: list[tuple[str, object]], kind: str) -> float | None:
    """Lê o nível do reservatório na ficha, em Sistema Local.

    As fichas usam "Max. Normal" ou "max. Operacional" para o nível normal.
    """
    values: list[object] = []
    in_upstream_block = False
    for key, value in rows:
        nkey = no_accents(key)
        if "montante" in nkey:
            in_upstream_block = True
        elif in_upstream_block and "jusante" in nkey:
            break
        if in_upstream_block and value is not None:
            values.append(value)

    for value in values:
        text = no_accents(value)
        if kind == "normal" and ("max. normal" in text or "max normal" in text
                                  or "operacional" in text):
            return numeric(value)
        if kind == "maximorum" and "max" in text and "maximorum" in text:
            return numeric(value)
        if kind == "minimo" and ("min" in text or "minimo" in text):
            return numeric(value)
    return None


def curve_sheet(path: Path) -> tuple[pd.DataFrame, str]:
    workbook = pd.ExcelFile(path)
    sheet = next(s for s in workbook.sheet_names if no_accents(s).startswith("curvas"))
    raw = pd.read_excel(path, sheet_name=sheet, header=None)
    header = None
    for idx, row in raw.iterrows():
        if any("altitude ortometrica sl" in clean_col(v) for v in row.tolist()):
            header = int(idx)
            break
    if header is None:
        raise ValueError(f"Cabeçalho CAV não encontrado: {path}")

    data = pd.read_excel(path, sheet_name=sheet, header=header)
    lookup = {clean_col(col): col for col in data.columns}

    def column(prefix: str) -> object:
        for key, original in lookup.items():
            if key.startswith(prefix):
                return original
        raise KeyError(f"Coluna '{prefix}' não encontrada em {path.name}")

    out = pd.DataFrame({
        "cota_sl_m": pd.to_numeric(data[column("altitude ortometrica sl")], errors="coerce"),
        "cota_sgb_m": pd.to_numeric(data[column("altitude ortometrica sgb")], errors="coerce"),
        "area_km2": pd.to_numeric(data[column("area")], errors="coerce"),
        "volume_hm3": pd.to_numeric(data[column("volume")], errors="coerce"),
    }).dropna()
    out = out.sort_values("cota_sl_m").drop_duplicates("cota_sl_m").reset_index(drop=True)
    if len(out) < 10 or not out.cota_sl_m.is_monotonic_increasing:
        raise ValueError(f"Curva CAV inválida ou incompleta: {path}")
    return out, sheet


def parse_date(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, (datetime, pd.Timestamp)):
        return pd.Timestamp(value).strftime("%Y-%m-%d")
    return str(value).strip()


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", no_accents(value)).strip("_")


def write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, sep=";", decimal=",", index=False, encoding="utf-8-sig")


def main() -> None:
    repo = Path(__file__).resolve().parents[2]
    root = Path(__import__("os").environ.get("EURO", repo))
    cav_root = root / "05_MODELAGEM" / "01_dados" / "cav_snirh"
    source_dir = cav_root / "planilhas_cav"
    curve_dir = cav_root / "curvas"
    curve_dir.mkdir(parents=True, exist_ok=True)

    all_curves: list[pd.DataFrame] = []
    metadata: list[dict[str, object]] = []

    for usina, source in SOURCES.items():
        path = source_dir / source["pattern"]
        if not path.exists():
            raise FileNotFoundError(f"Planilha não encontrada: {path}")
        curve, sheet = curve_sheet(path)
        curve.insert(0, "usina", usina)
        curve["arquivo_fonte"] = path.name
        curve["registro_snirh"] = METADATA_URL.rsplit("/", 1)[-1]
        curve["url_download"] = source["zip_url"]
        all_curves.append(curve)
        write_csv(curve, curve_dir / f"cav_{slug(usina)}.csv")

        rows = ficha_rows(path)
        normal_sl = ficha_level(rows, "normal")
        maximorum_sl = ficha_level(rows, "maximorum")
        minimo_sl = ficha_level(rows, "minimo")
        cota_normal_sgb = (
            float(np.interp(normal_sl, curve["cota_sl_m"], curve["cota_sgb_m"]))
            if normal_sl is not None else None
        )
        metadata.append({
            "usina": usina,
            "arquivo_fonte": path.name,
            "aba_curvas": sheet,
            "data_atualizacao_cav": parse_date(
                ficha_value(rows, "data de atualização da cav")),
            "potencia_mw": numeric(ficha_value(rows, "potencia instalada")),
            "qmlt_m3_s": numeric(ficha_value(rows, "vazao media de longo termo")),
            "area_drenagem_km2": numeric(ficha_value(rows, "area de drenagem total")),
            "area_normal_km2": numeric(
                ficha_value(rows, "area inundada atualizada")),
            "volume_util_hm3": numeric(
                ficha_value(rows, "volume util atualizado")),
            "volume_normal_hm3": numeric(
                ficha_value(rows, "volume maximo normal atualizado")),
            "volume_maximorum_hm3": numeric(
                ficha_value(rows, "volume maximo maximorum atualizado")),
            "cota_normal_sl_m": normal_sl,
            "cota_normal_sgb_m": cota_normal_sgb,
            "cota_maximorum_sl_m": maximorum_sl,
            "cota_minima_operacional_sl_m": minimo_sl,
            "cota_minima_operacional_sgb_m": (
                float(np.interp(minimo_sl, curve["cota_sl_m"], curve["cota_sgb_m"]))
                if minimo_sl is not None else None
            ),
            "offset_sgb_m_na_normal": (
                cota_normal_sgb - normal_sl
                if normal_sl is not None and cota_normal_sgb is not None else None
            ),
            "registro_snirh": METADATA_URL,
            "url_download": source["zip_url"],
        })

    curves = pd.concat(all_curves, ignore_index=True)
    metadata_df = pd.DataFrame(metadata)
    write_csv(curves, curve_dir / "cav_snirh_consolidada.csv")
    write_csv(metadata_df, cav_root / "cav_snirh_ficha_tecnica.csv")
    (cav_root / "cav_snirh_ficha_tecnica.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"Curvas importadas: {len(curves):,} linhas")
    print(metadata_df[[
        "usina", "data_atualizacao_cav", "cota_normal_sl_m",
        "cota_normal_sgb_m", "area_normal_km2", "volume_normal_hm3",
        "volume_maximorum_hm3",
    ]].to_string(index=False))


if __name__ == "__main__":
    main()
