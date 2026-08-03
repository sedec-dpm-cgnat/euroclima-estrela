# -*- coding: utf-8 -*-
"""Consolida a exposição municipal preliminar para a curva cota–dano.

A tabela é uma ponte entre a mancha HAND/geométrica e os registros declarados
no Atlas. Ela não estima população, imóveis ou preço de mercado: esses campos
dependem da malha/agregados IBGE 2022, cadastro municipal e custo unitário.
"""
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
TAB = REPO / "06_resultados" / "tabelas"
ATLAS = TAB / "atlas_danos_municipios.csv"
HAND = TAB / "manchas_por_municipio.csv"
OUT = TAB / "base_exposicao_municipal_preliminar.csv"
README = REPO / "06_resultados" / "BASE_EXPOSICAO_MUNICIPAL_PRELIMINAR.md"

if not ATLAS.exists() or not HAND.exists():
    raise FileNotFoundError("São necessários atlas_danos_municipios.csv e manchas_por_municipio.csv")

atlas = pd.read_csv(ATLAS, sep=";", decimal=",", encoding="utf-8")
hand = pd.read_csv(HAND, sep=";", decimal=",", encoding="utf-8")

atlas["Nome_Municipio"] = atlas["Nome_Municipio"].astype(str).str.strip()
hand["municipio"] = hand["municipio"].astype(str).str.strip()

# Agrupa por segurança caso uma nova extração do Atlas traga mais de um
# registro para o mesmo município e recorte.
id_atlas = ["recorte", "Nome_Municipio"]
num_atlas = [c for c in atlas.columns if c not in id_atlas]
atlas[num_atlas] = atlas[num_atlas].apply(pd.to_numeric, errors="coerce").fillna(0.0)
atlas = atlas.groupby(id_atlas, as_index=False)[num_atlas].sum()

base = hand.copy()
recortes = {
    "maio_2024_hidrologico": "mai24",
    "2024_hidrologico": "ano2024",
    "historico_hidrologico": "historico",
}
campos = [
    "eventos_atlas", "afetados_diretos", "outros_afetados",
    "danos_materiais", "prejuizo_publico", "prejuizo_privado",
    "prejuizo_total", "danos_economicos_atlas",
]

for recorte, sufixo in recortes.items():
    a = atlas.loc[atlas["recorte"] == recorte, ["Nome_Municipio"] + campos].copy()
    a = a.rename(columns={"Nome_Municipio": "municipio", **{c: f"{c}_{sufixo}" for c in campos}})
    base = base.merge(a, on="municipio", how="outer")

for c in base.columns:
    if c == "municipio":
        continue
    base[c] = pd.to_numeric(base[c], errors="coerce")

base = base.fillna(0.0)
base["fracao_municipio_inundada_sem_hand"] = np.where(
    base["area_mun_km2"] > 0,
    base["inund_sem_km2"] / base["area_mun_km2"],
    np.nan,
)
base["fracao_municipio_inundada_com_hand"] = np.where(
    base["area_mun_km2"] > 0,
    base["inund_com_km2"] / base["area_mun_km2"],
    np.nan,
)
base["dano_atlas_mai24_por_km2_inund_sem_hand"] = np.where(
    base["inund_sem_km2"] > 0,
    base["danos_economicos_atlas_mai24"] / base["inund_sem_km2"],
    np.nan,
)
base["status_populacao_domicilios_ibge_2022"] = "pendente — não integrado"
base["status_setores_censitarios_ibge_2022"] = "pendente — não integrado"
base["status_custo_reposicao"] = "pendente — SINAPI/CUB-RS/cadastro municipal"
base["classe_base"] = "exposição municipal preliminar; não é curva cota–dano"

base = base.sort_values(["inund_com_km2", "municipio"], ascending=[False, True])
base.to_csv(OUT, sep=";", decimal=",", index=False, encoding="utf-8-sig")

top = base.head(10)[["municipio", "inund_com_km2", "prof_media_com_m", "danos_economicos_atlas_mai24"]]
linhas = [
    "# Base de exposição municipal preliminar",
    "",
    "Produto de integração entre `manchas_por_municipio.csv` e `atlas_danos_municipios.csv`.",
    "",
    f"- Municípios na tabela: **{len(base)}**.",
    "- A área e a profundidade são saídas preliminares HAND/geométricas, não resultados HEC-RAS 1D.",
    "- Os valores do Atlas são perdas declaradas por evento e município; não são dano evitável diretamente atribuível a uma barragem.",
    "- População, domicílios, setores censitários, tipologias construtivas e custo de reposição ainda não foram integrados.",
    "- O campo `dano_atlas_mai24_por_km2_inund_sem_hand` é apenas indicador descritivo e não deve ser usado como função de dano.",
    "",
    "## Maiores áreas preliminares com a medida de referência",
    "",
    "| Município | Área inundada com HAND (km²) | Profundidade média com HAND (m) | Dano Atlas mai/2024 (R$) |",
    "|---|---:|---:|---:|",
]
for _, r in top.iterrows():
    linhas.append(
        f"| {r['municipio']} | {r['inund_com_km2']:.2f} | {r['prof_media_com_m']:.2f} | {r['danos_economicos_atlas_mai24']:,.2f} |".replace(",", "X").replace(".", ",").replace("X", ".")
    )
linhas += [
    "",
    "## Próximo passo",
    "",
    "Cruzar a mancha HEC-RAS 1D com setores censitários IBGE 2022 e, quando disponível, edificações/cadastro municipal. A função de dano deve aplicar profundidade e duração por classe de ativo, usando os valores do Atlas apenas para conferir ordem de grandeza e cobertura.",
    "",
]
README.write_text("\n".join(linhas), encoding="utf-8")
print(f"Base escrita: {OUT}")
print(f"Municípios: {len(base)}")
print(base[["municipio", "inund_com_km2", "danos_economicos_atlas_mai24"]].head(10).to_string(index=False))
