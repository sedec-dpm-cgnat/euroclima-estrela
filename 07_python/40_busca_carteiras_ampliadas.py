# -*- coding: utf-8 -*-
"""
Busca de carteiras ampliadas no rio das Antas, com teste posterior do Forqueta.

O modelo de roteamento é o mesmo da rodada Codex 39. O script executa:

1. busca exaustiva de todas as adições possíveis à carteira ALT-J, excluindo E10;
2. envelope teórico com E10 adicionado à ALT-J, somente para quantificar o limite superior;
3. teste de FQ1 e FQ2 em todas as carteiras de adição à ALT-J;
4. síntese sobre o limiar preliminar de 4.000 m³/s.

As tabelas não selecionam obras. Eixos aninhados ou com interferência longitudinal
continuam condicionados ao HEC-RAS 1D e à auditoria energética/operacional.
"""
from pathlib import Path
import contextlib
import io
import itertools
import runpy

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
D_RES = ROOT / "06_resultados"
D_TAB = D_RES / "tabelas"
D_TAB.mkdir(parents=True, exist_ok=True)
RD = dict(sep=";", decimal=",", encoding="utf-8-sig")
WR = dict(sep=";", decimal=",", encoding="utf-8-sig", index=False)

# Carrega exatamente a implementação consolidada da rodada Antas + Forqueta.
# O stdout é suprimido para deixar a saída desta busca legível; a execução da
# rodada-base continua sendo reproduzível pelo próprio script 39.
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    NS = runpy.run_path(str(ROOT / "07_python" / "39_roteamento_combinado_antas_forqueta.py"))

avalia = NS["avalia"]
AREA = NS["AREA"]
H_ADM = NS["H_ADM"]
Q_LIMIAR = float(NS["Q_LIMIAR"])
PICO_NATURAL = float(NS["PICO_NATURAL"])
Q_EVENTO_2023 = float(NS["Q_EVENTO_2023"])

TODOS = sorted([e for e in AREA if e in H_ADM], key=lambda e: (AREA[e], e))
PRINCIPAIS = [e for e in TODOS if e != "E10"]
ALTJ = list(NS["ALTERNATIVAS"]["ALT-J"])
ADICOES = [e for e in PRINCIPAIS if e not in ALTJ]


def combina(eixos):
    return "+".join(eixos) if eixos else "SEM_OBRA"


def linha(eixos, r, regime, escopo, cenario_forqueta="SEM_FORQUETA"):
    pico = float(r["pico"])
    return {
        "escopo_busca": escopo,
        "eixos_antas": combina(eixos),
        "n_eixos": len(eixos),
        "cenario_forqueta": cenario_forqueta,
        "regra_operativa": regime,
        "pico_natural_estrela_m3s": round(PICO_NATURAL, 1),
        "pico_resultante_estrela_m3s": round(pico, 1),
        "reducao_pico_pct": round(100.0 * (1.0 - pico / PICO_NATURAL), 2),
        "acima_limiar_4000_m3s": round(max(pico - Q_LIMIAR, 0.0), 1),
        "razao_limiar_4000": round(pico / Q_LIMIAR, 3),
        "reducao_vs_evento_2023_pct": round(100.0 * (1.0 - pico / Q_EVENTO_2023), 2),
        "area_controlada_antas_km2": round(float(r["area_antas"]), 1),
        "volume_usado_antas_hm3": round(float(r["vol_antas"]), 1),
        "algum_reservatorio_saturou": bool(r["saturou"]),
        "E10_presente": "E10" in eixos,
    }


def todos_subconjuntos(eixos):
    for n in range(len(eixos) + 1):
        for comb in itertools.combinations(eixos, n):
            yield list(comb)


# 1. Busca principal: todas as 2^5 adições possíveis à ALT-J, barragem seca.
NS["EXCLUIDOS"] = {"E10"}
principal_rows = []
for adicionais in todos_subconjuntos(ADICOES):
    eixos = sorted(set(ALTJ + adicionais), key=lambda e: (AREA[e], e))
    r = avalia(eixos, [], "seca")
    principal_rows.append(linha(eixos, r, "seca", "principal_sem_E10"))
principal = pd.DataFrame(principal_rows).sort_values("pico_resultante_estrela_m3s")
principal.to_csv(D_TAB / "carteiras_ampliadas_antas_principal.csv", **WR)

# 2. Envelope teórico: todas as adições à ALT-J incluindo E10, sem recomendação.
NS["EXCLUIDOS"] = set()
teorico_rows = []
for adicionais in todos_subconjuntos(ADICOES + ["E10"]):
    eixos = sorted(set(ALTJ + adicionais), key=lambda e: (AREA[e], e))
    r = avalia(eixos, [], "seca")
    teorico_rows.append(linha(eixos, r, "seca", "envelope_teorico_com_E10"))
teorico = pd.DataFrame(teorico_rows).sort_values("pico_resultante_estrela_m3s")
teorico.to_csv(D_TAB / "carteiras_ampliadas_antas_envelope_E10.csv", **WR)

# 3. Forqueta em todas as carteiras de adição à ALT-J, em seca e comportas.
NS["EXCLUIDOS"] = {"E10"}
top_eixos = [x.split("+") if x != "SEM_OBRA" else [] for x in principal.eixos_antas]
fq_rows = []
for eixos in top_eixos:
    for nome_fq, fq in (("SEM_FORQUETA", []), ("FQ1", ["FQ1"]), ("FQ2", ["FQ2"])):
        for regime in ("seca", "comportas"):
            r = avalia(eixos, fq, regime)
            row = linha(eixos, r, regime, "adicoes_altj_com_forqueta", nome_fq)
            row["volume_usado_forqueta_hm3"] = round(float(r["vol_forqueta"]), 1)
            row["volume_usado_total_hm3"] = round(float(r["vol_antas"] + r["vol_forqueta"]), 1)
            row["FQ1_FQ2_mutuamente_exclusivos"] = True
            fq_rows.append(row)
fq = pd.DataFrame(fq_rows).sort_values("pico_resultante_estrela_m3s")
fq.to_csv(D_TAB / "carteiras_ampliadas_antas_forqueta.csv", **WR)

best_main = principal.iloc[0]
best_theory = teorico.iloc[0]
best_fq = fq.iloc[0]
below_main = int((principal.pico_resultante_estrela_m3s <= Q_LIMIAR).sum())
below_theory = int((teorico.pico_resultante_estrela_m3s <= Q_LIMIAR).sum())
below_fq = int((fq.pico_resultante_estrela_m3s <= Q_LIMIAR).sum())

md = [
    "# Busca de carteiras ampliadas — Antas + Forqueta",
    "",
    "A busca testa todas as combinações adicionais dos eixos que ficaram fora da carteira ALT-J, usando a mesma triagem de Puls calibrada da rodada Antas + Forqueta. O exutório é Estrela e o limiar de 4.000 m³/s é provisório.",
    "",
    "## Resultado da busca exaustiva",
    "",
    "| Busca | Carteira de menor pico | Pico em Estrela | Redução | Excesso sobre 4.000 m³/s | Carteiras abaixo de 4.000 |",
    "|---|---|---:|---:|---:|---:|",
    f"| Adições à ALT-J, E10 excluído | {best_main.eixos_antas} | {best_main.pico_resultante_estrela_m3s:,.0f} m³/s | {best_main.reducao_pico_pct:.1f}% | {best_main.acima_limiar_4000_m3s:,.0f} m³/s | {below_main} de {len(principal)} |",
    f"| Envelope ALT-J incluindo E10 | {best_theory.eixos_antas} | {best_theory.pico_resultante_estrela_m3s:,.0f} m³/s | {best_theory.reducao_pico_pct:.1f}% | {best_theory.acima_limiar_4000_m3s:,.0f} m³/s | {below_theory} de {len(teorico)} |",
    f"| Adições ALT-J + FQ1/FQ2 | {best_fq.eixos_antas} + {best_fq.cenario_forqueta} ({best_fq.regra_operativa}) | {best_fq.pico_resultante_estrela_m3s:,.0f} m³/s | {best_fq.reducao_pico_pct:.1f}% | {best_fq.acima_limiar_4000_m3s:,.0f} m³/s | {below_fq} de {len(fq)} |",
    "",
    "## Interpretação",
    "",
    "A carteira ampliada reduz a vazão residual em relação à ALT-J, mas os eixos adicionais não eliminam o piso hidrológico da parcela não controlada e introduzem conflitos longitudinais. O envelope com E10 é apenas um limite superior teórico: E10 foi descartado na triagem energética por balanço líquido negativo.",
    "",
    "A busca não substitui a verificação hidráulica. E03, E06, E07 e E08 compartilham a faixa de remanso de Castro Alves; E09, E10, E11 e E12 pertencem à cascata inferior condicionada por Monte Claro/14 de Julho; E01 e E02 têm restrições operacionais próprias. A combinação de todos os eixos não pode ser apresentada como alternativa construtiva sem HEC-RAS 1D, operação e estudo energético.",
    "",
    f"Mesmo no melhor envelope testado, o pico permanece acima do limiar de 4.000 m³/s. A redução necessária para uma condição de não inundação deverá ser procurada na combinação de armazenamento distribuído, operação preventiva, medidas a jusante, zoneamento/alerta e eventualmente novos eixos fora da carteira atual — não apenas na soma de barragens do Antas.",
    "",
    "Arquivos: `tabelas/carteiras_ampliadas_antas_principal.csv`, `tabelas/carteiras_ampliadas_antas_envelope_E10.csv` e `tabelas/carteiras_ampliadas_antas_forqueta.csv`.",
]
(D_RES / "BUSCA_CARTEIRAS_AMPLIADAS_ANTAS_FORQUETA.md").write_text("\n".join(md) + "\n", encoding="utf-8")

print("Carteiras principais:", len(principal), "| abaixo do limiar:", below_main)
print(principal.head(10)[["eixos_antas", "pico_resultante_estrela_m3s", "reducao_pico_pct", "acima_limiar_4000_m3s"]].to_string(index=False))
print("Envelope com E10:", best_theory[["eixos_antas", "pico_resultante_estrela_m3s", "reducao_pico_pct", "acima_limiar_4000_m3s"]].to_dict())
print("Melhor com Forqueta:", best_fq[["eixos_antas", "cenario_forqueta", "regra_operativa", "pico_resultante_estrela_m3s", "reducao_pico_pct", "acima_limiar_4000_m3s"]].to_dict())
