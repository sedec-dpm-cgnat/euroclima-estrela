"""Atualiza a priorização dos eixos usando as alturas longitudinais revisadas."""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

EURO = Path(os.environ["EURO"])
MODELAGEM = EURO / "05_MODELAGEM"
OUT = MODELAGEM / "06_resultados" / "tabelas"
SRC = MODELAGEM / "06_resultados" / "CLAUDE" / "claude_altura_admissivel_revisada.csv"

df = pd.read_csv(SRC, sep=";", decimal=",")


def classifica(row: pd.Series) -> tuple[str, int, str]:
    eixo = row.eixo
    h = float(row.altura_max_m) if pd.notna(row.altura_max_m) else -1.0
    if h <= 0:
        return "inviavel_na_triagem", 5, "altura admissível não positiva"
    if eixo in {"E02", "E04"} and str(row.limitante).startswith("teto"):
        return "candidato_prioritario_baixa_interferencia_triagem", 1, "remanso não limita até 120 m; teto é hipótese de triagem"
    if eixo == "E01":
        return "candidato_em_tributario_com_restricao_operacional", 2, "tributário; restrição operacional precisa ser confirmada"
    if eixo in {"E03", "E06", "E07", "E08"}:
        return "conflito_operacional_castro_alves", 4, "altura limitada pelo remanso de Castro Alves"
    if eixo in {"E09", "E10", "E11", "E12"}:
        return "cascata_critica_alta_interferencia", 3, "altura limitada por usina existente da cascata principal"
    if eixo == "E05":
        return "alternativa_viavel_com_conflito_operacional", 3, "volta a ser viável, mas afeta o remanso de Castro Alves"
    return "revisar_classificacao", 5, "regra não prevista"


classes = df.apply(classifica, axis=1, result_type="expand")
classes.columns = ["classe_revisada", "prioridade", "justificativa"]
df = pd.concat([df, classes], axis=1)
df["nao_interferencia_comprovada"] = "não"
df = df.sort_values(["prioridade", "eixo"])

out = df[[
    "eixo", "estaca_km", "altura_max_m", "volume_max_hm3", "restricao",
    "limitante", "classe_revisada", "prioridade", "justificativa",
    "nao_interferencia_comprovada",
]]
out.to_csv(OUT / "prioridade_eixos_revisada.csv", index=False, sep=";", decimal=",")

md = [
    "# Priorização revisada dos eixos",
    "",
    "Classificação de triagem baseada na posição longitudinal dos aproveitamentos existentes. A expressão “baixa interferência” não significa interferência comprovadamente nula.",
    "",
]
for _, r in out.iterrows():
    md.append(f"- **{r.eixo}** — prioridade {int(r.prioridade)}; {r.classe_revisada}; {r.altura_max_m:.1f} m; {r.volume_max_hm3:.1f} hm³. {r.justificativa}.")
md.append("")
md.append("A adoção da tabela depende da confirmação da conectividade de E02/E04, da ausência de aproveitamentos intermediários e da substituição do teto de 120 m por critérios de engenharia.")
(MODELAGEM / "06_resultados" / "ALTERNATIVAS_EIXOS_REVISADA.md").write_text("\n".join(md) + "\n", encoding="utf-8")
print(out.to_string(index=False))
print("Saídas gravadas em", OUT)
