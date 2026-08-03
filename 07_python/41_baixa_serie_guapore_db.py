# -*- coding: utf-8 -*-
"""Baixa, em modo somente leitura, a série do Guaporé no banco DPM.

As credenciais são lidas exclusivamente das variáveis de ambiente:
EUROCLIMA_DB_HOST, EUROCLIMA_DB_PORT, EUROCLIMA_DB_NAME,
EUROCLIMA_DB_USER e EUROCLIMA_DB_PASSWORD.

Saída: 01_dados/dpm_db/86580000_vazao.csv.
"""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import psycopg2


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "01_dados" / "dpm_db" / "86580000_vazao.csv"
CODIGO = "86580000"


def connect():
    required = (
        "EUROCLIMA_DB_HOST",
        "EUROCLIMA_DB_NAME",
        "EUROCLIMA_DB_USER",
        "EUROCLIMA_DB_PASSWORD",
    )
    missing = [key for key in required if not os.environ.get(key)]
    if missing:
        raise RuntimeError("Variáveis ausentes: " + ", ".join(missing))
    return psycopg2.connect(
        host=os.environ["EUROCLIMA_DB_HOST"],
        port=int(os.environ.get("EUROCLIMA_DB_PORT", "5432")),
        dbname=os.environ["EUROCLIMA_DB_NAME"],
        user=os.environ["EUROCLIMA_DB_USER"],
        password=os.environ["EUROCLIMA_DB_PASSWORD"],
        connect_timeout=20,
        options="-c default_transaction_read_only=on -c statement_timeout=30000",
    )


def main():
    conn = connect()
    try:
        query = """
            SELECT data, valor AS vazao
            FROM hidro.vazoes_d_cb
            WHERE codigo = %s
              AND data >= DATE '1940-01-01'
              AND data <= DATE '2024-12-31'
            ORDER BY data
        """
        df = pd.read_sql_query(query, conn, params=(CODIGO,))
    finally:
        conn.close()

    if df.empty:
        raise RuntimeError(f"Nenhum registro encontrado para {CODIGO}")
    df["data"] = pd.to_datetime(df["data"])
    df["vazao"] = pd.to_numeric(df["vazao"], errors="coerce")
    df = df.dropna(subset=["data", "vazao"]).drop_duplicates("data")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, sep=";", decimal=",", index=False, encoding="utf-8-sig")
    print(f"Série Guaporé salva em: {OUT}")
    print(f"Registros: {len(df)} | {df.data.min().date()} a {df.data.max().date()} | máximo: {df.vazao.max():.1f} m³/s")


if __name__ == "__main__":
    main()
