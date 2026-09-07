"""Audita as séries diárias candidatas ao gerador Kirsch–Nowak.

Não preenche lacunas e não altera os dados originais. O objetivo é identificar:
  - período bruto e número de registros;
  - duplicidades, datas inválidas, lacunas e 29 de fevereiro;
  - valores negativos e cobertura comum entre os componentes candidatos;
  - distinção entre séries de treinamento e série curta de validação.

Uso:
    python 45_audita_entrada_kirsch_nowak.py
"""

from __future__ import annotations

import csv
from datetime import date, datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ANA = ROOT / "01_dados" / "ana_hidroweb"
DPM = ROOT / "01_dados" / "dpm_db"
OUT = ROOT / "06_resultados" / "VALIDACAO"


SERIES = [
    {
        "id": "antas_mucum_86510000",
        "posto": "86510000",
        "nome": "Muçum / Antas",
        "arquivo": ANA / "86510000_vazao.csv",
        "papel": "treinamento; componente do Antas",
    },
    {
        "id": "antas_encantado_86720000",
        "posto": "86720000",
        "nome": "Encantado / Antas",
        "arquivo": ANA / "86720000_vazao.csv",
        "papel": "treinamento ou validação intermediária; posto aninhado",
    },
    {
        "id": "forqueta_86745000",
        "posto": "86745000",
        "nome": "Passo do Coimbra / Forqueta",
        "arquivo": ANA / "86745000_vazao.csv",
        "papel": "treinamento; componente lateral do Forqueta",
    },
    {
        "id": "guapore_86580000",
        "posto": "86580000",
        "nome": "Santa Lúcia / Guaporé",
        "arquivo": DPM / "86580000_vazao.csv",
        "papel": "treinamento; componente lateral do Guaporé",
    },
    {
        "id": "estrela_86879300",
        "posto": "86879300",
        "nome": "Estrela",
        "arquivo": ANA / "86879300_vazao.csv",
        "papel": "validação do exutório; não recomendado para treinamento longo",
    },
]


def parse_float(value: str) -> float | None:
    value = value.strip().replace(".", "").replace(",", ".")
    # A substituição acima atende aos arquivos brasileiros, mas não deve transformar
    # corretamente um decimal com ponto. Os arquivos locais usam vírgula decimal.
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def load_series(path: Path) -> tuple[list[date], list[float | None], int]:
    dates: list[date] = []
    flows: list[float | None] = []
    invalid_rows = 0
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=";")
        for row in reader:
            raw_date = (row.get("data") or "").strip()
            raw_flow = (row.get("vazao") or "").strip()
            try:
                current = datetime.strptime(raw_date, "%Y-%m-%d").date()
            except ValueError:
                invalid_rows += 1
                continue
            # Local CSVs use comma decimal and no thousands separator.
            try:
                flow = float(raw_flow.replace(",", ".")) if raw_flow else None
            except ValueError:
                flow = None
            dates.append(current)
            flows.append(flow)
    return dates, flows, invalid_rows


def audit(item: dict) -> dict:
    path: Path = item["arquivo"]
    if not path.exists():
        return {**item, "arquivo": str(path), "status": "arquivo ausente"}

    dates, flows, invalid_rows = load_series(path)
    counts: dict[date, int] = {}
    for current in dates:
        counts[current] = counts.get(current, 0) + 1
    unique = sorted(counts)
    duplicates = sum(n - 1 for n in counts.values() if n > 1)
    gaps = 0
    if unique:
        expected = unique[0]
        for current in unique:
            if current > expected:
                gaps += (current - expected).days
            expected = current + timedelta(days=1)
    missing_values = sum(value is None for value in flows)
    negative = sum(value is not None and value < 0 for value in flows)
    leap_days = sum(current.month == 2 and current.day == 29 for current in dates)
    return {
        **item,
        "arquivo": str(path),
        "status": "ok",
        "inicio": unique[0].isoformat() if unique else "",
        "fim": unique[-1].isoformat() if unique else "",
        "registros": len(dates),
        "datas_unicas": len(unique),
        "dias_esperados": (unique[-1] - unique[0]).days + 1 if unique else 0,
        "duplicidades": duplicates,
        "lacunas_dias": gaps,
        "completude_pct": round(100.0 * len(unique) / ((unique[-1] - unique[0]).days + 1), 2) if unique else "",
        "valores_ausentes": missing_values,
        "valores_negativos": negative,
        "29_fevereiro": leap_days,
        "linhas_data_invalida": invalid_rows,
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = [audit(item) for item in SERIES]
    csv_path = OUT / "AUDITORIA_ENTRADA_KIRSCH_NOWAK.csv"
    fields = [
        "id", "posto", "nome", "papel", "arquivo", "status", "inicio", "fim",
        "registros", "datas_unicas", "duplicidades", "lacunas_dias",
        "dias_esperados", "completude_pct",
        "valores_ausentes", "valores_negativos", "29_fevereiro", "linhas_data_invalida",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter=";")
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in fields} for row in rows)

    valid = [row for row in rows if row.get("status") == "ok" and row.get("inicio")]
    training = [row for row in valid if row["id"] != "estrela_86879300"]
    common_start = max(datetime.strptime(row["inicio"], "%Y-%m-%d").date() for row in training)
    common_end = min(datetime.strptime(row["fim"], "%Y-%m-%d").date() for row in training)
    common_days = max(0, (common_end - common_start).days + 1)
    common_years = common_days / 365.0

    md_path = OUT / "AUDITORIA_ENTRADA_KIRSCH_NOWAK.md"
    with md_path.open("w", encoding="utf-8") as handle:
        handle.write("# Auditoria da entrada candidata ao Kirsch–Nowak\n\n")
        handle.write("**Script:** `07_python/45_audita_entrada_kirsch_nowak.py`  \n")
        handle.write("**Regra:** diagnóstico somente; nenhum dado original foi alterado ou preenchido.\n\n")
        handle.write("## Resultado por série\n\n")
        handle.write("| Posto | Nome | Papel | Período | Registros | Lacunas | Completude | 29/02 | Negativos | Status |\n")
        handle.write("|---|---|---|---:|---:|---:|---:|---:|---:|---|\n")
        for row in rows:
            period = f"{row.get('inicio', '')} a {row.get('fim', '')}" if row.get("inicio") else "—"
            handle.write(
                f"| {row['posto']} | {row['nome']} | {row['papel']} | {period} | "
                f"{row.get('registros', '—')} | {row.get('lacunas_dias', '—')} | "
                f"{row.get('completude_pct', '—')}% | "
                f"{row.get('29_fevereiro', '—')} | {row.get('valores_negativos', '—')} | {row.get('status', '—')} |\n"
            )
        handle.write("\n## Janela comum preliminar\n\n")
        handle.write(
            f"Considerando Muçum, Encantado, Forqueta e Guaporé como candidatos de treinamento, "
            f"a janela bruta comum é **{common_start} a {common_end}**, aproximadamente "
            f"**{common_years:.1f} anos de calendário de 365 dias**. Ela ainda precisa ser "
            f"recalculada depois da auditoria de lacunas e consistência; portanto não equivale "
            f"a 66,9 anos completos utilizáveis.\n\n"
        )
        handle.write(
            "A série de Estrela (86879300) é curta e deve ser reservada para validação do "
            "exutório. O gerador exige uma entrada diária harmonizada, sem anos bissextos "
            "e com tratamento documentado das lacunas; este script apenas identifica esses "
            "pontos. Também não resolve a escolha entre vazões de postos aninhados e "
            "incrementos hidrológicos, que deve ser feita pela topologia do modelo.\n"
        )

    print(f"CSV: {csv_path}")
    print(f"MD:  {md_path}")
    print(f"Janela comum bruta dos quatro candidatos: {common_start} a {common_end} ({common_years:.1f} anos de 365 dias)")


if __name__ == "__main__":
    main()
