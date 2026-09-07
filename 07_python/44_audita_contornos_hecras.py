# -*- coding: utf-8 -*-
"""
Auditoria dos contornos hidrológicos para a primeira rodada do HEC-RAS 1D.

Este script não monta nem executa um projeto HEC-RAS. Ele verifica se os
hidrogramas e as áreas usados como condições de contorno são compatíveis entre
si, evitando que um hidrograma já calculado em Estrela seja somado novamente
como afluência lateral ou usado no lugar de um efluente de barragem.

Produtos:
  03_HECRAS/contornos_preliminares/manifesto_contornos_hecras.csv
  03_HECRAS/contornos_preliminares/README.md
  06_resultados/VALIDACAO/AUDITORIA_CONTORNOS_HECRAS.md

Os produtos são de preparação e auditoria. Não substituem as séries
subdiárias, as seções topobatimétricas, as pontes cadastradas ou a curva-chave.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
CLAUDE = ROOT / "06_resultados" / "CLAUDE"
VALID = ROOT / "06_resultados" / "VALIDACAO"
OUT = ROOT / "03_HECRAS" / "contornos_preliminares"
OUT.mkdir(parents=True, exist_ok=True)
VALID.mkdir(parents=True, exist_ok=True)


def read_csv(name: str) -> pd.DataFrame:
    return pd.read_csv(CLAUDE / name, sep=";", decimal=",", encoding="utf-8")


def fmt(value: float, digits: int = 1) -> str:
    if not np.isfinite(value):
        return "—"
    return f"{value:,.{digits}f}".replace(",", "X").replace(".", ",").replace("X", ".")


contornos = pd.read_csv(
    CLAUDE / "claude_hecras_contornos.csv",
    sep=";",
    decimal=",",
    encoding="utf-8",
)
c4 = read_csv("claude_c4_hidrogramas_calibrado.csv")
c01 = pd.read_csv(
    ROOT / "06_resultados" / "tabelas" / "hidrogramas_cascatas_comportas_triagem.csv",
    sep=";",
    decimal=",",
    encoding="utf-8",
)
c01 = c01[c01["cenario"].eq("C01")].copy()


montante = contornos.loc[contornos["posicao"].eq("montante"), "area_drenagem_km2"]
jusante = contornos.loc[contornos["posicao"].eq("jusante"), "area_drenagem_km2"]
laterais = contornos.loc[contornos["posicao"].eq("lateral")]
area_montante = float(montante.iloc[0]) if len(montante) else np.nan
area_jusante = float(jusante.iloc[0]) if len(jusante) else np.nan
area_laterais = float(laterais["area_drenagem_km2"].sum())
area_fecharia = area_montante + area_laterais
deficit_area = area_jusante - area_fecharia

c4["t_h"] = pd.to_numeric(c4["t_h"], errors="coerce")
c4["Q_natural"] = pd.to_numeric(c4["Q_natural"], errors="coerce")
c01["tempo_h"] = pd.to_numeric(c01["tempo_h"], errors="coerce")
c01["Q_resultante_Estrela_m3s"] = pd.to_numeric(
    c01["Q_resultante_Estrela_m3s"], errors="coerce"
)

dt_c4 = float(c4["t_h"].diff().dropna().median())
q_c4_max = float(c4["Q_natural"].max())
q_c01_max = float(c01["Q_resultante_Estrela_m3s"].max())

manifesto = pd.DataFrame(
    [
        {
            "componente": "montante",
            "plano": "HEC-00",
            "situacao": "hidrograma calibrado disponível",
            "arquivo_base": "06_resultados/CLAUDE/claude_c4_hidrogramas_calibrado.csv",
            "uso": "candidato a entrada no limite de 19.440 km²",
            "restricao": "confirmar que o domínio começa exatamente na seção de 19.440 km²",
        },
        {
            "componente": "montante",
            "plano": "HEC-01",
            "situacao": "efluente nodal ainda não disponível",
            "arquivo_base": "06_resultados/CLAUDE/claude_c4_roteamento_calibrado.csv",
            "uso": "não usar o pico agregado de Estrela como efluente de E02/E04",
            "restricao": "gerar séries efluentes por nó para E02 e E04",
        },
        {
            "componente": "laterais",
            "plano": "HEC-00",
            "situacao": "áreas localizadas; séries não consolidadas",
            "arquivo_base": "06_resultados/CLAUDE/claude_hecras_contornos.csv",
            "uso": "Forqueta e demais tributários entram concentrados nas confluências",
            "restricao": "obter ou transpor hidrogramas com defasagem explícita",
        },
        {
            "componente": "jusante",
            "plano": "HEC-00",
            "situacao": "normal depth preliminar",
            "arquivo_base": "06_resultados/CLAUDE/claude_hecras_contornos.csv",
            "uso": "apenas teste de sensibilidade",
            "restricao": "curva-chave, nível observado ou domínio estendido",
        },
        {
            "componente": "HEC-01",
            "plano": "HEC-01",
            "situacao": "triagem antiga disponível, não calibrada",
            "arquivo_base": "06_resultados/tabelas/hidrogramas_cascatas_comportas_triagem.csv",
            "uso": "controle de ordem de grandeza, não entrada final",
            "restricao": "substituir por C1/C4 com efluentes nodais calibrados",
        },
    ]
)
manifesto.to_csv(OUT / "manifesto_contornos_hecras.csv", index=False, sep=";", encoding="utf-8")

md = f"""# Auditoria dos contornos do HEC-RAS 1D

**Data da auditoria:** {date.today().strftime("%d/%m/%Y")}  
**Status:** preparação — nenhum plano HEC-RAS foi executado.

## Resultado principal

Os insumos geométricos do trecho estão organizados, mas os hidrogramas ainda não
formam uma entrada hidráulica final. O arquivo calibrado de C4 contém o
hidrograma natural associado à seção de análise de **19.440 km²**, com pico de
**{fmt(q_c4_max, 0)} m³/s** e passo temporal de **{fmt(dt_c4, 1)} h**. Ele pode
ser candidato à condição de montante do HEC-00 somente se o limite montante do
modelo coincidir exatamente com essa seção.

O C01 disponível para E02+E04 pertence à rodada de triagem antiga. Seu pico
resultante em Estrela é **{fmt(q_c01_max, 0)} m³/s**, mas o próprio relatório
classifica essa série como baseada em hidrograma sintético, tempo de viagem fixo
e parâmetros de comportas não calibrados. Ela deve ser usada apenas para conferir
ordem de grandeza, não como condição final do HEC-01.

## Fechamento espacial das áreas

| Componente | Área (km²) |
|---|---:|
| Limite de montante informado | {fmt(area_montante, 1)} |
| Soma das seis laterais localizadas | {fmt(area_laterais, 1)} |
| Montante + laterais | {fmt(area_fecharia, 1)} |
| Limite de jusante informado | {fmt(area_jusante, 1)} |
| Diferença a explicar | {fmt(deficit_area, 1)} |

A diferença de **{fmt(deficit_area, 1)} km²** precisa ser explicada antes da
calibração: pode representar áreas não cadastradas, diferença entre seções de
controle ou inconsistência de áreas. Somar todas as laterais ao hidrograma de
19.440 km² sem fechar esse balanço pode duplicar contribuição.

## Decisão de modelagem registrada

1. **HEC-00:** usar o hidrograma calibrado como entrada de montante apenas após
   confirmar a seção de 19.440 km²; inserir as laterais com séries próprias ou
   transpostas e testar a condição de jusante.
2. **HEC-01:** não usar `Q_resultante_Estrela` do C01 como entrada de montante.
   É necessário gerar os efluentes de E02 e E04 no ponto de cada nó, depois
   propagá-los até o limite do HEC-RAS sem dupla contagem.
3. **Forqueta:** entra como afluência lateral a montante de Estrela, não como
   parcela já contida no hidrograma de montante, salvo se a desagregação da
   bacia demonstrar o contrário.
4. **Guaporé:** sua contribuição está a montante do ponto de análise e precisa
   ser retirada da parcela residual antes de qualquer cenário GU1.

## Insumos que destravam a execução

- séries efluentes nodais calibradas para E02 e E04;
- série de vazão lateral do Forqueta com defasagem e tratamento da lacuna de
  novembro de 2023;
- confirmação da área correspondente ao limite de 19.440 km²;
- seções topobatimétricas, pontes, diques e curva-chave/nível de jusante;
- definição da representação do Guaporé na decomposição do hidrograma.

O manifesto auditável está em
`03_HECRAS/contornos_preliminares/manifesto_contornos_hecras.csv`.
"""
(VALID / "AUDITORIA_CONTORNOS_HECRAS.md").write_text(md, encoding="utf-8")

readme = """# Contornos preliminares do HEC-RAS 1D

Este diretório contém o manifesto da preparação dos casos HEC-00 e HEC-01.
Ainda não há arquivos nativos de projeto, geometria ou plano HEC-RAS porque
faltam seções topobatimétricas, cadastro de pontes, dados de jusante e séries
efluentes por nó.

O produto principal é `manifesto_contornos_hecras.csv`. A auditoria completa,
com o fechamento de áreas e as regras contra dupla contagem, está em:

`06_resultados/VALIDACAO/AUDITORIA_CONTORNOS_HECRAS.md`

O caso prioritário continua sendo:

- HEC-00: situação atual, sem novas barragens;
- HEC-01: E02 + E04, após gerar os efluentes nodais calibrados.

Não usar as séries agregadas em Estrela como se fossem simultaneamente entrada
de montante e afluências laterais.
"""
(OUT / "README.md").write_text(readme, encoding="utf-8")

print(f"Auditoria gravada em {VALID / 'AUDITORIA_CONTORNOS_HECRAS.md'}")
print(f"Manifesto gravado em {OUT / 'manifesto_contornos_hecras.csv'}")
print(f"Area montante + laterais: {area_fecharia:.1f} km2")
print(f"Area jusante: {area_jusante:.1f} km2")
print(f"Diferenca a explicar: {deficit_area:.1f} km2")
print(f"Pico C4 natural: {q_c4_max:.1f} m3/s")
print(f"Pico C01 triagem: {q_c01_max:.1f} m3/s")
