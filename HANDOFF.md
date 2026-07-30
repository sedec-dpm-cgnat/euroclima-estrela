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

### 4.7 Manchas de inundação

HAND + curva‑chave sintética de Manning, do eixo barrado até Bom Retiro do Sul:

| Cenário | Área inundada |
|---|---:|
| Sem barragem | 296,8 km² |
| Com E12 90 m seca | 252,2 km² |
| Redução | 44,6 km² (15,0%) |

Por município, maiores reduções relativas: Roca Sales 45%, Encantado 43%, Colinas 38%, Arroio do Meio 33%, Muçum 31%. Em Estrela a área cai só 19% mesmo com o pico caindo 53% — a planície é larga e plana.

---

## 5. O que NÃO é confiável — leia antes de usar qualquer número

### 5.1 Parâmetros não calibrados (todos em `02_R/00_config.R` e nos blocos `PAR`)

| Parâmetro | Valor usado | Situação |
|---|---:|---|
| Pico do evento em Estrela | 18.000 m³/s | **sintético** — hidrograma gama de 2 parâmetros |
| Lâmina escoada | 260 mm | arbitrado |
| **Dano direto do evento em Estrela** | **R$ 2.500 M** | **placeholder — governa toda a economia** |
| Vazão sem dano relevante | 4.000 m³/s | estimado, a determinar com HEC‑RAS |
| TR atribuído ao evento | 100 anos | arbitrado |
| Vazão específica de longo termo | 0,020 m³/s/km² | estimado — sensível para a energia |
| Custo de aterro | R$ 90/m³ | ordem de grandeza |
| Desapropriação | R$ 45.000/ha | ordem de grandeza |

Sensibilidade ao dano: **se o dano real for inferior a ~R$ 1 bilhão, nenhuma barragem se justifica**. Acima de R$ 1,5 bi, várias se justificam. Limiar de viabilidade de cada alternativa em `06_resultados/tabelas/dano_limiar_viabilidade.csv`.

### 5.2 Limitação de método que não tem contorno com os dados atuais

**O volume ABAIXO do NA atual dos reservatórios existentes não pode ser obtido do MDE**, porque o MDE contém a superfície da água, não a batimetria. Isso significa que a pergunta *"quanto volume de espera dá para abrir por deplecionamento preventivo, sem obra nenhuma?"* — que é provavelmente a alternativa mais barata de todas — **continua sem resposta**.

Para respondê‑la é preciso obter as curvas cota × volume das usinas. Tentei o ANA SAR (`https://www.ana.gov.br/sar/`) e os endpoints públicos retornaram 404. Caminhos: solicitar à ANA, ao ONS, ou aos concessionários (CERAN para Monte Claro / Castro Alves / 14 de Julho).

### 5.3 Energia superestimada

`07_comportas_uso_multiplo.R` calcula energia assumindo turbinamento contínuo da vazão média de longo termo. Energia firme real é bem menor. **A metodologia SINV foi extraída mas não implementada** (ver §6.1).

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

O usuário pediu explicitamente avaliação preliminar de: **custos do alteamento, como fazer, e os limites**. Falta:

- custo unitário de alteamento por metro e por usina (reforço estrutural, comportas, realocação de borda);
- o que é inundado a cada metro adicional (cruzar com edificações e infraestrutura);
- limite estrutural (barragens existentes suportam alteamento? depende do tipo — CCR, terra, enrocamento);
- **e alternativas que não impliquem alteamento**, para o caso de inviabilidade.

Base já disponível: `06_resultados/tabelas/volume_espera_existentes.csv` tem o volume ganho por metro em cada usina.

### 6.3 Obter as curvas cota × volume das usinas existentes

Desbloqueia a análise de deplecionamento preventivo (§5.2), que é a alternativa potencialmente mais barata.

### 6.4 Recalibrar com dados reais

- Rodar `02_R/01_baixa_dados_ana.R` (nunca executado) para as séries dos postos 86870000, 86879300 (Estrela/Lajeado), 86510000 (Muçum), 86720000 (Encantado).
- Digitalizar a série consistida 1939–2023 de `Referencias/revisao_consolidacao_serie_historica_rio_taquari_lajeado.pdf` (Moraes, Collischonn, Buffon & Eckhardt, 2024) — seções 8 e 9. É a melhor base disponível.
- Substituir `PAR_EVENTO` em `02_R/02_volume_amortecimento.R`. Todas as conclusões se atualizam sozinhas.

### 6.5 HEC‑RAS **1D** (decisão do usuário)

O usuário definiu que a modelagem será **unidimensional**. Roteiro em `PLANO_DE_ACAO.md` §3, que precisa ser ajustado (foi escrito para 2D). Insumos prontos: `Trecho_Modelagem` (39,4 km) e o perfil do talvegue em `06_resultados/tabelas/perfil_talvegue.csv`.

### 6.6 Site Quarto — **nada foi feito**

O usuário quer um site no padrão de `https://sedec-dpm-cgnat.github.io/tutorial-trigrs/`, **sem a logo da UFF**, mantendo DPM e Proteção e Defesa Civil. Com imagens em planta, perfis de linha d'água e diagramas esquemáticos, bem didático. Nenhum `.qmd` foi escrito.

### 6.7 Figura de divisão de quedas

Perfil longitudinal já extraído (`perfil_talvegue.csv`, 141 km de E10 até Bom Retiro do Sul, com cotas, áreas e declividades por município). Falta a figura no padrão de inventário: talvegue + NA máximo normal + NA máximo maximorum + crista de cada barramento, incluindo as usinas existentes.

### 6.8 Reorganização das pastas

`07_python/04_reorganiza_pastas.py` está pronto e testado em *dry‑run* (37 movimentações mapeadas). **Nunca foi executado com `--aplicar`** — mover centenas de arquivos no OneDrive é irreversível e ficou aguardando decisão.

---

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

1. **Barragens sozinhas não evitam os danos de uma cheia como a de 2024.** Precisaria de 3.230 hm³; o máximo mobilizável respeitando a cascata existente é ~2.565 hm³, e o piso físico de 3.400 m³/s da área não controlada é intransponível.

2. **O arranjo operacional importa mais que o tamanho.** Vertedouro com comportas + deplecionamento preventivo entrega 63% de redução *e* geração; soleira livre entrega 0–16%.

3. **A cascata existente é a restrição dominante**, e não foi considerada em nenhum momento do desenho original dos eixos.

4. **Alteamento não é caminho** — 20 m em 20 usinas dá 20% do volume necessário.

5. **A alternativa mais promissora ainda não foi avaliada**: alocar volume de espera nos reservatórios existentes por regra operativa. 360 MW instalados na bacia operando sem nenhuma função de controle de cheias é, por si só, um achado para o TR.

6. **Consequência para o TR:** o Eixo 3 deve ser enquadrado como *análise comparativa de alternativas híbridas* — barragens + diques + realocação + controle de uso do solo + alerta precoce + regra operativa dos reservatórios existentes — e não como projeto de barragens. A minuta REV_0B já está redigida assim.
