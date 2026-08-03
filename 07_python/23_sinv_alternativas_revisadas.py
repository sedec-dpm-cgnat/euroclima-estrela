"""Reorganiza alternativas SINV após a revisão longitudinal das alturas."""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

EURO = Path(os.environ["EURO"])
MODELAGEM = EURO / "05_MODELAGEM"
SRC = MODELAGEM / "06_resultados" / "CLAUDE" / "claude_sinv_energetico.csv"
OUT = MODELAGEM / "06_resultados" / "VALIDACAO"
OUT.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(SRC, sep=";", decimal=",")
FRAC = 0.50
ALTERNATIVAS = {
    "E02 isolado": ["E02"],
    "E04 isolado": ["E04"],
    "E02 + E04": ["E02", "E04"],
    "E01 + E02 + E04": ["E01", "E02", "E04"],
    "E05 isolado": ["E05"],
    "E02 + E04 + E05": ["E02", "E04", "E05"],
    "E02 + E04 + E08": ["E02", "E04", "E08"],
    "E12 isolado": ["E12"],
    "E09 + E10": ["E09", "E10"],
}

rows = []
for nome, eixos in ALTERNATIVAS.items():
    sel = df[(df.eixo.isin(eixos)) & (df.frac_espera == FRAC)]
    sel0 = df[(df.eixo.isin(eixos)) & (df.frac_espera == 0.0)]
    if len(sel) != len(eixos) or len(sel0) != len(eixos):
        continue
    rows.append({
        "alternativa": nome,
        "eixos": "+".join(eixos),
        "n_eixos": len(eixos),
        "area_controlada_km2": sel.area_km2.sum(),
        "V_max_hm3": sel.V_max_hm3.sum(),
        "V_espera_hm3": sel.V_espera_hm3.sum(),
        "V_util_hm3": sel.V_util_hm3.sum(),
        "Ef_MWmed": sel.Ef_MWmed.sum(),
        "Ef_sem_espera_MWmed": sel0.Ef_MWmed.sum(),
        "P_MW": sel.P_MW.sum(),
        "custo_MRS": sel.custo_MRS.sum(),
        "ICB_RS_MWh": sel.CT_MRS_ano.sum() * 1e6 / (sel.Ef_MWmed.sum() * 8760),
        "restricoes_montante": "; ".join(f"{r.eixo}: {r.restricao_montante}" for _, r in sel.iterrows()),
    })

out = pd.DataFrame(rows).sort_values("ICB_RS_MWh")
out.to_csv(OUT / "sinv_alternativas_revisadas.csv", index=False, sep=";", decimal=",")
md = [
    "# Alternativas SINV revisadas",
    "",
    "Reorganização da saída SINV do Claude após a revisão das alturas admissíveis. Foi usada fração de 50% do volume máximo como volume de espera, apenas para comparação energética preliminar.",
    "",
]
for _, r in out.iterrows():
    md.append(f"- **{r.alternativa}** — {r.V_max_hm3:.0f} hm³ máximos; {r.V_espera_hm3:.0f} hm³ de espera; {r.Ef_MWmed:.1f} MW médios; ICB preliminar R$ {r.ICB_RS_MWh:.1f}/MWh.")
md.extend([
    "",
    "Os valores absolutos de ICB seguem dependentes de vazão específica, custo e demais parâmetros não calibrados. A tabela serve para ordenar alternativas e não para justificar investimento.",
    "Combinações na mesma cascata, como E09 + E10, não devem ser tratadas como soma independente sem roteamento conjunto e sem representar o remanso entre os eixos.",
])
(OUT / "SINV_ALTERNATIVAS_REVISADAS.md").write_text("\n".join(md) + "\n", encoding="utf-8")
print(out.to_string(index=False))
