# -*- coding: utf-8 -*-
"""
EUROCLIMA+ / AECID — triagem de alteamento e alternativas sem alteamento.

Este script não é um orçamento de engenharia. Ele consolida o volume acima
do NA atual calculado em ``volume_espera_existentes.csv`` e produz:

1. uma tabela por usina e altura de análise;
2. uma faixa paramétrica de custo, calibrada somente pelo benchmark de custos
   de novos eixos admissíveis já existente no projeto;
3. uma matriz de alternativas que não exigem altear barragens existentes;
4. um relatório Markdown para a tomada de decisão e para o TR.

Por que o custo é paramétrico
-----------------------------
Os dados ANEEL disponíveis informam potência, situação, coordenadas e
concessionário, mas não informam tipo estrutural, altura, comprimento de
crista, fundações, órgãos extravasores, instrumentação ou custo histórico das
usinas. O custo de ``geometria_todos.csv`` é, portanto, usado apenas como
benchmark interno de um novo eixo, e não como custo observado de alteamento.

O benchmark é resumido pelos percentis 25, 50 e 75 de R$ milhões por hm³
armazenado dos eixos admissíveis. Sobre ele aplicam-se fatores de 1,5, 2,0 e
3,0 para representar, respectivamente, alteamento simples, caso-base e
alteamento complexo de barragem existente. Esses fatores são hipóteses de
triagem e devem ser substituídos por orçamento conceitual após inspeção,
batimetria, topobatimetria e anteprojeto.

Limitação central
-----------------
O MDE usado no projeto enxerga a superfície dos reservatórios existentes e
não contém a batimetria abaixo do NA atual. Os volumes ``V_acima_*`` são
limites geométricos superiores para a faixa acima do NA atual; não são ainda
volume de espera operacional. Não se deve converter esta saída diretamente
em volume de deplecionamento preventivo.

Entrada de custo: ``altura_maxima_admissivel.csv`` (custo dos eixos admissíveis,
originado pelo pipeline de geometria; não é custo histórico das UHEs).
Demais entradas: 05_MODELAGEM/06_resultados/tabelas/
Saídas:   05_MODELAGEM/06_resultados/tabelas/ e 05_MODELAGEM/06_resultados/
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TABELAS = ROOT / "06_resultados" / "tabelas"
RESULTADOS = ROOT / "06_resultados"

VOLUME_NECESSARIO_HM3 = 3230.0
DANO_REFERENCIA_MRS = 2500.0  # placeholder já documentado no HANDOFF

# Fatores de complexidade sobre o benchmark de um novo eixo. Não são cotações.
FATORES_ALTEAMENTO = {
    "baixo": 1.5,
    "base": 2.0,
    "alto": 3.0,
}


def ler_csv_projeto(caminho: Path) -> pd.DataFrame:
    """Lê CSV semicolon do projeto, tolerando UTF-8 e arquivos legados."""
    ultimo_erro = None
    for encoding in ("utf-8-sig", "cp1252", "latin1"):
        try:
            return pd.read_csv(caminho, sep=";", decimal=",", encoding=encoding)
        except UnicodeDecodeError as exc:
            ultimo_erro = exc
    raise ultimo_erro  # type: ignore[misc]


def numero(serie: pd.Series) -> pd.Series:
    """Converte números com vírgula decimal ou valores vazios."""
    if serie.dtype == object:
        serie = serie.astype(str)
        # Arquivos do projeto usam vírgula decimal; a saída desta análise pode
        # ser lida novamente com ponto decimal. Só remover separador de milhar
        # quando a própria célula contém vírgula.
        com_virgula = serie.str.contains(",", regex=False)
        serie = serie.where(
            ~com_virgula,
            serie.str.replace(".", "", regex=False).str.replace(",", ".", regex=False),
        )
    return pd.to_numeric(serie, errors="coerce")


def moeda_mrs(valor: float) -> str:
    """Formata R$ milhões em padrão brasileiro, sem falsa precisão."""
    if pd.isna(valor):
        return "—"
    return f"R$ {valor:,.0f} M".replace(",", "X").replace(".", ",").replace("X", ".")


def numero_pt(valor: float, casas: int = 1) -> str:
    if pd.isna(valor):
        return "—"
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def taxa_mrs(valor: float) -> str:
    """Formata taxa em milhões de reais por hm³ com duas casas."""
    return f"{numero_pt(valor, 2)} M R$/hm³"


def benchmark_de_novos_eixos(altura: pd.DataFrame) -> dict[str, float]:
    """Extrai os percentis do custo de novos eixos admissíveis."""
    volume = numero(altura["volume_max_hm3"])
    custo = numero(altura["custo_MRS"])
    taxa = (custo / volume).where((volume > 0) & (custo > 0)).dropna()
    if taxa.empty:
        raise ValueError("Não há eixos admissíveis com volume e custo para benchmark.")
    return {
        "min": float(taxa.min()),
        "p25": float(taxa.quantile(0.25)),
        "mediana": float(taxa.quantile(0.50)),
        "p75": float(taxa.quantile(0.75)),
        "max": float(taxa.max()),
        "n": float(taxa.size),
    }


def consolidar_cenarios(volume: pd.DataFrame, benchmark: dict[str, float]) -> pd.DataFrame:
    """Transforma a tabela larga de volumes em cenários comparáveis."""
    colunas_volume = []
    for coluna in volume.columns:
        encontrado = re.fullmatch(r"V_acima_(\d+)m_hm3", coluna)
        if encontrado:
            colunas_volume.append((int(encontrado.group(1)), coluna))
    colunas_volume.sort()
    if not colunas_volume:
        raise ValueError("Nenhuma coluna V_acima_*m_hm3 foi encontrada.")

    taxas = {
        "baixo": benchmark["p25"],
        "base": benchmark["mediana"],
        "alto": benchmark["p75"],
    }
    registros: list[dict[str, object]] = []
    for _, linha in volume.iterrows():
        for altura_m, coluna in colunas_volume:
            vol = float(numero(pd.Series([linha[coluna]])).iloc[0])
            registro: dict[str, object] = {
                "nome": linha["nome"],
                "potencia_MW": float(numero(pd.Series([linha["potencia_MW"]])).iloc[0]),
                "area_drenagem_km2": float(numero(pd.Series([linha["area_drenagem_km2"]])).iloc[0]),
                "cota_NA_atual_m": float(numero(pd.Series([linha["cota_NA_atual_m"]])).iloc[0]),
                "area_espelho_atual_km2": float(numero(pd.Series([linha["area_espelho_km2"]])).iloc[0]),
                "altura_cenario_m": altura_m,
                "volume_limite_upper_hm3": vol,
                "percentual_do_necessario": 100.0 * vol / VOLUME_NECESSARIO_HM3,
            }
            for faixa, taxa in taxas.items():
                registro[f"custo_{faixa}_MRS"] = vol * taxa * FATORES_ALTEAMENTO[faixa]
            registros.append(registro)
    return pd.DataFrame(registros)


def adicionar_totais(cenarios: pd.DataFrame) -> pd.DataFrame:
    """Adiciona uma linha TOTAL_CASCATA para cada altura."""
    linhas = []
    for altura, grupo in cenarios.groupby("altura_cenario_m", sort=True):
        linha: dict[str, object] = {
            "nome": "TOTAL_CASCATA",
            "potencia_MW": grupo["potencia_MW"].sum(),
            "area_drenagem_km2": pd.NA,
            "cota_NA_atual_m": pd.NA,
            "area_espelho_atual_km2": grupo["area_espelho_atual_km2"].sum(),
            "altura_cenario_m": altura,
            "volume_limite_upper_hm3": grupo["volume_limite_upper_hm3"].sum(),
            "percentual_do_necessario": grupo["volume_limite_upper_hm3"].sum() / VOLUME_NECESSARIO_HM3 * 100.0,
        }
        for faixa in FATORES_ALTEAMENTO:
            linha[f"custo_{faixa}_MRS"] = grupo[f"custo_{faixa}_MRS"].sum()
        linhas.append(linha)
    return pd.concat([cenarios, pd.DataFrame(linhas)], ignore_index=True)


def alternativas() -> pd.DataFrame:
    """Matriz de alternativas sem altear barragens existentes."""
    return pd.DataFrame(
        [
            {
                "prioridade": 1,
                "alternativa": "CAV real + deplecionamento preventivo",
                "tipo": "operacional",
                "implica_alteamento": "não",
                "efeito_esperado": "Mobiliza parte do volume já existente antes de eventos previstos; quantificação ainda bloqueada pela ausência de batimetria.",
                "dados_ou_obra": "Curvas cota×volume, regras de operação, limites de reenchimento, dados ANA/ONS/CERAN e simulação em cascata.",
                "limite_principal": "Não cria volume novo; depende de previsão confiável, coordenação entre operadores e não pode comprometer geração, vazão mínima ou segurança.",
            },
            {
                "prioridade": 2,
                "alternativa": "Operação coordenada de comportas e vertedouros",
                "tipo": "operacional",
                "implica_alteamento": "não",
                "efeito_esperado": "Sincroniza a liberação dos reservatórios com a onda de cheia e evita contribuição atrasada da cascata.",
                "dados_ou_obra": "SINV, regras de decisão, telemetria, previsão hidrometeorológica e validação em Puls/HEC-RAS 1D.",
                "limite_principal": "A capacidade é limitada pelo armazenamento existente e pela descarga segura dos órgãos extravasores.",
            },
            {
                "prioridade": 3,
                "alternativa": "Previsão, alerta e protocolo de resposta",
                "tipo": "gestão de risco",
                "implica_alteamento": "não",
                "efeito_esperado": "Reduz exposição e tempo de resposta mesmo sem reduzir o pico hidrológico.",
                "dados_ou_obra": "Rede de chuva e nível, previsão, sirenes/mensagens, rotas, abrigos, protocolos Defesa Civil–operadores.",
                "limite_principal": "Reduz dano residual; não substitui controle hidráulico nem corrige ocupação em área de risco.",
            },
            {
                "prioridade": 4,
                "alternativa": "Ordenamento territorial e adaptação urbana",
                "tipo": "redução de exposição",
                "implica_alteamento": "não",
                "efeito_esperado": "Evita novas perdas e protege infraestrutura crítica nas cotas de inundação.",
                "dados_ou_obra": "Manchas HEC-RAS 1D, cadastro de edificações, infraestrutura crítica, regras de uso do solo e soluções de retrofit.",
                "limite_principal": "Não reduz o volume da cheia; exige governança municipal e pode demandar reassentamento ou adaptação de imóveis.",
            },
            {
                "prioridade": 5,
                "alternativa": "Medidas naturais e retenções distribuídas na bacia",
                "tipo": "baseada na natureza",
                "implica_alteamento": "não",
                "efeito_esperado": "Retarda escoamento e reduz contribuição de sub-bacias, especialmente em eventos frequentes e moderados.",
                "dados_ou_obra": "Diagnóstico de uso do solo, áreas de várzea, restauração, retenções rurais e monitoramento de desempenho.",
                "limite_principal": "Efeito é distribuído e dependente da escala do evento; não deve ser vendido como substituto isolado para cheia extrema.",
            },
            {
                "prioridade": 6,
                "alternativa": "Barragem seca ou novo eixo admissível",
                "tipo": "obra nova",
                "implica_alteamento": "não",
                "efeito_esperado": "Cria controle dedicado de cheias sem elevar a crista das usinas existentes.",
                "dados_ou_obra": "Revisão dos eixos com restrições de remanso, estudos geológico-geotécnicos, hidrologia, socioambiental e licenciamento.",
                "limite_principal": "Continua sendo uma obra de alto impacto; as restrições da cascata e a comparação de alternativas precisam ser respeitadas.",
            },
        ]
    )


def tabela_resumo(cenarios: pd.DataFrame) -> pd.DataFrame:
    totais = cenarios[cenarios["nome"] == "TOTAL_CASCATA"].copy()
    return totais.sort_values("altura_cenario_m")[[
        "altura_cenario_m",
        "volume_limite_upper_hm3",
        "percentual_do_necessario",
        "custo_baixo_MRS",
        "custo_base_MRS",
        "custo_alto_MRS",
    ]]


def gerar_relatorio(
    cenarios: pd.DataFrame,
    resumo: pd.DataFrame,
    benchmark: dict[str, float],
    alt: pd.DataFrame,
    alternativas_df: pd.DataFrame,
) -> str:
    linhas = []
    for _, linha in resumo.iterrows():
        linhas.append(
            f"| +{int(linha.altura_cenario_m)} m | {numero_pt(linha.volume_limite_upper_hm3, 1)} | "
            f"{numero_pt(linha.percentual_do_necessario, 1)}% | "
            f"{moeda_mrs(linha.custo_baixo_MRS)} | {moeda_mrs(linha.custo_base_MRS)} | "
            f"{moeda_mrs(linha.custo_alto_MRS)} |"
        )

    dez = cenarios[(cenarios["nome"] != "TOTAL_CASCATA") & (cenarios["altura_cenario_m"] == 10)]
    dez = dez.sort_values("volume_limite_upper_hm3", ascending=False).head(3)
    contribuintes = "; ".join(
        f"{linha.nome} ({numero_pt(linha.volume_limite_upper_hm3, 1)} hm³)" for _, linha in dez.iterrows()
    )

    alt_rows = []
    for _, linha in alternativas_df.iterrows():
        alt_rows.append(
            f"| {int(linha.prioridade)} | {linha.alternativa} | {linha.tipo} | {linha.efeito_esperado} |"
        )

    n_admissiveis = int(benchmark["n"])
    return f"""# Avaliação preliminar de alteamento e alternativas

**Projeto:** EUROCLIMA+ / AECID — redução do risco de cheias em Estrela e bacia do Taquari-Antas  
**Estado:** triagem reproduzível, sem valor de orçamento executivo  
**Entradas principais:** `volume_espera_existentes.csv` e `altura_maxima_admissivel.csv` (o custo desta última é o benchmark interno dos eixos admissíveis)

## Resultado executivo

O alteamento das barragens existentes não fecha a lacuna de armazenamento identificada no projeto. Mesmo o cenário geométrico de **+20 m em toda a cascata** soma somente **{numero_pt(float(resumo.iloc[-1].volume_limite_upper_hm3), 1)} hm³**, ou **{numero_pt(float(resumo.iloc[-1].percentual_do_necessario), 1)}%** dos **{numero_pt(VOLUME_NECESSARIO_HM3, 0)} hm³** de referência.

Os números acima são **limites superiores geométricos**, porque o MDE vê a água no NA atual e não contém batimetria abaixo dela. Eles não autorizam concluir que esse volume pode ser operado como volume de espera.

Os maiores contribuintes a +10 m são: **{contribuintes}**. A concentração da capacidade em poucos reservatórios reforça a necessidade de verificar a cascata do rio das Antas e os limites de remanso antes de qualquer estudo de engenharia.

## Faixa paramétrica de custo

| Faixa de alteamento | Volume-limite acima do NA | % dos 3.230 hm³ | Custo triagem baixo | Custo triagem base | Custo triagem alto |
|---:|---:|---:|---:|---:|---:|
{chr(10).join(linhas)}

O benchmark interno foi calculado em **{n_admissiveis} eixos admissíveis**, com custo de novos eixos entre **{taxa_mrs(benchmark['min'])} e {taxa_mrs(benchmark['max'])}**; os percentis 25/50/75 usados na tabela são **{taxa_mrs(benchmark['p25'])} / {taxa_mrs(benchmark['mediana'])} / {taxa_mrs(benchmark['p75'])}**. Sobre essas taxas foram aplicados fatores de alteamento **1,5 / 2,0 / 3,0**.

Esses valores são uma **faixa de sensibilidade**, não uma estimativa de CAPEX. O custo de um alteamento depende principalmente de tipo e estado da barragem, fundações, comprimento de crista, vertedouro, comportas, instrumentação, acessos, desapropriações, realocação de infraestrutura, operação durante a obra, licenciamento e medidas de segurança. Nenhum desses dados está disponível de forma suficiente para orçar as 20 usinas.

O placeholder de dano de **{moeda_mrs(DANO_REFERENCIA_MRS)}** não deve ser usado para validar economicamente o alteamento antes da recalibração do dano evitável por cenário. A comparação correta deve seguir o ICB do Manual de Inventário, depois que o benefício for obtido por simulação hidrológico-hidráulica e não por proporção simples de hm³.

## Como fazer, se a alternativa sobreviver à triagem

1. **Dados e diagnóstico:** obter projeto “as built”, tipo estrutural, cotas, instrumentação, inspeções, curvas cota-área-volume, batimetria e topobatimetria de cada reservatório candidato.
2. **Segurança e hidráulica:** verificar estabilidade, fundação, percolação, borda livre, capacidade do vertedouro, comportas, dissipação, cheias de projeto e propagação do remanso na cascata.
3. **Operação:** definir NA normal e máximo, volume de espera, regra de deplecionamento, reenchimento em até 36 meses quando aplicável, vazões remanescentes, geração perdida e coordenação entre operadores.
4. **Território e ambiente:** mapear a área adicional inundada, imóveis, pontes, estradas, linhas, captações, unidades de conservação, patrimônio e necessidade de reassentamento.
5. **Anteprojeto e decisão:** comparar CAPEX, OPEX, energia, dano evitado, segurança e licenciamento com alternativas sem alteamento; eliminar alternativas dominadas antes do detalhamento.
6. **Execução:** somente após aprovação de segurança e licenciamento definir a sequência construtiva, desvios, rebaixamento temporário, reforço de crista/ombreiras, extravasores e comissionamento.

## Limites que impedem uma decisão executiva hoje

- **Volume:** +10 m = aproximadamente 220 hm³ e +20 m = aproximadamente 635 hm³ na aproximação atual; a ordem de grandeza permanece muito abaixo da necessidade de referência.
- **Dados:** não há batimetria/cotas-volume confiáveis abaixo do NA atual; não há inventário estrutural suficiente para assumir que as barragens aceitam alteamento.
- **Cascata:** o remanso e a inundação de usinas existentes dominam a altura admissível dos eixos novos; esse mesmo cuidado deve ser aplicado a qualquer alteamento.
- **Hidráulica:** sem roteamento em cascata, vertedouro e operação coordenada, volume armazenado não equivale a redução do pico em Estrela.
- **Território:** a área adicional, edificações e infraestrutura por metro ainda precisam ser cruzadas com cadastro e manchas hidráulicas; a tabela atual só informa o espelho atual.
- **Regulação e segurança:** qualquer intervenção em barragem existente exige avaliação específica de segurança, responsabilidades do empreendedor, operação, emergência e licenciamento.

## Alternativas sem alteamento

| Prioridade | Alternativa | Tipo | Efeito esperado |
|---:|---|---|---|
{chr(10).join(alt_rows)}

### Recomendação de sequência

1. Solicitar as curvas cota×volume e regras operativas à ANA, ONS e concessionárias, começando pela CERAN (Monte Claro, Castro Alves e 14 de Julho).
2. Rodar a alternativa de deplecionamento preventivo com CAV real e o SINV somente dentro das alturas fisicamente admissíveis.
3. Avançar em paralelo com previsão/alerta, HEC-RAS 1D, ordenamento territorial e medidas distribuídas, pois essas frentes não dependem de demonstrar viabilidade de alteamento.
4. Só contratar inspeção/anteprojeto de alteamento para um conjunto pequeno de reservatórios que sobreviva à comparação de benefício, segurança, remanso, área adicional e custo.

## Rastreabilidade

- `07_python/14_avaliacao_alteamento.py` — script desta análise.
- `06_resultados/tabelas/volume_espera_existentes.csv` — volumes acima do NA atual; limite geométrico.
- `06_resultados/tabelas/altura_maxima_admissivel.csv` — restrições de remanso dos eixos estudados.
- `06_resultados/tabelas/altura_maxima_admissivel.csv` — custos dos eixos admissíveis usados apenas como benchmark interno de novos eixos.
- `01_dados/cav/geometria_todos.csv` — origem do pipeline geométrico que alimenta o custo dos novos eixos; não é custo histórico das UHEs.
- Manual de Inventário Hidroelétrico e Bacias Hidrográficas, capítulos 4.6, 4.11 e 5.3 — volumes de espera, comparação econômica e simulação final.
"""


def main() -> None:
    volume_path = TABELAS / "volume_espera_existentes.csv"
    altura_path = TABELAS / "altura_maxima_admissivel.csv"
    if not volume_path.exists() or not altura_path.exists():
        raise FileNotFoundError("Saídas-base de volume/altura não encontradas.")

    volume = ler_csv_projeto(volume_path)
    altura = ler_csv_projeto(altura_path)
    benchmark = benchmark_de_novos_eixos(altura)
    cenarios = consolidar_cenarios(volume, benchmark)
    cenarios_com_total = adicionar_totais(cenarios)
    resumo = tabela_resumo(cenarios_com_total)
    alternativas_df = alternativas()

    TABELAS.mkdir(parents=True, exist_ok=True)
    cenarios_com_total.to_csv(
        TABELAS / "avaliacao_alteamento_existentes.csv",
        index=False,
        sep=";",
        decimal=",",
        encoding="utf-8-sig",
    )
    alternativas_df.to_csv(
        TABELAS / "alternativas_sem_alteamento.csv",
        index=False,
        sep=";",
        encoding="utf-8-sig",
    )
    relatorio = gerar_relatorio(cenarios_com_total, resumo, benchmark, altura, alternativas_df)
    (RESULTADOS / "AVALIACAO_ALTEAMENTO_E_ALTERNATIVAS.md").write_text(relatorio, encoding="utf-8")

    print("\nAVALIAÇÃO PRELIMINAR DE ALTEAMENTO")
    print("=" * 70)
    print(resumo.to_string(index=False, formatters={
        "volume_limite_upper_hm3": lambda x: numero_pt(x),
        "percentual_do_necessario": lambda x: numero_pt(x),
        "custo_baixo_MRS": lambda x: moeda_mrs(x),
        "custo_base_MRS": lambda x: moeda_mrs(x),
        "custo_alto_MRS": lambda x: moeda_mrs(x),
    }))
    print(f"\nRelatório: {RESULTADOS / 'AVALIACAO_ALTEAMENTO_E_ALTERNATIVAS.md'}")


if __name__ == "__main__":
    main()
