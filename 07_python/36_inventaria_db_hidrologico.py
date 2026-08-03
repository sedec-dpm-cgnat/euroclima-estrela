"""Inventário seletivo do banco hidrológico DPM.

O script é somente leitura. As credenciais devem existir apenas no ambiente:
EUROCLIMA_DB_HOST, EUROCLIMA_DB_PORT, EUROCLIMA_DB_NAME,
EUROCLIMA_DB_USER e EUROCLIMA_DB_PASSWORD.

Execução recomendada com o Python que possui psycopg2 (por exemplo, o Python do
QGIS). O resultado é um CSV sem credenciais em 06_resultados/tabelas/.
"""

from __future__ import annotations

import csv
import os
from pathlib import Path

import psycopg2


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "06_resultados" / "tabelas" / "catalogo_db_hidrologico.csv"

FLOW_CODES = [
    "86305000",  # Castro Alves barramento
    "86448000",  # Monte Claro barramento
    "86470800",  # 14 de Julho barramento
    "86510000",  # Muçum
    "86720000",  # Encantado
    "86745000",  # Forqueta / Passo do Coimbra
    "86580000",  # Guaporé / Santa Lúcia
    "86879300",  # Estrela
    "86870000",  # Lajeado (série curta
]


def connect():
    """Abre uma sessão read-only e limita cada consulta a 30 segundos."""

    missing = [
        name
        for name in (
            "EUROCLIMA_DB_HOST",
            "EUROCLIMA_DB_NAME",
            "EUROCLIMA_DB_USER",
            "EUROCLIMA_DB_PASSWORD",
        )
        if not os.environ.get(name)
    ]
    if missing:
        raise RuntimeError(
            "Variáveis ausentes: " + ", ".join(missing) + ". "
            "Nenhuma credencial deve ser gravada no script."
        )

    return psycopg2.connect(
        host=os.environ["EUROCLIMA_DB_HOST"],
        port=int(os.environ.get("EUROCLIMA_DB_PORT", "5432")),
        dbname=os.environ["EUROCLIMA_DB_NAME"],
        user=os.environ["EUROCLIMA_DB_USER"],
        password=os.environ["EUROCLIMA_DB_PASSWORD"],
        connect_timeout=20,
        options=(
            "-c default_transaction_read_only=on "
            "-c statement_timeout=30000"
        ),
    )


def rows_for(cur, query, params=()):
    cur.execute(query, params)
    return cur.fetchall()


def main() -> None:
    conn = connect()
    try:
        cur = conn.cursor()
        rows = []

        # Estimativas de catálogo: evita varrer as tabelas de séries completas.
        relation_rows = rows_for(
            cur,
            """
            SELECT n.nspname, c.relname, c.reltuples::bigint
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE (n.nspname, c.relname) IN (
                ('hidro', 'vazoes_d_cb'),
                ('hidro', 'chuvas_d_cb'),
                ('dados_xavier', 'grid_ponto'),
                ('dados_xavier', 'clima_diario_grade_2023'),
                ('dados_xavier', 'clima_diario_grade_2024'),
                ('dados_xavier', 'clima_diario_grade_2025'),
                ('atlas_desastres', 'atlas_valores_corrigidos')
            )
            ORDER BY n.nspname, c.relname
            """,
        )
        for schema, table, estimate in relation_rows:
            rows.append(["catalogo", schema, table, "", "", estimate, ""])

        station_rows = rows_for(
            cur,
            """
            SELECT codigo, nomeestacao, nomedorio, municipio,
                   latitude, longitude, areadrenagem, tipodedado
            FROM hidro.inventario
            WHERE codigo = ANY(%s)
            ORDER BY codigo
            """,
            (FLOW_CODES,),
        )
        station_by_code = {str(row[0]): row for row in station_rows}

        series_rows = rows_for(
            cur,
            """
            SELECT codigo, count(*)::bigint, min(data), max(data),
                   min(valor), max(valor)
            FROM hidro.vazoes_d_cb
            WHERE codigo = ANY(%s)
            GROUP BY codigo
            ORDER BY codigo
            """,
            (FLOW_CODES,),
        )
        series_by_code = {str(row[0]): row for row in series_rows}

        qref_rows = rows_for(
            cur,
            """
            SELECT codigo, anoini, anofim, adkm2, qmlt, q95, qmin, qmax
            FROM info_dados_flu_ana.estacoes_flu_qrefsazonal_consistido
            WHERE codigo = ANY(%s)
            ORDER BY codigo
            """,
            (FLOW_CODES,),
        )
        qref_by_code = {str(row[0]): row for row in qref_rows}

        for code in FLOW_CODES:
            meta = station_by_code.get(code, [code, "", "", "", "", "", "", ""])
            series = series_by_code.get(code, [code, "", "", "", "", ""])
            qref = qref_by_code.get(code, [code, "", "", "", "", "", "", ""])
            rows.append(
                [
                    "estacao_vazao",
                    code,
                    meta[1],
                    meta[2],
                    meta[3],
                    series[1],
                    f"{series[2]} a {series[3]}",
                    f"max={series[5]}; area_km2={meta[6]}; "
                    f"qref={qref[1]}-{qref[2]}; qmlt={qref[4]}; q95={qref[5]}",
                ]
            )

        OUT.parent.mkdir(parents=True, exist_ok=True)
        with OUT.open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                ["tipo", "identificador", "nome_ou_schema", "rio_ou_tabela", "municipio", "n_ou_area", "periodo", "observacao"]
            )
            writer.writerows(rows)
        print(f"Inventário salvo em: {OUT}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
