"""Compara as saídas da triagem de batimetria por MDE.

Não transforma nenhuma das duas execuções em batimetria medida. O objetivo é
deixar explícita a sensibilidade ao MDE e a cobertura efetivamente reconstruída.
"""

from __future__ import annotations

import csv
from pathlib import Path

MODELAGEM = Path(__file__).resolve().parents[1]
TABELAS = MODELAGEM / "06_resultados" / "tabelas"
OUT_CSV = TABELAS / "comparacao_mdes_batimetria.csv"
OUT_MD = MODELAGEM / "06_resultados" / "COMPARACAO_MDES_BATIMETRIA.md"


def ler_csv(nome: str) -> dict[str, dict[str, str]]:
    caminho = TABELAS / nome
    for enc in ("utf-8-sig", "cp1252", "latin1"):
        try:
            with caminho.open("r", encoding=enc, newline="") as f:
                return {row["nome"]: row for row in csv.DictReader(f, delimiter=";")}
        except UnicodeDecodeError:
            continue
    raise RuntimeError(f"nao foi possivel ler {caminho}")


def numero(valor: str | None) -> float | None:
    if not valor:
        return None
    try:
        return float(valor.replace(".", "").replace(",", "."))
    except ValueError:
        return None


def fmt(valor: float | None) -> str:
    return "" if valor is None else f"{valor:.2f}".replace(".", ",")


def soma(dados: dict[str, dict[str, str]], campo: str) -> float:
    return sum(numero(r.get(campo)) or 0.0 for r in dados.values())


mdr = ler_csv("batimetria_sintetica_mdr.csv")
anadem = ler_csv("batimetria_sintetica_anadem.csv")
nomes = sorted(set(mdr) | set(anadem))

linhas = []
for nome in nomes:
    a = mdr.get(nome, {})
    b = anadem.get(nome, {})
    v_mdr = numero(a.get("V_submerso_hm3"))
    v_anadem = numero(b.get("V_submerso_hm3"))
    d_mdr = numero(a.get("V_deplec_10m_hm3"))
    d_anadem = numero(b.get("V_deplec_10m_hm3"))
    linhas.append({
        "nome": nome,
        "status_mdr": "reconstruido" if a else "nao_reconstruido",
        "status_anadem": "reconstruido" if b else "nao_reconstruido",
        "V_submerso_mdr_hm3": fmt(v_mdr),
        "V_submerso_anadem_hm3": fmt(v_anadem),
        "delta_V_submerso_anadem_menos_mdr_hm3": fmt(None if v_mdr is None or v_anadem is None else v_anadem - v_mdr),
        "V_deplec_10m_mdr_hm3": fmt(d_mdr),
        "V_deplec_10m_anadem_hm3": fmt(d_anadem),
        "delta_V_deplec_10m_anadem_menos_mdr_hm3": fmt(None if d_mdr is None or d_anadem is None else d_anadem - d_mdr),
        "qualidade_mdr": a.get("qualidade_triagem", ""),
        "qualidade_anadem": b.get("qualidade_triagem", ""),
    })

campos = list(linhas[0]) if linhas else []
with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=campos, delimiter=";")
    w.writeheader()
    w.writerows(linhas)

comuns = sorted(set(mdr) & set(anadem))
md = [
    "# Comparação dos MDEs na triagem de batimetria",
    "",
    "Esta tabela compara execuções do método sintético adaptado para triagem. Não é validação de batimetria nem substitui CAV medida.",
    "",
    f"- Usinas reconstruídas com `mdr.tif`: **{len(mdr)}**.",
    f"- Usinas reconstruídas com ANADEM: **{len(anadem)}**.",
    f"- Usinas reconstruídas nos dois MDEs: **{len(comuns)}**.",
    f"- Volume submerso total estimado no `mdr.tif`: **{soma(mdr, 'V_submerso_hm3'):.1f} hm³**.",
    f"- Volume submerso total estimado no ANADEM: **{soma(anadem, 'V_submerso_hm3'):.1f} hm³**.",
    f"- Deplecionamento de 10 m no `mdr.tif`: **{soma(mdr, 'V_deplec_10m_hm3'):.1f} hm³**.",
    f"- Deplecionamento de 10 m no ANADEM: **{soma(anadem, 'V_deplec_10m_hm3'):.1f} hm³**.",
    "",
    "A diferença de cobertura é tão importante quanto a diferença numérica: o `mdr.tif` não reconstrói vários aproveitamentos neste recorte, enquanto o ANADEM permite reconstruir mais trechos. Os resultados devem ser apresentados como sensibilidade de terreno, com a fonte declarada em cada tabela.",
    "",
    f"Tabela detalhada: `{OUT_CSV.name}`.",
]
OUT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
print(f"gravado: {OUT_CSV}")
print(f"gravado: {OUT_MD}")
print(f"mdr={len(mdr)} anadem={len(anadem)} comuns={len(comuns)}")
