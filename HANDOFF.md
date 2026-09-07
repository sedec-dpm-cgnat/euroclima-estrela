# HANDOFF — estado do trabalho e como continuar

**Projeto:** EUROCLIMA+ / AECID — estudo integrado de alternativas para redução do risco de inundação em Estrela/RS (bacia Taquari‑Antas)
**Repositório:** `github.com/sedec-dpm-cgnat/euroclima-estrela` (privado)
**Pasta local:** `C:\Users\cassi\OneDrive\Documents\SEDEC\PROJETO_EUROCLIMA\05_MODELAGEM`
**Última atualização:** 30/07/2026

> Documento de passagem. Descreve o que foi feito, o que ficou pendente, quais números são confiáveis e quais não são.

---

## 1. Contexto em uma página

A SEDEC/MIDR vai contratar um estudo técnico (€ 273.875 de assistência técnica, 7 trimestres) dentro do programa EUROCLIMA+. O projeto tem três frentes: governança (Haskoning/NL, € 250 mil), financiamento climático (Eco Ltd/UK, € 200 mil) e **este componente técnico** (AECID, € 300 mil).

O objeto é mapear risco, modelar hidrodinamicamente e **analisar alternativas** de redução de danos por inundação em Estrela/RS, tendo como evento de referência a cheia de 2024 no Taquari.

A pergunta que motivou toda a modelagem: **quantas barragens, de que porte e com que volume, evitariam os danos de uma cheia como a de 2024?**

Bacia de drenagem em Estrela: **19.440 km²**. Bacia Taquari‑Antas total: 23.618 km².

---

## 2. Ambiente de execução

Python — usar o interpretador do QGIS (tem GDAL, geopandas, scipy):

```bash
export QGIS="C:/Program Files/QGIS 3.44.11"
export QPY="$QGIS/apps/Python312/python.exe"
export PROJ_LIB="$QGIS/share/proj"; export PROJ_DATA="$QGIS/share/proj"
export GDAL_DATA="$QGIS/share/gdal"; export PATH="$QGIS/bin:$PATH"
export EURO="C:/Users/cassi/OneDrive/Documents/SEDEC/PROJETO_EUROCLIMA"
export ESP="$EURO/Documentos EUROCLIMA+/Espanha"
export GIS="$ESP/GIS"; export SHP="$GIS/shapefiles"; export KMZ="$ESP/kmz"
```

R — `C:/Program Files/R/R-4.5.3/bin/x64/Rscript.exe`. Pacotes necessários já instalados (`data.table`, `ggplot2`, `sf`, `terra`, `scales`, `patchwork`).

Também instalados na máquina: HEC‑RAS 6.3.1 e 7.0.1, HEC‑HMS 4.11 e 4.13, QGIS 3.30 e 3.44.

---

## 3. O que já está pronto

### 3.1 Documentos

| Arquivo | Conteúdo |
|---|---|
| `06_resultados/TR_MINUTA_REV0B.docx` | Minuta do Termo de Referência. A REV_0A tinha, da seção 3.2 em diante, o plano de gerenciamento de **outro projeto** (dashboard ANA/COMUC/IICA, consultor Ramon Torres). Isso foi removido e substituído pelo escopo real, amarrado às atividades AC1.1–AC3.1 do Macro Logframe. |
| `06_resultados/NOTA_TECNICA_PRELIMINAR_BARRAGENS.docx` | Nota técnica sobre o potencial das barragens. Proposta como ANEXO VII do TR. |
| `06_resultados/ANALISE_DE_ALTERNATIVAS_RESERVATORIOS.docx` | Análise de 160 alternativas de reservatório. |
| `PLANO_DE_ACAO.docx` | Plano em 5 fases para fechar o TR e as simulações. |

### 3.2 Pipeline geoespacial (`07_python/`)

Todos os scripts leem os eixos direto do KMZ e são **genéricos para N eixos** — basta acrescentar eixos ao arquivo e rodar de novo.

| Script | Função | Estado |
|---|---|---|
| `02_bacias_barragens.py` | Versão inicial, 3 eixos em shapefile | superado por `10_` |
| `05_bacias_kmz.py` | Delineação a partir de KMZ | superado por `10_` |
| `06_geometria_barragens.py` | Perfil transversal, crista, aterro, custo | ok |
| `07_extrai_euroclima_kmz.py` | Extrai todas as feições do EUROCLIMA.kmz | ok |
| `08_manchas_hand.py` | Manchas de inundação por HAND + Manning | ok |
| `09_perfil_divisao_quedas.py` | Perfil longitudinal do talvegue | ok |
| **`10_eixos_cascata.py`** | **Pipeline principal**: lê N eixos, ancora na BHO, delineia, CAV, geometria, custo, topologia das cascatas, numeração lógica montante→jusante | ok |
| `11_barragens_existentes.py` | Baixa ANEEL SIGA + empreendimentos em estudo, filtra pela bacia | ok |
| `12_altura_maxima_admissivel.py` | Altura máxima de cada eixo sem afogar aproveitamento de montante | ok |
| `13_volume_espera_existentes.py` | Volume ganho por alteamento dos reservatórios existentes | ok, com ressalva (ver §5) |
| `14_batimetria_sintetica.py` | Triagem de geometria submersa inspirada em Domeneghetti (2016) | executado; 6/20 reconstruídos, não calibrado |
| `15_prioriza_eixos_sem_interferencia.py` | Classificação preliminar de eixos por interferência em UHEs existentes | ok, triagem |
| `16_extrai_atlas_danos.py` | Extração municipal do Atlas por recorte hidrológico | ok |
| `17_organiza_gis.py` | GeoPackage mestre e exportações SHP/KMZ | ok |
| `18_prepara_anadem.py` | Recorte alinhado do ANADEM para o contexto da bacia | ok, controle de sensibilidade |
| `19_compara_mdes_batimetria.py` | Comparação das saídas de batimetria sintética por MDE | ok |
| `20_audita_restricoes_longitudinais.py` | Auditoria independente da ordem geométrica dos barramentos | ok |
| `21_prioriza_eixos_revisada.py` | Priorização com alturas admissíveis revisadas | ok, triagem |
| `22_figura_divisao_quedas_revisada.py` | Figura geral e zooms legíveis da divisão de quedas revisada | ok |
| `23_sinv_alternativas_revisadas.py` | Reorganização das alternativas SINV após a revisão | ok, triagem |
| `24_importa_cav_snirh.py` | Importação reproduzível das CAV oficiais do SNIRH/ANA | ok, 3 UHEs |
| `25_compara_cav_snirh_e_deplecionamento.py` | Comparação CAV × MDE e volume de espera por deplecionamento | ok, 3 UHEs |
| `26_figura_cav_snirh.py` | Figura SVG das curvas CAV oficiais | ok |
| `27_ajusta_cav_eixos_novos.py` | Densificação PCHIP e ajuste polinomial das CAVs dos 12 eixos novos | ok, triagem |
| `28_consolida_base_cavs.py` | Base única de CAVs oficiais e derivadas do MDE natural | ok, 15 curvas |
| `29_valida_cavs.py` | Verificação de monotonicidade e consistência dV/dc ≈ área | ok |
| `30_inventario_cascatas_comportas.py` | Rede imediata, caminhos e cenários para roteamento conjunto de barragens com comportas | ok, preparação hidráulica |
| `31_roteamento_cascata_comportas.py` | Sensibilidade de roteamento conjunto, conservação de massa, saturação e galgamento | executado, não calibrado |
| `claude_01_sinv_energetico.py` | SINV preliminar nas alturas revisadas | ok, não calibrado |
| `claude_02_divisao_quedas.py` | Perfil longitudinal e figura de divisão de quedas | ok, figura original precisa de legenda revisada |
| `claude_03_altura_admissivel_revisada.py` | Altura por posição longitudinal dos barramentos | ok, validado independentemente |

### 3.3 Análises em R (`02_R/`)

| Script | Função |
|---|---|
| `00_config.R` | Parâmetros da bacia, eixos, limiares. **Ponto único de calibração.** |
| `01_baixa_dados_ana.R` | Baixa séries da ANA/HidroWeb (endpoint SOAP legado). **Nunca foi executado.** |
| `02_volume_amortecimento.R` | Volume de amortecimento necessário, piso físico, altura requerida |
| `03_roteamento_puls.R` | Roteamento de reservatório (Puls), cenários convencional × barragem seca |
| `04_cenarios_kmz.R` | Comparação KMZ × shapefile |
| `05_analise_alternativas.R` | 160 alternativas, EAD, custo‑benefício |
| `06_sensibilidade.R` | Sensibilidade ao dano de referência |
| `07_comportas_uso_multiplo.R` | Vertedouro com comportas + geração hidrelétrica |

---

## 4. Resultados principais

### 4.1 Os 12 eixos (numerados montante→jusante)

Fonte: `EUROCLIMA-rev.kmz`. Delineação D8 sobre `Fdr.tif` (28,6 m), ancorada na BHO/ANA — aderência entre −0,8% e +0,1%.

| Código | Área controlada | Incremental | Cota do eixo | Eixos a montante |
|---|---:|---:|---:|---:|
| E01 | 2.549 km² | 2.549 | 72,5 m | 0 |
| E02 | 3.591 km² | 3.591 | 293,0 m | 0 |
| E03 | 3.772 km² | 181 | 149,5 m | 1 |
| E04 | 7.498 km² | 7.498 | 239,0 m | 0 |
| E05 | 7.923 km² | 425 | 167,0 m | 1 |
| E06 | 8.159 km² | 661 | 149,5 m | 2 |
| E07 | 8.174 km² | 676 | 149,5 m | 3 |
| E08 | 11.951 km² | 862 | 148,0 m | 6 |
| E09 | 12.330 km² | 1.241 | 106,0 m | 7 |
| E10 | 12.778 km² | 1.689 | 71,5 m | 8 |
| E11 | 15.457 km² | 1.819 | 57,5 m | 10 |
| E12 | 15.760 km² | 2.122 | 47,0 m | 11 |

Eixos independentes (sem outro a montante): **E01, E02, E04**.

### 4.2 Quanto volume é necessário

Para não ultrapassar 4.000 m³/s em Estrela (limiar estimado de dano relevante), no evento de referência: **3.230 hm³**.

**Piso físico**: E12 controla 81,1% da bacia. Os 18,9% restantes (3.680 km²) produzem sozinhos ~3.400 m³/s. Nenhum arranjo de barragens nesses eixos reduz o pico abaixo disso.

### 4.3 O arranjo operacional domina

| Arranjo | Melhor redução obtida |
|---|---:|
| Barragem convencional (vertedouro de soleira livre) | 0 a 16% — satura e transfere a cheia |
| Barragem seca (*dry dam*) | 54% |
| **Vertedouro com comportas + deplecionamento preventivo** | **63,1%** — e ainda gera energia |

Com comportas, os melhores arranjos em E12 (antes da restrição de remanso, ver §4.5):

| Altura | NA normal | Vol. espera | Redução | Potência | Energia | Custo | VPL líq. | B/C |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 120 m | 84 m | 3.289 hm³ | 63,1% | 499 MW | 1.986 GWh | R$ 3.460 M | R$ 8.616 M | 3,21 |
| 110 m | 66 m | 3.310 hm³ | 63,1% | 392 MW | 1.561 GWh | R$ 2.873 M | R$ 7.602 M | 3,35 |
| 100 m | 45 m | 3.163 hm³ | 63,1% | 240 MW | 1.064 GWh | R$ 2.350 M | R$ 6.222 M | 3,35 |

Alerta operacional: NA normal acima de ~0,85 da altura produz **redução negativa** — o reservatório satura cedo e a liberação atrasada dessincroniza com a contribuição da área livre.

### 4.4 A bacia já está tomada

83 aproveitamentos na bacia: **49 em operação, 34 em estudo** (ANEEL SIGA + cadastro de empreendimentos em estudo). Cascata do rio das Antas:

| Usina | Potência | Área drenagem | Cota |
|---|---:|---:|---:|
| Monte Claro | 130 MW | 12.414 km² | 132,5 m |
| Castro Alves | 130 MW | 7.700 km² | 236,0 m |
| 14 de Julho | 100 MW | 12.877 km² | 104,5 m |
| Foz do Prata | 49 MW | 3.776 km² | 171,3 m |

Todos os 12 eixos ficam entre **1,6 e 10 km** de alguma usina existente.

### 4.5 Restrição de remanso — o achado que muda tudo

Critério do item 4.6.1 do Manual de Inventário: o NA do novo reservatório não pode afogar a restituição do aproveitamento imediatamente a montante. Com 2 m de folga:

| Eixo | Altura admissível | Volume admissível | Volume a 90 m | Perda | Restrição |
|---|---:|---:|---:|---:|---|
| E12 | **55,5 m** | 978 hm³ | 2.904 hm³ | 66% | 14 de Julho |
| E11 | **45,0 m** | 400 hm³ | 2.126 hm³ | 81% | 14 de Julho |
| E10 | **59,0 m** | 481 hm³ | 1.326 hm³ | 64% | Monte Claro |
| E09 | **63,3 m** | 377 hm³ | 839 hm³ | 55% | Foz do Prata |
| E04 | **27,3 m** | 125 hm³ | 1.164 hm³ | 89% | Jararaca |
| E01 | **56,4 m** | 129 hm³ | 405 hm³ | 68% | Vale do Leite |
| E05 | inviável | — | 295 hm³ | — | Monte Cuco |

**Volume total mobilizável respeitando a cascata: ~2.565 hm³** — contra 3.230 hm³ necessários.

Os arranjos de 90–120 m que apareciam como melhores **afogariam a UHE 14 de Julho**.

### 4.5.1 Revisão longitudinal das alturas admissíveis — atualização do Claude

O critério anterior foi auditado e corrigido. A comparação apenas por área de drenagem e cota podia inverter a ordem entre barramentos com áreas semelhantes. O perfil geométrico do talvegue, com estaca crescente de montante para jusante, reproduz a ordem espacial e foi conferido por `20_audita_restricoes_longitudinais.py`.

| Eixo | Restrição revisada | Altura revisada | Volume revisado |
|---|---|---:|---:|
| E02 | Passo do Meio | 120,0 m* | 1.377 hm³ |
| E04 | Serra dos Cavalinhos II | 120,0 m* | 2.211 hm³ |
| E05 | Castro Alves | 67,0 m | 91 hm³ |
| E03/E06/E07 | Castro Alves | 84,5 m | 152/338/386 hm³ |
| E08 | Castro Alves | 86,0 m | 621 hm³ |
| E09 | Monte Claro | 24,5 m | 60 hm³ |
| E10 | 14 de Julho | 31,0 m | 70 hm³ |
| E01 | Cotiporã | 63,6 m | 172 hm³ |
| E11/E12 | 14 de Julho | 45,0/55,5 m | 400/978 hm³ |

\* 120 m é teto técnico de triagem, não altura recomendada. As curvas geométricas disponíveis terminam nesse limite e ainda faltam geotecnia, custos, licenciamento, conectividade hidráulica e confirmação de aproveitamentos intermediários.

A auditoria reproduziu as mesmas 7 usinas operacionais válidas como restrições. O volume positivo revisado sobe de aproximadamente 2.601 hm³ para 6.855 hm³, mas esse valor deve ser usado somente como cenário de triagem até a validação dos dois eixos prioritários. A decisão de integração detalhada está em `06_resultados/VALIDACAO/DECISAO_INTEGRACAO_REVISAO_ALTURAS.md`; a nova priorização está em `06_resultados/tabelas/prioridade_eixos_revisada.csv`.

### 4.6 Alteamento dos reservatórios existentes

Volume ganho ao elevar o NA de **toda** a cascata (20 usinas ≥ 15 MW):

| Alteamento | Volume ganho | % do necessário |
|---:|---:|---:|
| +5 m | 80 hm³ | 2,5% |
| +10 m | 220 hm³ | 6,8% |
| +15 m | 401 hm³ | 12,4% |
| +20 m | 635 hm³ | 19,7% |

Maiores contribuintes a +10 m: 14 de Julho (82 hm³), Castro Alves (39 hm³), Da Ilha (17 hm³). Área de espelho atual de toda a cascata: apenas **11,1 km²** — são reservatórios de vale encaixado, a fio d'água.

**Conclusão:** alteamento não resolve. Mesmo elevando 20 m em 20 usinas, chega‑se a 20% do volume necessário — a um custo que seria de bilhões (reforço estrutural, comportas, realocação da infraestrutura de borda em 20 sítios).

**Atualização — avaliação preliminar de custos e alternativas (30/07/2026):** foi criado `07_python/14_avaliacao_alteamento.py`, que gera `06_resultados/AVALIACAO_ALTEAMENTO_E_ALTERNATIVAS.md`, `06_resultados/tabelas/avaliacao_alteamento_existentes.csv` e `06_resultados/tabelas/alternativas_sem_alteamento.csv`. A faixa paramétrica, baseada no custo interno de novos eixos admissíveis e em fatores explícitos de complexidade do alteamento, resulta em aproximadamente **R$ 634 M no caso-base para +10 m** e **R$ 1.831 M para +20 m**. Isso é triagem, não orçamento executivo: faltam tipo/estado estrutural, projetos as built, vertedouros, fundações, área adicional inundada, infraestrutura afetada, operação durante a obra e licenciamento.

As alternativas sem alteamento foram ordenadas por prioridade: (1) CAV real + deplecionamento preventivo; (2) operação coordenada de comportas/vertedouros; (3) previsão, alerta e protocolo de resposta; (4) ordenamento territorial e adaptação urbana; (5) medidas naturais e retenções distribuídas; (6) barragem seca ou novo eixo admissível. A primeira continua bloqueada pela ausência de batimetria/cotas×volume abaixo do NA atual.

**Atualização de escopo:** o alteamento fica em segundo plano como sensibilidade. A carteira principal passa a priorizar novos eixos com baixa interferência da cascata existente na triagem: E02 e E04 são os candidatos prioritários; E01 é alternativa em tributário; E05 volta a ser viável, mas condicionado a Castro Alves; E03/E06/E07/E08, E09/E10 e E11/E12 permanecem condicionados às usinas existentes. A classificação revisada está em `06_resultados/tabelas/prioridade_eixos_revisada.csv`. A expressão “sem interferência comprovada” não deve ser usada antes da validação hidráulica e de campo.

### 4.7 Manchas de inundação — HAND como triagem antes do HEC-RAS 1D

O `08_manchas_hand.py` já executou uma triagem com HAND + curva‑chave sintética
de Manning, do eixo barrado até Bom Retiro do Sul. O HAND foi usado antes do
HEC-RAS 1D para delimitar o corredor, testar coerência geomorfológica, gerar
uma primeira aproximação de lâmina/mancha e organizar a comparação com o
evento observado. Ele **não substitui** o modelo hidráulico.

A implementação segue a mecânica descrita por Rennó et al. (2008), Nobre et
al. (2011) e Goerl et al. no trabalho *O modelo HAND como ferramenta de
mapeamento de áreas propensas a inundar*: MDE hidrologicamente consistente,
direção/acumulação de fluxo, definição da drenagem de referência e
normalização `HAND = cota do terreno − cota da drenagem`. A versão do projeto
acopla uma curva-chave sintética de Manning por trecho. Os parâmetros
`LIM_CANAL_KM2 = 150`, `MANNING_CANAL = 0,035` e `MANNING_PLANICIE = 0,070`
ainda são preliminares e devem ser calibrados por sensibilidade, usando
sensibilidade/especificidade e a mancha de maio de 2024 como no artigo.

O HEC-RAS 1D deverá receber hidrogramas de entrada, seções topobatimétricas,
pontes, diques, confluências e condições de jusante; depois será calibrado
com níveis, curva-chave e mancha de maio de 2024. Os resultados HEC-RAS 1D
serão a base para curva cota–dano, EAD e seleção final da alternativa.

| Cenário | Área inundada |
|---|---:|
| Sem barragem | 296,8 km² |
| Com E12 90 m seca | 252,2 km² |
| Redução | 44,6 km² (15,0%) |

Por município, maiores reduções relativas: Roca Sales 45%, Encantado 43%, Colinas 38%, Arroio do Meio 33%, Muçum 31%. Em Estrela a área cai só 19% mesmo com o pico caindo 53% — a planície é larga e plana.

### 4.8 Cascatas de barragens com comportas — preparação

O `EUROCLIMA-rev.kmz` contém 12 eixos; o pipeline `10_eixos_cascata.py` já
gerou a topologia completa. O teste existente em `07_comportas_uso_multiplo.R`
é apenas para um reservatório (E12). Portanto, ele não representa ainda a
operação conjunta de barragens com comportas em série ou em ramos convergentes.

Foi criado `07_python/30_inventario_cascatas_comportas.py`, que gera:

- `06_resultados/tabelas/rede_imediata_cascatas_comportas.csv`;
- `06_resultados/tabelas/cascatas_candidatas_comportas.csv`;
- `06_resultados/CASCATAS_COMPORTAS_METODOLOGIA.md`.

Os caminhos geomorfológicos de triagem são `E01 → E11 → E12`,
`E02 → E03 → E08 → E09 → E10 → E11 → E12` e
`E04 → E05 → E06 → E07 → E08 → E09 → E10 → E11 → E12`. Eles são uma rede de
conexões derivada de D8/BHO, não uma autorização para construir todos os
eixos. O próximo passo é o roteamento conjunto com conservação de massa,
tempos de viagem, deplecionamento preventivo, abertura de comportas,
saturação, galgamento, perda de queda e interação com Monte Claro–Castro
Alves–14 de Julho. A validação final será no HEC-RAS 1D.

Uma primeira sensibilidade do `31_roteamento_cascata_comportas.py` indicou
48,8% de redução para E02+E04, 63,1% para E02+E04+E12, 51,6% para E02+E04+E08,
18,0% para E09+E10+E11+E12 e 66,9% para a rede ramificada C05. Esses números
usam hidrograma sintético, 6 h de viagem e descarga simplificada. C05 teve um
galgamento e inclui E10; não deve ser tratado como recomendação. Os resultados
estão em `06_resultados/CASCATAS_COMPORTAS_TRIAGEM.md` e nas tabelas
`roteamento_cascata_comportas_triagem.csv`,
`roteamento_cascata_comportas_detalhe.csv` e
`hidrogramas_cascatas_comportas_triagem.csv`.

---

### 4.9 Integração dos achados da trilha Claude

O relatório `CLAUDE/CLAUDE_ACHADOS_PARA_CODEX.md` foi incorporado ao estado do
projeto. As decisões são:

- usar `claude_sinv_*_v2.csv`; a vazão específica média calibrada é 0,0269
  m³/s/km². Os ICB da v1 ficam apenas como histórico;
- manter E10 fora da carteira principal por balanço energético líquido negativo
  em toda a faixa viável;
- separar, nas fichas dos eixos, a altura de veto por cota mínima operacional
  da altura de início da perda energética na usina de montante;
- manter a discrepância de 15,5 m em Monte Claro como pendência de datum,
  ponto de ancoragem ou identificação da superfície. A restrição de E09 não
  deve ser tratada como confiável antes desse esclarecimento;
- considerar os insumos HEC-RAS 1D como geometria preliminar de montagem:
  39,4 km, 102 seções, 4 travessias e 6 confluências. Ainda faltam
  topobatimetria, cadastro de pontes, diques, curva-chave e séries observadas;
- testar a condição de jusante, pois a declividade estimada nos 10 km finais é
  6,3 × 10⁻⁵ m/m e pode fazer o nível de Estrela depender do remanso de jusante.

O relatório completo está em `06_resultados/CLAUDE/CLAUDE_ACHADOS_PARA_CODEX.md`.

## 5. O que NÃO é confiável — leia antes de usar qualquer número

### 5.1 Parâmetros não calibrados (todos em `02_R/00_config.R` e nos blocos `PAR`)

| Parâmetro | Valor usado | Situação |
|---|---:|---|
| Pico do evento em Estrela | 18.000 m³/s | **sintético** — hidrograma gama de 2 parâmetros |
| Lâmina escoada | 260 mm | arbitrado |
| **Dano direto do evento em Estrela** | **R$ 2.500 M** | **placeholder — governa toda a economia** |
| Vazão sem dano relevante | 4.000 m³/s | estimado, a determinar com HEC‑RAS |
| TR atribuído ao evento | 100 anos | arbitrado |
| Vazão específica de longo termo | 0,0269 m³/s/km² | calibrado preliminarmente nas fichas SNIRH; ainda sensível para a energia |
| Custo de aterro | R$ 90/m³ | ordem de grandeza |
| Desapropriação | R$ 45.000/ha | ordem de grandeza |

Sensibilidade ao dano: **se o dano real for inferior a ~R$ 1 bilhão, nenhuma barragem se justifica**. Acima de R$ 1,5 bi, várias se justificam. Limiar de viabilidade de cada alternativa em `06_resultados/tabelas/dano_limiar_viabilidade.csv`.

### 5.2 Curvas CAV e volume abaixo do NA atual

**O volume ABAIXO do NA atual dos reservatórios existentes não pode ser obtido diretamente do MDE**, porque o MDE contém a superfície da água, não a batimetria. Foi executada uma adaptação de triagem inspirada em Domeneghetti (2016), usando superfície, perfil natural e largura do espelho; ela reconstruiu 6 de 20 usinas e apresentou divergências grandes em relação a Manning.

Foi executada uma segunda sensibilidade com o recorte público ANADEM. Ela reconstruiu 17 de 20 usinas, contra 6 de 20 no `mdr.tif`; as saídas estão separadas em `batimetria_sintetica_mdr.csv` e `batimetria_sintetica_anadem.csv`. A comparação está em `06_resultados/COMPARACAO_MDES_BATIMETRIA.md`. A diferença de cobertura confirma que o MDE é uma fonte de incerteza; o ANADEM não deve ser somado ao `mdr.tif` como observação independente.

Saídas da triagem: `06_resultados/tabelas/batimetria_sintetica.csv` e `06_resultados/tabelas/volume_deplecionamento.csv`. Esses números continuam sendo apenas sensibilidade. A pendência foi parcialmente destravada pelo registro de CAV da ANA/SNIRH: foram baixadas as planilhas oficiais de **14 de Julho, Castro Alves e Monte Claro**, com curvas atualizadas, relatório batimétrico e geodatabase nos pacotes originais. A base consolidada está em `01_dados/cav_snirh/curvas/cav_snirh_consolidada.csv`, a ficha em `01_dados/cav_snirh/cav_snirh_ficha_tecnica.csv` e a documentação em `01_dados/cav_snirh/README.md`.

Para as três UHEs, `06_resultados/tabelas/volume_deplecionamento_cav_snirh.csv` substitui a curva sintética do MDE. Na primeira leitura, o volume oficial de espera acumulado é aproximadamente **12 hm³ a 1 m, 36 hm³ a 3 m, 58 hm³ a 5 m, 105 hm³ a 10 m e 139 hm³ a 15 m**, somando as três usinas. O valor ainda não é volume operacional disponível: depende de regra de depleção, reenchimento, segurança, geração, remanso e simulação da cascata.

O cadastro encontrado não trouxe pacotes com os nomes Foz do Prata, Passo do Meio, Serra Cavalinhos, Jararaca ou Cotiporã. Isso é ausência no registro consultado, não prova de inexistência de CAV em outras bases da ANA, ONS ou CERAN.

Para as usinas sem pacote, ainda será necessário solicitar CAV, nível e batimetria à ANA, ao ONS ou aos concessionários. O MDE continua sendo inadequado para preencher essa lacuna.

Para os 12 eixos novos, a situação é diferente: não existe reservatório atual
no local. O `10_eixos_cascata.py` já havia calculado 276 pontos CAV a cada 5 m
entre 10 e 120 m de altura, a partir do relevo natural do MDE. O
`27_ajusta_cav_eixos_novos.py` densificou esses dados para passos de 1 m por
interpolação PCHIP monotônica, sem extrapolação. Polinômios de graus 2–4 foram
calculados apenas para documentação e sensibilidade; a curva monotônica deve
ser usada na interpolação operacional preliminar. A nota metodológica está em
`06_resultados/CAV_EIXOS_NOVOS_METODOLOGIA.md`.

A base integrada, com classe de confiabilidade explícita, está em
`06_resultados/tabelas/cav_base_unica.csv`: 3 CAVs oficiais SNIRH (classe A) e
12 CAVs derivadas do MDE natural dos eixos novos (classe B).

A validação está em `06_resultados/tabelas/VALIDACAO_CAVS.md` e
`validacao_cavs.csv`. Todas as 15 curvas estão crescentes em cota, área e
volume. Nos eixos novos, o erro mediano da verificação `dV/dc ≈ área` ficou
entre 0,1% e 0,6%; os maiores desvios aparecem em trechos de área pequena ou
de mudanças abruptas do relevo e devem ser tratados como incerteza de triagem.

### 5.3 Energia superestimada

`07_comportas_uso_multiplo.R` calcula energia assumindo turbinamento contínuo da vazão média de longo termo. Energia firme real é bem menor. **A metodologia SINV foi implementada em triagem pelo Claude** nos arquivos `06_resultados/CLAUDE/claude_sinv_energetico.csv` e `claude_sinv_sintese_eixos.csv`. A rodada v2 (`claude_sinv_energetico_v2.csv`, `claude_sinv_sintese_eixos_v2.csv` e `claude_sinv_alternativas_v2.csv`) usa vazão específica calibrada pelas fichas SNIRH e as CAVs PCHIP dos eixos novos. A ordenação relativa é útil, mas os ICB absolutos ainda dependem de séries ANA, custos, razão de período crítico e reenchimento. A auditoria energética indica E10 com balanço negativo em toda a faixa viável; tratá-lo como descartado da carteira principal até revisão.

### 5.4 Bugs corrigidos ao longo do caminho

Registrados porque indicam onde o código merece revisão:

- Sinal invertido na integral do EAD em `05_analise_alternativas.R` — benefícios saíam negativos.
- Acumulação de fluxo truncada pela janela de recorte em `08_manchas_hand.py` — as duas manchas saíam idênticas.
- Snap caindo no canal de fuga em vez do espelho d'água em `13_volume_espera_existentes.py` — volumes saíam ~zero.
- Teste de "usina a montante" usando só área de drenagem em `12_altura_maxima_admissivel.py` — pegava usinas de outros tributários. Corrigido exigindo área menor **e** cota maior.
- Três bugs no roteamento com comportas: vertedouro superdimensionado (soleira a meia altura, 200 m de comprimento, dava 150.000 m³/s), regra de reservatório cheio despejando mais que a afluência, e ausência de dimensionamento do vertedouro pela cheia de projeto.
- Artefato na decomposição do hidrograma (somar gamas independentes produzia "redução negativa") — corrigido decompondo o hidrograma natural por fração de área.

---

## 6. Pendências, em ordem de prioridade

### 6.1 Implementar a metodologia SINV (fórmulas já extraídas)

**Estado atualizado:** implementada em triagem pelo Claude e executada nas alturas longitudinais revisadas. Saídas: `06_resultados/CLAUDE/claude_sinv_energetico.csv`, `claude_sinv_sintese_eixos.csv`, `claude_sinv_alternativas.csv` e `06_resultados/VALIDACAO/sinv_alternativas_revisadas.csv`. Os ICB absolutos não são defensáveis antes de calibrar vazão específica, razão de período crítico, custos e reenchimento; a ordenação relativa é o uso recomendado nesta etapa.

Manual em `Referencias/Manual de Inventario Hidroeletrico .../fscommand/`. Seções relevantes: `46.pdf` (estudos energéticos preliminares), `53.pdf` (estudos finais), `411.pdf` (comparação e seleção). Texto já extraído em formato utilizável.

Fórmulas a implementar:

- **Energia firme**: `Ef_i = 0,0088 × Hlm_i × Qlm_i` [MW médios] — eq. 4.6.1.01
  O coeficiente 0,0088 = 1000 kg/m³ × 0,93 (turbina) × 0,97 (gerador) × 9,81 / 10⁶
- **NAmxn com volume de espera**: nível correspondente ao volume máximo **descontada a média dos volumes de espera** ao longo do período crítico
- **NAjn**: nível natural para vazão 10% superior à média do período crítico, **ou o NAmxn do reservatório imediatamente a jusante, se mais elevado** ← é aqui que entra a cascata existente
- **Depleção máxima ≤ 1/3 da queda bruta máxima**
- **Perdas de carga**: 2% (circuito compacto) ou 3% (longo)
- **Qlm** — eq. 4.6.1.03, com desconto de evaporação, volumes de espera e retiradas para usos múltiplos
- **Otimização de volumes úteis** — item 4.6.4, iterativo de jusante para montante
- **Potência instalada**: `P_i = Ef_i / Fk` — eq. 4.6.5.01
- **Reenchimento em até 36 meses** — item 4.6.6
- **ICB**: `ICB_i = CT_i / (ΔEf_i × 8760)` [R$/MWh] — eq. 4.11.1.01
  com `CT_i = C_i × FRC + P_i × COM × 10³` e `FRC = j(1+j)^z / ((1+j)^z − 1)`, z = 50 anos

Rodar **apenas nas alturas admissíveis** da §4.5 — não faz sentido calcular energia de arranjos que afogam usina existente.

### 6.2 Custos e limites do alteamento

**Entregue na atualização de 30/07/2026:** triagem reproduzível de custo, execução, limites e alternativas sem alteamento. Base: `06_resultados/tabelas/volume_espera_existentes.csv`, que tem o volume ganho por metro em cada usina; benchmark de custo: `06_resultados/tabelas/altura_maxima_admissivel.csv`, que contém os custos dos novos eixos admissíveis calculados pelo pipeline geométrico.

**Ainda falta para transformar a triagem em estudo de pré-viabilidade:**

- cruzar a área adicional inundada a cada metro com edificações, estradas, pontes, linhas, captações, unidades de conservação e patrimônio;
- obter tipo, estado, altura, comprimento de crista, fundações, vertedouro, comportas e instrumentação de cada barragem;
- obter projetos as built, inspeções, batimetria e curvas cota×volume;
- substituir a faixa paramétrica por orçamento conceitual de engenharia e comparar custo, energia, segurança, licenciamento e dano evitado;
- simular hidrologia, operação e remanso em cascata antes de aceitar qualquer volume como volume de espera.

O alteamento não é a frente principal de decisão neste momento; fica reservado para os poucos reservatórios que sobreviverem à análise de benefício, segurança, remanso, área adicional, custo e licenciamento.

### 6.3 Curva cota–dano e base territorial única

O Atlas foi extraído para 19 municípios do corredor e consolidado com a malha municipal no GeoPackage mestre. A estratégia seguinte é cruzar manchas/profundidades com setores censitários definitivos do IBGE 2022, população/domicílios, custo de reposição por tipologia e, quando disponível, cadastro municipal. IpeaGEO entra como contexto socioeconômico e fonte territorial; não será tratado como cadastro de preço de imóvel.

Arquivo de orientação: `06_resultados/CURVA_COTA_DANO_ESTRATEGIA.md`. Saídas atuais: `01_dados/atlas/`, `06_resultados/tabelas/atlas_danos_municipios.csv` e `Documentos EUROCLIMA+/Espanha/GIS/02_GPKG_MESTRE/euroclima_master.gpkg`.

### 6.4 Completar as curvas cota × volume das usinas existentes

**Parcialmente concluído.** As três UHEs principais da CERAN já têm curvas oficiais importadas e auditáveis no SNIRH/ANA; a análise de deplecionamento foi rodada para 1, 2, 3, 5, 8, 10 e 15 m. Completar a cobertura para os demais reservatórios, confirmar o datum vertical do MDE, obter níveis operacionais/telemetria e simular a operação conjunta da cascata.

### 6.5 Recalibrar com dados reais

- Rodar `02_R/01_baixa_dados_ana.R` (nunca executado) para as séries dos postos 86870000, 86879300 (Estrela/Lajeado), 86510000 (Muçum), 86720000 (Encantado).
- Digitalizar a série consistida 1939–2023 de `Referencias/revisao_consolidacao_serie_historica_rio_taquari_lajeado.pdf` (Moraes, Collischonn, Buffon & Eckhardt, 2024) — seções 8 e 9. É a melhor base disponível.
- Substituir `PAR_EVENTO` em `02_R/02_volume_amortecimento.R`. Todas as conclusões se atualizam sozinhas.

### 6.6 HEC‑RAS **1D** (decisão do usuário)

O usuário definiu que a modelagem será **unidimensional**. O roteiro foi ajustado pelo Claude em `06_resultados/CLAUDE/CLAUDE_ROTEIRO_HECRAS_1D.md`. A recomendação é detalhar aproximadamente 12 km na área urbana de Estrela/Lajeado, mantendo os 39,4 km do trecho contratado como contexto. Insumos prontos: `Trecho_Modelagem`, o perfil `06_resultados/CLAUDE/claude_perfil_principal.csv`, manchas observadas e o roteiro de condições de contorno. O canal continua bloqueado por ausência de seções topobatimétricas, curva-chave e séries consistidas.

### 6.7 Site Quarto no GitHub — **estrutura criada e renderizada**

O site segue o padrão de [`tutorial-trigrs`](https://sedec-dpm-cgnat.github.io/tutorial-trigrs/),
com capítulos independentes em `.qmd`, navegação lateral, referências e linguagem didática.
Mantém as logos `DPM-Circular.png` e `logo_marca_sedec.png`; **não usa a logo da UFF**.
O HTML local está em `docs/index.html`; falta apenas revisão final, commit, push e publicação.

### 6.8 Figura de divisão de quedas

Perfil longitudinal extraído pelo Claude (`06_resultados/CLAUDE/claude_perfil_principal.csv`, aproximadamente 375 km no canal principal) e figura revisada em `06_resultados/VALIDACAO/DIVISAO_QUEDAS_REVISADA.png`. Foram acrescentados os zooms `DIVISAO_QUEDAS_ZOOM_E02_E04_CASTRO.png` e `DIVISAO_QUEDAS_ZOOM_CASCATA_ANTAS.png` para tornar legíveis os rótulos e a cascata principal no relatório/site. A figura original de Claude é mantida em `06_resultados/CLAUDE/claude_divisao_quedas.png` para rastreabilidade.

### 6.9 Reorganização das pastas

`07_python/04_reorganiza_pastas.py` continua em *dry‑run* para a árvore documental geral. Para GIS, a organização foi aplicada de forma reversível: `GIS/02_GPKG_MESTRE` contém o GeoPackage mestre, `GIS/03_SHP_ENTREGA` os shapefiles, `GIS/04_KMZ_ENTREGA` os KMZ e `GIS/00_CATALOGO` os metadados. As fontes legadas `GIS/shapefiles` e `GIS/raster` foram preservadas.

---

### 6.10 Atualização de 31/07/2026 — relatório, hidrologia e eixos exploratórios

O relatório Quarto foi estruturado e renderizado em `docs/index.html`, com capítulos sobre
hidrologia, HAND, alternativas, cascatas, HEC-RAS 1D, danos, energia, custo–benefício,
limitações e referências. Foram incorporados os hidrogramas sem barragem versus C01–C05,
figuras de divisão de quedas por alternativa e o plano de trabalho paralelo em
`PLANO_TRABALHO_PARALLELO_CODEX_CLAUDE.md`.

O script `07_python/32_figuras_eixos_exploratorios.py` gerou:

- `06_resultados/tabelas/eixos_exploratorios_propostos.csv`;
- `06_resultados/GIS/eixos_exploratorios_propostos.kmz` e `.kml`;
- `06_resultados/VALIDACAO/PERFIL_EIXOS_EXPLORATORIOS.png`;
- `06_resultados/VALIDACAO/DIVISAO_QUEDAS_ALTERNATIVAS.png`;
- `06_resultados/VALIDACAO/MATRIZ_ALTERNATIVAS_EIXOS.png`;
- `06_resultados/VALIDACAO/validacao_ancoragem_eixos.csv`;
- `06_resultados/figuras/14_hidrogramas_natural_vs_cascatas.png`;
- `06_resultados/figuras/15_hidrograma_natural_vs_C02.png`.

O arquivo separado `EIXO-MONTECLARO2.kmz` foi conferido e contém uma `LineString` alinhada ao
canal principal. O ponto médio está na estaca aproximada 294,48 km do perfil, a cerca de 12 m
do talvegue, entre Monte Claro e 14 de Julho. A geometria original foi preservada no KMZ
consolidado. MC2 deve ser tratado como candidato adicional no pipeline, não como E13 definitivo,
até validar CAV, remanso, energia, interferência com a cascata e a cota/datum da geometria.

### 6.11 Proposta de divisão da próxima rodada — 01/08/2026

O Claude registrou a proposta completa em
`06_resultados/CLAUDE/CLAUDE_PROPOSTA_DIVISAO_PROXIMA_RODADA.md`. O caminho crítico é:

- **Claude:** C1 roteamento das alternativas revisadas; C2 séries ANA; C3 recalibração do
  evento e do limiar de dano; C4 SINV v3; C5 casos HEC-RAS 1D; C6 sincronização dos tributários;
- **Codex:** X1/X2 ancoragem BHO/D8; X3 conciliação do datum de Monte Claro; X4 atualização
  do MC2; X5 relatório, figuras e template; X6 exposição/cota–dano; X7 custo–benefício.

A auditoria X1/X2 foi executada em saída isolada `01_dados/cav_anchor_check2` e mostrou os
12 eixos com interseção BHO e razão área_D8/área_BHO entre 0,988 e 1,001. O resultado está em
`06_resultados/VALIDACAO/validacao_ancoragem_eixos.csv`; os arquivos canônicos não foram
substituídos porque as pequenas mudanças de ponto/cota precisam ser propagadas junto com CAV,
SINV e roteamento.

A conciliação preliminar de Monte Claro está em
`06_resultados/VALIDACAO/CONCILIACAO_DATUM_MONTE_CLARO.md`. O ANADEM reproduz 148,0 m, enquanto
o MDE principal registra 132,5 m; isso indica diferença de fonte/superfície, mas ainda não
prova um datum. Até obter a referência vertical oficial, E09 e MC2 devem permanecer em
sensibilidade.

### 6.12 Rodada calibrada C1–C4 — 01/08/2026

O Claude concluiu a rodada C1–C4 e deixou os produtos em
`06_resultados/CLAUDE/CLAUDE_RELATORIO_C1_C2_C3.md` e nos arquivos
`claude_c1_*` a `claude_c4_*`. Esta rodada deve ser a referência de triagem do
relatório; os resultados anteriores baseados em pico sintético de 18.000 m³/s
devem ser mantidos apenas para rastreabilidade histórica.

Parâmetros calibrados preliminares: pico no ponto de análise de 16.300 m³/s,
lâmina efetiva de 227 mm, vazão de base de 926 m³/s e período de retorno de
333 anos pelo ajuste de Gumbel por L-momentos na série de Muçum. A série tem
aproximadamente 86,2 anos e máximo de 15.092 m³/s. Setembro de 2023 tem o maior
pico observado, enquanto maio de 2024 tem maior volume; a nota técnica deve
preservar essa distinção.

O roteamento calibrado produziu a seguinte ordem de grandeza:

| Alternativa | Volume usado (hm³) | Pico residual (m³/s) | Redução | Saturação |
|---|---:|---:|---:|---|
| ALT-A — E02+E04 | 1.694 | 9.272 | 43,1% | não |
| ALT-D — E02+E04+E08 | 1.871 | 8.411 | 48,4% | não |
| ALT-E — E02+E04+E12 | 2.366 | 6.328 | 61,2% | não |
| ALT-J — carteira completa | 2.639 | 6.213 | 61,9% | sim, em pelo menos um eixo |
| E12 isolado | 976 | 16.267 | 0,2% | sim |

Nenhuma das 30 combinações alcançou a referência preliminar de 4.000 m³/s.
O resultado confirma que a operação de barragem seca é decisiva e que E12
isolado satura antes de contribuir para o pico. Isso ainda não seleciona uma
alternativa: a conclusão depende da defasagem dos tributários, remanso,
HEC-RAS 1D, perdas de geração, custo e benefício monetizado.

O gráfico integrado ao relatório é
`06_resultados/figuras/16_hidrograma_calibrado_ALTJ.png`. Antes da rodada final,
o Codex deve atualizar a curva cota–dano e a análise custo–benefício com esses
hidrogramas, sem reutilizar o dano placeholder de R$ 2.500 milhões como valor
central.

### 6.13 Novo ramo de investigação — Forqueta

Após a rodada C1–C4, foram propostos dois eixos de retenção no Forqueta, que representa
aproximadamente 14,63% da área contribuinte do trecho de Estrela. O FQ1, no segmento
inferior, controla 2.353,6 km² (82,7% da bacia do tributário); o FQ2, em posição
intermediária, controla 2.226,7 km² (78,3%).

O pipeline isolado confirmou razão área_D8/área_BHO de 0,9985 para FQ1 e 0,9899 para FQ2.
As cotas do eixo no MDE são 22,5 m e 40,0 m. A CAV de triagem indica, a 80 m de altura,
2.424 hm³ para FQ1 e 1.289 hm³ para FQ2; no teto geométrico de 120 m, 5.518 hm³ e
3.043 hm³, respectivamente. Esses números são classe B, derivados do MDE natural, e não
constituem altura admissível nem volume operacional.

Produtos: `07_python/35_propoe_eixos_forqueta.py`,
`06_resultados/GIS/eixos_forqueta_propostos.kmz`,
`06_resultados/tabelas/eixos_forqueta_propostos.csv`,
`01_dados/cav_forqueta/` e `06_resultados/VALIDACAO/MAPA_EIXOS_FORQUETA.png`.

O roteamento solicitado foi concluído pelo Claude em `CLAUDE_NOTA_FORQUETA.md`.
FQ1/FQ2 foram tratados como afluências laterais na seção de Estrela, não no ponto de
análise de 19.440 km². FQ1 e FQ2 ficam fora da referência e são mutuamente exclusivos;
FQ1 só será reaberto se Barra do Fão confirmar defasagem positiva no evento de projeto.

Como primeira entrega de X6, o Codex criou
`07_python/34_consolida_exposicao_municipal.py`, que gera
`06_resultados/tabelas/base_exposicao_municipal_preliminar.csv` e a documentação
`06_resultados/BASE_EXPOSICAO_MUNICIPAL_PRELIMINAR.md`. A tabela integra 19
municípios, a mancha HAND preliminar e os três recortes do Atlas. Ela não contém
estimativas inventadas de população, domicílios ou valor de imóveis: esses campos
continuam aguardando setores/agregados IBGE 2022, tipologias e custos unitários.

## 7. Divergências do TR ainda em aberto

Resolvidas pelo `EUROCLIMA.kmz` (as feições `AreaLIDAR_DRONE` = 16,3 km² e `Trecho_Modelagem` = 39,4 km confirmam o Descritivo, não a base GIS antiga):

| Item | Descritivo | Base GIS antiga | KMZ (vale este) |
|---|---:|---:|---:|
| Trecho de modelagem | 40 km | 51,7 km | **39,4 km** |
| Área do voo LiDAR | 16 km² | 24 a 139 km² | **16,3 km²** |
| Batimetria | 1,6 km² | — | **1,35 km²** |

Ainda em aberto: divergência de **€ 1.375** entre o Anexo II — Presupuesto (€ 273.875) e a aba *Actividades‑Español* do Macro Logframe (€ 272.500).

---

## 8. Conclusão substantiva até aqui

1. **A primeira estimativa de 2.565 hm³ estava condicionada ao critério antigo de montante/jusante.** A revisão longitudinal auditada elevou o volume geométrico de triagem para 6.855 hm³, com E02 + E04 somando 3.588 hm³ até o teto hipotético de 120 m. Isso ainda não prova que os danos de 2024 serão evitados: faltam engenharia, hidrologia conjunta, remanso entre eixos e validação de campo.

2. **O arranjo operacional importa mais que o tamanho.** Vertedouro com comportas + deplecionamento preventivo entrega 63% de redução *e* geração; soleira livre entrega 0–16%.

3. **A cascata existente continua sendo a restrição dominante na maior parte do canal principal**, mas E02 e E04 surgem como candidatos de baixa interferência na triagem. A distinção precisa ser mantida até a confirmação hidráulica da conectividade e dos aproveitamentos intermediários.

4. **Alteamento não é caminho** — 20 m em 20 usinas dá 20% do volume necessário.

5. **A alternativa mais promissora ainda não foi avaliada**: alocar volume de espera nos reservatórios existentes por regra operativa. 360 MW instalados na bacia operando sem nenhuma função de controle de cheias é, por si só, um achado para o TR.

6. **Consequência para o TR:** o Eixo 3 deve ser enquadrado como *análise comparativa de alternativas híbridas* — barragens + diques + realocação + controle de uso do solo + alerta precoce + regra operativa dos reservatórios existentes — e não como projeto de barragens. A minuta REV_0B já está redigida assim.

### 6.14 Acesso ao banco hidrológico DPM

Em 2026-08-01 foi validado o acesso read-only ao banco PostgreSQL privado informado pelo
usuário. O catálogo seletivo e a estratégia de uso estão em
`06_resultados/DB_HIDROLOGICO_ACESSO_ESTRATEGIA.md`; a tabela de inventário está em
`06_resultados/tabelas/catalogo_db_hidrologico.csv` e o script é
`07_python/36_inventaria_db_hidrologico.py`. Nenhuma credencial foi registrada no
repositório e nenhuma operação de escrita foi executada.

As séries prioritárias são: Castro Alves (86305000), Monte Claro (86448000), 14 de
Julho (86470800), Muçum (86510000), Encantado (86720000), Forqueta/Passo do Coimbra
(86745000) e Estrela (86879300). O banco também oferece chuva diária, grade climática
Xavier, metadados estatísticos ANA e Atlas de Desastres. A próxima rodada deve extrair
somente as séries e janelas necessárias, alimentar C5/C6 e manter Estrela como controle
de evento, não como amostra estatística principal.

### 6.15 Resultado final da rodada Forqueta

O relatório completo do Claude está em `06_resultados/CLAUDE/CLAUDE_NOTA_FORQUETA.md`.
Ele substitui a priorização anterior de FQ1. A série observada do posto Passo do Coimbra
(86745000) indicou defasagem central de 0 dia em 13 eventos e pico transposto de 3.837 m³/s.
No roteamento com exutório em Estrela, ALT-J sem Forqueta reduziu 58,6%, ALT-J+FQ1 reduziu
59,3% e ALT-J+FQ2 reduziu 59,7%.

FQ1 e FQ2 são mutuamente exclusivos: a 30 m, o NA preliminar de FQ1 fica 12,5 m acima da
cota do eixo FQ2. Nenhum deve integrar a alternativa de referência. Isso não é descarte do
tributário: como o Forqueta conflui a montante de Estrela, ele permanece relevante como
afluência lateral. FQ1 permanece uma opção
condicionada à confirmação de defasagem positiva no evento de novembro de 2023, que coincide
com uma lacuna da série do Passo do Coimbra. A ação prioritária é reativar a curva-chave e
obter dados subdiários em Barra do Fão (86780000).

Há também um novo achado: o Guaporé, representado pelo posto Santa Lúcia (86580000), tem
contribuição de ordem semelhante à do Forqueta e deságua a montante do ponto de análise.
Deve ser investigado antes de ampliar o trabalho no Forqueta. A próxima frente do Codex é
avaliar BHO/D8, CAV, interferências, energia e roteamento de um eixo exploratório no Guaporé.
O banco confirma 31.047 registros diários de 1940 a 2024, área ANA de 2.470 km² e máximo
observado de 5.077,1 m³/s. O GU1-PROPOSTO foi ancorado com razão D8/BHO de 0,9999, área
D8 de 1.993,4 km² e cota MDE de 227,5 m; esses valores ainda são classe de triagem.

### 6.16 Busca ampliada de carteiras — 01/08/2026

Para responder à hipótese de adicionar outras barragens, o Codex executou uma busca
exaustiva de todas as 32 adições possíveis à ALT-J usando E03, E06, E07, E09 e E11,
mantendo E10 fora da carteira principal. O melhor pico em Estrela permaneceu em
7.005 m³/s; nenhuma carteira ficou abaixo do limiar preliminar de 4.000 m³/s.
O envelope teórico com E10 também teve 0 de 64 carteiras abaixo do limiar. Com FQ1/FQ2,
foram testadas 192 combinações; o melhor resultado foi ALT-J + FQ2, seca, com
6.802 m³/s, ainda 2.802 m³/s acima do limiar.

A repetição do pico nas adições do Antas decorre da topologia aninhada e do E12 como
terminal de 81,1% da área, não de uma prova de irrelevância hidráulica local desses
eixos. Resultados: `06_resultados/BUSCA_CARTEIRAS_AMPLIADAS_ANTAS_FORQUETA.md` e
`06_resultados/tabelas/carteiras_ampliadas_antas_*.csv`.

### 6.17 Primeira rodada numérica do GU1 — 01/08/2026

A sub-bacia do Guaporé foi desagregada do hidrograma do Antas: 2.486,7 km² no Guaporé
e 16.953,3 km² na vertente residual. A série DPM do Santa Lúcia foi baixada para
`01_dados/dpm_db/86580000_vazao.csv` (30.591 registros válidos; máximo 5.077,1 m³/s).
Foram avaliadas 384 combinações de evento, defasagem, altura, operação, ALT-J e FQ2.

No máximo histórico do Santa Lúcia, ALT-J + GU1 a 100 m produziu **4.532 m³/s** em
Estrela, contra 7.038 m³/s sem GU1 na mesma decomposição. No evento de novembro de 2023,
com defasagem zero e 120 m apenas como envelope geométrico, o pico foi **4.763 m³/s**.
Nenhuma combinação ficou abaixo de 4.000 m³/s. O GU1 passa a ser a prioridade estrutural
para HEC-RAS 1D, mas a altura admissível, a operação, a energia e a interferência com
Guaporé/Monte Cuco ainda precisam ser verificadas.

### 6.18 Matriz HEC-RAS 1D explicitada — 02/08/2026

O relatório foi atualizado para separar o caso de referência, as alternativas estruturais
comparáveis e as sensibilidades laterais. A ordem de modelagem é:

1. **HEC-00 / REF:** situação atual, sem novos reservatórios, para calibrar o evento de 2024;
2. **HEC-01 / ALT-A / C01:** E02 + E04, primeiro caso com obra;
3. **HEC-02 / ALT-D / C03:** E02 + E04 + E08, incremento de E08;
4. **HEC-03 / ALT-E / C02:** E02 + E04 + E12, incremento de E12;
5. **HEC-04:** ALT-J + GU1, extensão estrutural prioritária após a calibração;
6. **HEC-05:** ALT-J + FQ2, sensibilidade lateral no trecho de Estrela;
7. **HEC-06:** C04, C05, FQ1 e combinações selecionadas, apenas como sensibilidade.

O primeiro resultado com obra a ser solicitado é, portanto, **E02 + E04**. C02/C03
continuam sendo nomes de cenários de comportas: C03 é E02+E04+E08 e C02 é
E02+E04+E12. O diagrama reproduzível está em
`07_python/43_diagrama_topologico_hecras.py` e
`06_resultados/VALIDACAO/DIAGRAMA_TOPOLOGICO_ALTERNATIVAS_HECRAS.svg`.
Nenhuma alternativa deve ser chamada de selecionada antes da validação do HEC-RAS 1D,
da curva cota–dano e dos custos, benefícios, remanso, energia e segurança.

### 6.19 Retomada do projeto — auditoria dos contornos — 07/09/2026

O site Quarto foi publicado em `https://sedec-dpm-cgnat.github.io/euroclima-estrela-site/`.
O repositório técnico continua privado; a publicação é a saída estática de `docs/`.

Foi criada a auditoria `06_resultados/VALIDACAO/AUDITORIA_CONTORNOS_HECRAS.md` e o
manifesto `03_HECRAS/contornos_preliminares/manifesto_contornos_hecras.csv`. A
auditoria confirmou que o hidrograma calibrado de C4 tem pico de 16.299 m³/s e está
associado à seção de análise de 19.440 km². O C01/E02+E04 disponível ainda é uma
rodada sintética de triagem, com pico de 9.217 m³/s, e não deve ser usado como
condição final de montante do HEC-01.

O fechamento preliminar das áreas deixou 256,7 km² a explicar entre o limite de
jusante informado e a soma do limite de montante com as seis laterais. Antes da
execução do HEC-00, deve-se confirmar a seção de 19.440 km², fechar esse balanço,
gerar as séries laterais com defasagem e definir a condição de jusante. Para o
HEC-01, ainda é necessário produzir os efluentes nodais calibrados de E02 e E04;
não usar o hidrograma agregado de Estrela como substituto.

### 6.20 Avaliação do gerador Kirsch–Nowak — 07/09/2026

Foi localizada a pasta indicada pelo usuário em
`C:\Users\cassi\OneDrive\Documents\Ajumar\Kirsch-Nowak_Streamflow_Generator-master`.
O gerador é um método MATLAB para séries diárias sintéticas multissítio: gera totais
mensais correlacionados por Cholesky e os desagrega para diária por k-NN e
reescalonamento de padrões históricos. A avaliação detalhada está em
`06_resultados/AVALIACAO_KIRSCH_NOWAK_EUROCLIMA.md`.

A decisão metodológica é incorporá-lo como **C7 — ensemble probabilístico**, para
frequência de excedência, coincidência de picos, volume, duração, energia e danos. Ele
não substitui a rodada C3/C4 nem o HEC-RAS 1D: assume estacionariedade, produz série
diária e não representa diretamente comportas, remanso ou pontes. O primeiro passo é
auditar e harmonizar as séries ANA/DPM e montar componentes não aninhados de Antas,
Forqueta e Guaporé, sem dupla contagem. A validação estatística deve preceder qualquer
uso do ensemble em custo-benefício ou seleção final de alternativa.
