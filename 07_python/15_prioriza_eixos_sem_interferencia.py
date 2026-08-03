# -*- coding: utf-8 -*-
"""Classifica os eixos propostos pela interferência potencial em barragens existentes.

Esta é uma triagem de escopo, não uma declaração de segurança ou de não interferência.
A confirmação exige perfil hidráulico, remanso, operação e cadastro atualizado das UHEs.
"""
from pathlib import Path
import re
import pandas as pd

RAIZ = Path(r"C:\Users\cassi\OneDrive\Documents\SEDEC\PROJETO_EUROCLIMA")
DEST = RAIZ / "05_MODELAGEM"
TAB = DEST / "06_resultados" / "tabelas"
TAB.mkdir(parents=True, exist_ok=True)


def ler_csv(nome):
    p = DEST / "01_dados" / "cav" / nome
    for enc in ("utf-8", "latin1"):
        try:
            return pd.read_csv(p, sep=";", decimal=",", encoding=enc)
        except UnicodeDecodeError:
            pass
    raise RuntimeError(f"não foi possível ler {p}")


alt = pd.read_csv(TAB / "altura_maxima_admissivel.csv", sep=";", decimal=",")
eixos = ler_csv("eixos_todos.csv")
alt = alt.merge(
    eixos[["codigo", "n_montante", "eixos_montante"]],
    left_on="eixo", right_on="codigo", how="left",
).drop(columns=["codigo"])

alt["altura_max_m"] = pd.to_numeric(alt["altura_max_m"], errors="coerce")
alt["volume_max_hm3"] = pd.to_numeric(alt["volume_max_hm3"], errors="coerce")
alt["area_alagada_km2"] = pd.to_numeric(alt["area_alagada_km2"], errors="coerce")
alt["custo_MRS"] = pd.to_numeric(alt["custo_MRS"], errors="coerce")
alt["eixo_independente"] = alt["n_montante"].fillna(0).eq(0)


def normaliza(s):
    return re.sub(r"[^a-z0-9 ]", "", str(s).lower())


def classifica(r):
    if pd.isna(r.altura_max_m) or r.altura_max_m <= 0:
        return pd.Series(["inviavel", 99, "eliminar da carteira"])
    restr = normaliza(r.restricao)
    if r.eixo == "E02" and r.eixo_independente:
        return pd.Series([
            "candidato_prioritario_baixa_interferencia",
            1,
            "validar em campo e no modelo; restrição listada como estudo",
        ])
    if r.eixo_independente and "operacao" in restr:
        return pd.Series([
            "candidato_independente_com_conflito_operacional",
            2,
            "só avançar após confirmar remanso e regra operativa da usina",
        ])
    if any(x in restr for x in ("monte claro", "14 de julho", "castro alves")):
        return pd.Series([
            "cascata_critica_alta_interferencia",
            3,
            "manter apenas como cenário condicionado à cascata existente",
        ])
    return pd.Series([
        "interferencia_operacional_a_confirmar",
        4,
        "confirmar conflito com a usina indicada antes de dimensionar",
    ])


alt[["classe_interferencia", "ordem_prioridade", "recomendacao"]] = alt.apply(
    classifica, axis=1
)
alt["nao_interferencia_comprovada"] = "não"
alt["observacao_metodologica"] = (
    "triagem baseada na restrição de cota e na topologia atual; não substitui estudo de remanso"
)

cols = [
    "eixo", "area_km2", "cota_eixo_m", "altura_max_m", "volume_max_hm3",
    "area_alagada_km2", "custo_MRS", "restricao", "potencia_restr_MW",
    "eixo_independente", "classe_interferencia", "ordem_prioridade",
    "nao_interferencia_comprovada", "recomendacao", "observacao_metodologica",
]
out = alt[cols].sort_values(["ordem_prioridade", "volume_max_hm3"], ascending=[True, False])
out.to_csv(TAB / "prioridade_eixos_sem_interferencia.csv", index=False, sep=";", decimal=",")

linhas = [
    "# Carteira preliminar de eixos sem interferência direta",
    "",
    "**Status:** triagem de escopo; nenhuma classe abaixo comprova ausência de interferência.",
    "",
    "## Decisão preliminar",
    "",
    "O alteamento das UHEs existentes passa a ser uma análise de sensibilidade. A carteira principal deve investigar novos eixos, começando pelos que não têm conflito operacional comprovado com a cascata existente.",
    "",
    "No conjunto atual, **E02 é o único candidato classificado como prioridade 1**: é independente na topologia extraída e sua restrição aparece como estudo, não como operação. Isso não significa que seja automaticamente viável; significa que é o melhor primeiro alvo para confirmar interferência, remanso, licenciamento, geologia e volume útil.",
    "",
    "E01 e E04 são independentes na topologia, mas já aparecem limitados por usinas em operação. E10, E11 e E12 permanecem cenários de alta interferência, sobretudo pela cascata Monte Claro–Castro Alves–14 de Julho. E05 é inviável na altura admissível atualmente calculada.",
    "",
    "## Critério",
    "",
    "- `eixo_independente`: não possui eixo proposto a montante na tabela de topologia; não equivale a bacia sem usina existente.",
    "- `candidato_prioritario_baixa_interferencia`: prioridade de verificação, não aprovação.",
    "- `interferencia_operacional_a_confirmar`: a restrição registrada aponta usina em operação.",
    "- `cascata_critica_alta_interferencia`: a cota admissível é governada por uma das usinas dominantes da cascata.",
    "",
    "## Próxima verificação obrigatória",
    "",
    "Para cada candidato, levantar NA, curva cota–área–volume, regras de operação e perfil de remanso da usina existente mais próxima. Só depois disso a classe poderá ser convertida em `sem_interferencia_confirmada`, `interferencia_gerenciável` ou `inviável`.",
    "",
    "A tabela reproduzível está em `tabelas/prioridade_eixos_sem_interferencia.csv`.",
]
(DEST / "06_resultados" / "ALTERNATIVAS_EIXOS_SEM_INTERFERENCIA.md").write_text(
    "\n".join(linhas) + "\n", encoding="utf-8"
)
print(out.to_string(index=False))
print("\nSaídas gravadas em", TAB)
