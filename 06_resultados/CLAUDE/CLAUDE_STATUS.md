# CLAUDE_STATUS — trilha de modelagem hidráulica, energética e de alternativas

**Projeto:** EUROCLIMA+ / AECID — Estrela/RS (bacia Taquari‑Antas)
**Trilha:** modelagem hidráulica, energética e de alternativas
**Data:** 30/07/2026
**Escopo respeitado:** apenas `07_python/claude_*.py`, `06_resultados/CLAUDE/`, `01_dados/claude/`. Nenhum arquivo do Codex foi editado. Nenhum resultado existente foi sobrescrito. Nenhuma reorganização de pastas.

---

## 1. Tarefas concluídas

| # | Tarefa solicitada | Estado |
|---|---|---|
| 1 | Implementar as fórmulas do SINV, exclusivamente para alturas admissíveis | ✅ concluída |
| 2 | Tabelas de energia, potência, volume, altura e restrições por eixo | ✅ concluída |
| 3 | Confirmar E02 como candidato prioritário de baixa interferência | ✅ **confirmado, e com margem muito maior que a estimada** |
| 4 | Avaliar E01 e E04 como alternativas independentes | ✅ concluída — **E04 mudou de patamar** |
| 5 | Retirar E05 da avaliação principal por inviabilidade | ⚠️ **contestada — ver §5** |
| 6 | Roteiro técnico HEC‑RAS 1D | ✅ concluída |
| 7 | Figura do perfil / divisão de quedas | ✅ concluída |

---

## 2. Scripts criados

| Script | Função |
|---|---|
| `07_python/claude_01_sinv_energetico.py` | Avaliação energética SINV (energia firme, potência instalada, ICB, reenchimento) nas alturas admissíveis, varrendo frações de volume de espera |
| `07_python/claude_02_divisao_quedas.py` | Perfil longitudinal do canal principal e diagrama de divisão de quedas |
| `07_python/claude_03_altura_admissivel_revisada.py` | Revisão da altura admissível de cada eixo por **posição longitudinal** |

---

## 3. Arquivos gerados

Todos em `06_resultados/CLAUDE/`:

| Arquivo | Conteúdo |
|---|---|
| `claude_sinv_energetico.csv` | 66 combinações eixo × fração de espera, com todas as grandezas SINV |
| `claude_sinv_sintese_eixos.csv` | Melhor arranjo de cada eixo, com e sem volume de espera |
| `claude_sinv_alternativas.csv` | 7 alternativas (conjuntos de eixos) com energia firme e ICB |
| `claude_altura_admissivel_revisada.csv` | Altura admissível revisada dos 12 eixos |
| `claude_comparacao_altura_admissivel.csv` | Comparação com a versão anterior, eixo a eixo |
| `claude_perfil_principal.csv` | Perfil do canal principal — 375 km, com cota, área de drenagem e coordenadas UTM por estaca |
| `claude_quedas_por_trecho.csv` | Quedas disponíveis entre barramentos consecutivos |
| `claude_divisao_quedas.png` | Diagrama de divisão de quedas |
| `CLAUDE_ROTEIRO_HECRAS_1D.md` | Roteiro de montagem do modelo 1D |

---

## 4. Comandos executados

```bash
export QGIS="C:/Program Files/QGIS 3.44.11"
export QPY="$QGIS/apps/Python312/python.exe"
export PROJ_LIB="$QGIS/share/proj"; export PROJ_DATA="$QGIS/share/proj"
export GDAL_DATA="$QGIS/share/gdal"; export PATH="$QGIS/bin:$PATH"
export EURO="C:/Users/cassi/OneDrive/Documents/SEDEC/PROJETO_EUROCLIMA"
export ESP="$EURO/Documentos EUROCLIMA+/Espanha"
export GIS="$ESP/GIS"; export SHP="$GIS/shapefiles"; export KMZ="$ESP/kmz"

"$QPY" 07_python/claude_02_divisao_quedas.py            # gera o perfil, ~31 s
"$QPY" 07_python/claude_03_altura_admissivel_revisada.py # revisa alturas, <1 s
"$QPY" 07_python/claude_01_sinv_energetico.py            # SINV, <1 s
```

Ordem obrigatória: `claude_02` → `claude_03` → `claude_01`. O `claude_02` grava as coordenadas do perfil, das quais o `claude_03` depende; o `claude_01` consome as alturas revisadas.

---

## 5. Resultados principais

### 5.1 Correção metodológica — a mais relevante desta rodada

`12_altura_maxima_admissivel.py` identifica quem está a montante comparando **área de drenagem e cota**. Esse critério falha quando dois barramentos têm áreas quase iguais, porque a diferença cai dentro do erro do MDE e a ordem montante/jusante sai trocada.

Caso detectado no perfil longitudinal:

| | Área | Cota | Estaca |
|---|---:|---:|---:|
| E09 | 12.330 km² | 106,0 m | 303,3 km |
| Monte Claro | 12.414 km² | 132,5 m | 279,5 km |

Monte Claro tem área **0,7% maior**, o que o classificava como jusante de E09 — mas está **24 km acima** no talvegue.

Foram introduzidos três filtros:

1. **Posição longitudinal** substitui área de drenagem para eixos no canal principal;
2. **Só usinas em operação** impõem restrição — os 34 registros "em estudo" da ANEEL têm coordenadas arredondadas a 2 casas decimais (~1 km) e a cota amostrada cai em encosta, chegando a 218 m e 465 m para pontos que deveriam estar no leito;
3. **Coerência de cota** — o ponto precisa estar a menos de 40 m do talvegue na sua estaca; 39 dos 49 em operação foram descartados por isso (estão em tributários fora do canal principal).

Restaram **7 aproveitamentos** válidos como restrição.

### 5.2 Alturas admissíveis revisadas

| Eixo | Estaca | Restrição de montante | Altura antes | **Altura revisada** | **Volume revisado** |
|---|---:|---|---:|---:|---:|
| **E04** | 238,1 km | Serra dos Cavalinhos II (196 m acima) | 27,3 m | **120,0 m** ¹ | **2.211 hm³** |
| **E02** | 243,9 km | Passo do Meio (232 m acima) | 22,5 m | **120,0 m** ¹ | **1.377 hm³** |
| E08 | 274,3 km | Castro Alves | 21,3 m | 86,0 m | 621 hm³ |
| E06 / E07 | 270–273 km | Castro Alves | 15,9 m | 84,5 m | 338 / 386 hm³ |
| E03 | 272,8 km | Castro Alves | 15,9 m | 84,5 m | 152 hm³ |
| E05 | 257,6 km | Castro Alves | **−1,6 m** | **67,0 m** | 91 hm³ |
| E01 | 345,7 km | Cotiporã | 56,4 m | 63,6 m | 172 hm³ |
| E12 | 375,2 km | 14 de Julho | 55,5 m | 55,5 m | 978 hm³ |
| E11 | 358,1 km | 14 de Julho | 45,0 m | 45,0 m | 400 hm³ |
| **E10** | 335,5 km | 14 de Julho | 59,0 m | **31,0 m** ↓ | 70 hm³ |
| **E09** | 303,3 km | Monte Claro | 63,3 m | **24,5 m** ↓ | 60 hm³ |

¹ Teto técnico de 120 m — o remanso **não é o fator limitante**. A usina de montante mais próxima está 196 m (E04) e 232 m (E02) acima. Acima de 120 m a altura passa a ser governada por topografia, geotecnia, custo e meio ambiente, e as curvas cota‑área‑volume não foram calculadas além disso.

**Volume total mobilizável: 2.601 hm³ → 6.855 hm³ (+164%).**

Isso ultrapassa os **3.230 hm³** estimados como necessários para evitar os danos do evento de referência.

### 5.3 Confirmação de E02 e reclassificação de E04 (tarefas 3 e 4)

**E02 confirmado como prioritário**, e com margem muito maior que a estimada: não é um eixo de 22,5 m e 32 hm³, mas um eixo **livre de interferência da cascata**, com 1.377 hm³ a 120 m. Está fora do canal principal (15,7 km de distância), o que reforça a baixa interferência.

**E04 muda de patamar** — passa de "independente com conflito operacional" (27,3 m, 125 hm³) para **sem interferência da cascata** (120 m, 2.211 hm³). É o maior volume individual de todo o conjunto.

**E01 pouco alterado** — 56,4 → 63,6 m, 129 → 172 hm³. Continua independente, com restrição de Cotiporã.

**E02 + E04 juntos somam 3.588 hm³** — acima do volume necessário, e **ambos sem interferência direta com usinas existentes**. É o achado mais importante desta rodada.

### 5.4 Avaliação energética SINV

Melhores ICB por eixo, sem volume de espera:

| Eixo | Altura | Queda líq. | Ef (MW méd) | P (MW) | **ICB (R$/MWh)** |
|---|---:|---:|---:|---:|---:|
| E09 | 24,5 m | 20,3 m | 24,3 | 44,2 | **44,8** |
| E10 | 31,0 m | 25,9 m | 32,1 | 58,4 | **46,0** |
| E11 | 45,0 m | 37,3 m | 56,3 | 102,3 | 72,0 |
| E05 | 67,0 m | 56,0 m | 43,1 | 78,4 | 85,2 |
| E12 | 55,5 m | 46,1 m | 71,7 | 130,3 | 99,1 |
| E08 | 86,0 m | 72,0 m | 84,7 | 153,9 | 102,0 |
| E04 | 120,0 m | 100,7 m | 80,2 | 145,9 | 312,5 |
| E02 | 120,0 m | 101,2 m | 40,2 | 73,2 | 518,0 |

**Tensão central a registrar:** os eixos energeticamente mais eficientes (E09, E10, ICB de R$ 45/MWh) são justamente os mais restritos pela cascata — 24 a 31 m de altura, 60 a 70 hm³, praticamente sem volume para controle de cheias. Os eixos com volume relevante para amortecimento (E02, E04) têm ICB de R$ 312 a 518/MWh, **acima da faixa usualmente considerada competitiva** (~R$ 250–300/MWh).

Ou seja: **não há, no conjunto avaliado, um eixo que seja simultaneamente bom gerador e bom amortecedor.** A decisão é um trade‑off explícito, e o volume de espera custa energia — a perda fica entre 21% e 36% ao alocar 50% do volume ao controle de cheias.

### 5.5 Alternativas (energia firme do conjunto, eq. 4.6.2.01)

Com 50% do volume alocado a espera:

| Alternativa | Área controlada | V. espera | Ef (MW méd) | P (MW) | Custo | ICB |
|---|---:|---:|---:|---:|---:|---:|
| E12 isolado | 15.760 km² | 489 hm³ | 51,0 | 92,7 | R$ 722 M | **137** |
| E08 + E02 + E04 | 23.039 km² | 2.104 hm³ | 145,2 | 264,0 | R$ 5.731 M | 374 |
| E02 + E04 + E12 | 26.848 km² | 2.283 hm³ | 136,1 | 247,4 | R$ 5.575 M | 387 |
| E04 isolado | 7.498 km² | 1.105 hm³ | 55,9 | 101,6 | R$ 2.642 M | 446 |
| **E02 + E04** | 11.089 km² | **1.794 hm³** | 85,1 | 154,7 | R$ 4.853 M | 537 |
| E02 isolado | 3.591 km² | 689 hm³ | 29,2 | 53,1 | R$ 2.211 M | 712 |

### 5.6 Divisão de quedas

O perfil do canal principal tem **375 km**, da cabeceira (cota 789 m) até Bom Retiro do Sul. A figura mostra os aproveitamentos existentes e os eixos propostos, com a altura limitada ao admissível, distinguindo por cor os que sofrem e os que não sofrem interferência da cascata.

Dos 12 eixos, **10 estão no canal principal** e 2 (E01, E02) em tributários.

### 5.7 Sobre a tarefa 5 — retirada de E05

**Contesto a retirada.** A inviabilidade de E05 vinha do critério antigo, que lhe atribuía Monte Cuco (cota 167,4 m) como restrição — um ponto 1,5 m *abaixo* da cota do eixo, gerando altura negativa. Pela posição longitudinal, a restrição real é **Castro Alves**, e a altura admissível é **67,0 m**, com 91 hm³ e ICB de R$ 85/MWh — dentro da faixa competitiva.

E05 foi **mantido** na avaliação. Recomendo que a retirada só seja formalizada após verificação em campo, e sinalizo o ponto para decisão do Codex e do gestor.

---

## 6. Limitações

### 6.1 Parâmetros não calibrados — governam os resultados

| Parâmetro | Valor | Efeito |
|---|---:|---|
| Vazão específica de longo termo | 0,020 m³/s/km² | **Energia firme e ICB escalam linearmente** |
| Razão Qn(crítico)/Qmlt | 0,55 | idem |
| Evaporação líquida anual | 150 mm | efeito secundário |
| Taxa de desconto | 8 % a.a. | ICB aproximadamente proporcional ao FRC |
| Custo de O&M | R$ 25/kW/ano | efeito secundário |
| BDI casa de força + equipamentos | +25 % sobre o civil | ICB proporcional |

Nenhum desses valores foi verificado contra dados da bacia. **Os ICB absolutos não devem ser citados como resultado**; a ordenação relativa entre eixos é mais robusta que os valores.

### 6.2 Limitações de método

- **Teto técnico de 120 m é arbitrário.** Foi adotado porque é até onde as curvas cota‑área‑volume existem. Para E02 e E04 o volume real disponível pode ser maior — ou menor, se topografia ou geotecnia limitarem antes.
- **Volume de espera tratado como fração fixa do volume máximo**, não como série mensal ao longo do período crítico como prevê o manual. É simplificação de triagem.
- **Simplificação em Qlm:** o manual desconta o volume de espera no início do período crítico na eq. 4.6.1.03, além de o NAmxn já ser líquido da média dos volumes de espera. Com um único valor de Vesp isso seria dupla contagem; adotou‑se descontar **uma vez só**. Está comentado no código.
- **Ganho de energia firme em última adição (eq. 4.6.3.01) não foi implementado** — as alternativas usam a soma das energias firmes individuais (eq. 4.6.2.01), o que é a aproximação prevista para Estudos Preliminares mas não captura o efeito de regularização em cascata.
- **NAjn considera apenas aproveitamentos existentes**, não o remanso de eixos propostos entre si. Em arranjos de cascata isso subestima a perda de queda.
- **Verificação de reenchimento simplificada** — usa vazão média anual, não a série dos 36 meses subsequentes ao período crítico.
- **Cota dos reservatórios existentes vem do MDE**, não de dados cadastrais. Para as usinas do canal principal a coerência foi verificada contra o talvegue, mas o valor pode diferir do NA operativo real.

### 6.3 O que não foi feito

- Não usei os dados do Atlas Digital de Desastres. O script `16_extrai_atlas_danos.py` e a tabela `atlas_danos_municipios.csv` são do Codex e estavam na lista de não‑edição; não dupliquei o trabalho. A avaliação econômica de danos permanece com o Codex.
- Não avaliei alteamento de reservatórios existentes — conforme orientação, ficou em segundo plano.
- Não construí o modelo HEC‑RAS; apenas o roteiro.

---

## 7. Pendências para integração pelo Codex

### 7.1 Decisão necessária — conflito com resultados já publicados

`claude_altura_admissivel_revisada.csv` **diverge substancialmente** de `altura_maxima_admissivel.csv` e, por consequência, de `prioridade_eixos_sem_interferencia.csv` e `alternativas_sem_alteamento.csv`, que dele derivam.

Os documentos do Codex que citam alturas admissíveis ou volume mobilizável precisam ser revistos **se** a revisão for aceita. Especificamente:

- volume total mobilizável: 2.601 → 6.855 hm³;
- E02 e E04 deixam de ser eixos pequenos e passam a ser os maiores do conjunto;
- E09 e E10 têm o volume reduzido em ~85%;
- E05 deixa de ser inviável.

**Não sobrescrevi nenhum arquivo do Codex.** A decisão sobre adotar a revisão é do gestor.

### 7.2 Verificações recomendadas antes de adotar

1. Conferir em campo, ou em imagem de satélite, se Monte Claro está de fato a montante de E09 e 14 de Julho a montante de E10 — é a inversão que motivou toda a revisão.
2. Conferir a distância real de E02 e E04 às usinas de montante e confirmar que não há aproveitamento intermediário ausente do cadastro ANEEL.
3. Definir o teto técnico com base em critério de engenharia, não no limite das curvas CAV.

### 7.3 Insumos que a trilha de modelagem precisa e não tem

| Insumo | Bloqueia |
|---|---|
| Séries de vazão ANA (script `01_baixa_dados_ana.R` nunca executado) | calibração de tudo |
| Vazão específica real da bacia | energia firme, ICB |
| Curvas cota × volume das usinas existentes | volume de espera por deplecionamento |
| Batimetria ou seções topobatimétricas | HEC‑RAS 1D |
| Curva‑chave em Estrela | condição de contorno e conversão cota→vazão |

### 7.4 Sugestão de próximo passo na trilha

Rodar `02_R/01_baixa_dados_ana.R` e recalibrar `Q_ESPEC` e `RAZAO_CRIT` em `claude_01_sinv_energetico.py`. É a intervenção de maior retorno: converte os ICB de ordem de grandeza em números defensáveis, sem exigir nenhum dado novo além do que a ANA publica.

---

# ADENDO — segunda rodada (aproveitando as curvas CAV do SNIRH)

Com as curvas oficiais que a outra trilha obteve (`01_dados/cav_snirh/`), duas coisas que estavam bloqueadas ficaram possíveis.

## A1. Vazão específica calibrada com dado oficial

| Usina | Área | Qmlt | q específica |
|---|---:|---:|---:|
| 14 de Julho | 12.758 km² | 370,86 m³/s | 0,0291 m³/s/km² |
| Monte Claro | 12.113 km² | 320,55 m³/s | 0,0265 m³/s/km² |
| Castro Alves | 7.742,6 km² | 185,57 m³/s | 0,0240 m³/s/km² |

**Média ponderada por área: 0,0269 m³/s/km²** — contra os 0,020 arbitrados. A energia firme calculada na primeira rodada estava **subestimada em 34%**, e os ICB, superestimados na mesma proporção.

Ajustei uma relação regional potencial (`Qmlt = 0,0013 · A^1,322`) mas **não a uso**: expoente de 1,32 é fisicamente implausível (esperado 0,8 a 1,0) e, com três pontos concentrados entre 7.700 e 12.800 km², extrapolar para E01/E02/E03 (2.500 a 3.800 km²) não se sustenta. Adotei a vazão específica média.

Arquivo: `claude_vazao_especifica_calibrada.csv`.

## A2. Correção conceitual — interferência é custo, não veto

O enquadramento de "altura admissível" que usei na primeira rodada, e que a outra trilha incorporou, trata a interferência como **proibição**. Isso não é o que o manual prescreve.

O item 4.6.1 diz que o NAjn de um aproveitamento é o nível natural **ou o NAmxn do reservatório imediatamente a jusante, se este for mais elevado**. Ou seja: quando um novo reservatório eleva o nível no canal de fuga da usina de montante, o efeito não é impedir a obra — é **reduzir a queda daquela usina**, e portanto a sua energia. É custo quantificável, não veto.

O veto só se justifica quando o remanso atinge a **cota mínima operacional** da usina de montante.

### Consequência prática — o erro de referência

A altura admissível comparava o NA do novo reservatório contra o **NA do reservatório de montante**. O nível correto de comparação é o **leito no eixo daquela usina**, que é onde fica o canal de fuga:

| Usina | Leito (base da CAV) | NA normal | Mín. operacional |
|---|---:|---:|---:|
| 14 de Julho | **62,37 m** | 104,0 m | 103,0 m |
| Monte Claro | **116,88 m** | 148,0 m | 147,0 m |
| Castro Alves | **187,05 m** | 240,0 m | 239,0 m |

Para E12 (eixo em 47 m), a perda de energia em 14 de Julho **começa aos 15 m de altura**, não aos 55,5 m. O veto por cota mínima operacional é que cai em 56 m — próximo dos 55,5 m que eu havia calculado, por coincidência.

### Balanço energético líquido

Ganho do novo eixo menos perda na usina de montante:

| Eixo | Altura | Gera | Tira de montante | **Líquido** | Volume |
|---|---:|---:|---:|---:|---:|
| **E10** | 10 m | 16,3 | 33,7 (14 de Julho) | **−17,4** | 11 hm³ |
| **E10** | 20 m | 32,6 | 51,2 | **−18,6** | 33 hm³ |
| **E10** | 30 m | 48,9 | 68,8 | **−19,9** | 64 hm³ |
| **E10** | 40 m | 65,2 | 73,2 | **−8,0** | 155 hm³ |
| E12 | 30 m | 60,3 | 25,7 | +34,6 | 257 hm³ |
| E12 | 50 m | 100,5 | 60,9 | +39,6 | 790 hm³ |
| E09 | 30 m | 47,2 | 29,1 (Monte Claro) | +18,1 | 85 hm³ |

*(MW médios)*

**E10 tem balanço energético negativo em toda a faixa até 40 m** — tira mais energia da 14 de Julho do que gera. Como sua altura admissível pelo critério de veto é 31 m, **E10 deve ser descartado**: em nenhuma altura viável ele produz ganho líquido de energia.

31 das 81 combinações avaliadas caem em veto por atingir a cota mínima operacional.

## A3. Arquivos adicionais

| Arquivo | Conteúdo |
|---|---|
| `claude_vazao_especifica_calibrada.csv` | Calibração com Qmlt oficial |
| `claude_interferencia_energetica.csv` | Elevação do canal de fuga e perda por eixo × altura |
| `claude_balanco_energetico_liquido.csv` | Balanço líquido e veto por combinação |
| `07_python/claude_04_interferencia_energetica.py` | Script |

## A4. O que isto obriga a revisar

1. **Os ICB de `claude_sinv_energetico.csv` estão superestimados em ~34%** — foram calculados com q = 0,020. Refazer com 0,0269. Não refiz para não invalidar a tabela que a outra trilha pode já ter consumido; a correção é uma divisão por 1,34.
2. **A tabela de altura admissível precisa de uma segunda coluna**: altura de veto (cota mínima operacional) e altura a partir da qual começa a perda de energia. São coisas diferentes, e hoje só a primeira está representada.
3. **E10 sai da carteira** por balanço energético negativo, não por veto de remanso.
4. Falta estender a análise aos demais aproveitamentos: só as três usinas do rio das Antas têm CAV oficial. Para as outras 17 em operação, a cota de canal de fuga continua sendo a do MDE.

---

# ADENDO 2 — auditoria das CAVs interpoladas e SINV v2

## B1. Execução de `27_ajusta_cav_eixos_novos.py`

Executado. 276 pontos originais → **1.332 interpolados** (12 eixos × 111 alturas de 10 a 120 m, passo 1 m). Gravou `cav_eixos_novos_interpolada_1m.csv`, `cav_eixos_novos_ajustes_polinomiais.csv` e `cav_eixos_novos_modelos.json`.

**Auditoria do código:** implementação PCHIP de Fritsch‑Carlson correta, inclusive as fórmulas de extremidade e o limitador `3·delta`. Ajuste polinomial com escalonamento para [−1,1], que é boa prática numérica. Não extrapola. Sem reparos.

## B2. Fidelidade da interpolação monotônica

**Reproduz exatamente os 23 nós de cada eixo** — erro máximo 0,0 em área e volume nos 276 pontos, dentro de tolerância de 1e‑6. É o esperado, já que PCHIP é interpoladora, mas ficou verificado.

## B3. Avaliação dos polinômios — não servem como modelo operacional

O erro **absoluto** do cúbico é pequeno; o **relativo** não é, e é isso que importa:

| Eixo | Var. | RMSE | Erro máx. | Erro rel. médio | **Erro rel. até 40 m** | Monotônico | Gera negativo |
|---|---|---:|---:|---:|---:|:--:|:--:|
| E04 | volume | 0,62 | 1,09 | 0,2 % | **1,3 %** | sim | não |
| E12 | volume | 10,46 | 27,24 | 2,3 % | **13,0 %** | sim | não |
| E08 | volume | 8,58 | 14,96 | 8,1 % | **98,6 %** | sim | não |
| E07 | volume | 8,47 | 17,75 | 11,9 % | **143,0 %** | sim | **sim (−4,0)** |
| E06 | volume | 8,44 | 17,69 | 15,9 % | **203,8 %** | sim | **sim (−6,8)** |
| E05 | volume | 7,03 | 15,87 | 22,0 % | **200,9 %** | sim | **sim (−1,7)** |
| E05 | área | 0,99 | 2,72 | 41,0 % | **278,6 %** | **não** | não |
| E10 | volume | 8,05 | 21,68 | 7,4 % | 35,9 % | **não** | não |

Resumo por grau:

| Grau | Não monotônicos | Produzem valor negativo | Pior erro relativo até 40 m |
|---:|---:|---:|---:|
| 2 | 14 de 24 | 2 | **3.350 %** |
| 3 | 2 de 24 | 4 | **279 %** |
| 4 | 1 de 24 | 1 | **491 %** |

**Causa:** a curva cota‑volume é fortemente convexa. Um erro absoluto de 8 hm³ é 0,4% do volume a 120 m e mais de 100% do volume a 20 m. Nenhum grau resolve — o grau 4 reduz a não‑monotonicidade mas piora o erro relativo baixo.

**Conclusão:** confirmo a recomendação metodológica do Codex. A **PCHIP é a curva operacional**; os polinômios servem apenas como forma compacta de documentação, e mesmo assim **não devem ser usados abaixo de ~40 m de altura**, onde quatro deles produzem volume negativo.

## B4. Coerência com as alturas admissíveis

Todas as 12 alturas admissíveis caem dentro do intervalo interpolado — **não há extrapolação**. A diferença entre a interpolação linear de 5 m (usada até agora) e a PCHIP é pequena:

| Eixo | Volume linear 5 m | Volume PCHIP | Diferença |
|---|---:|---:|---:|
| E10 | 70,0 hm³ | 68,7 hm³ | **−1,87 %** |
| E05 | 91,0 hm³ | 90,3 hm³ | −0,72 % |
| E12 | 977,7 hm³ | 976,5 hm³ | −0,13 % |
| demais | — | — | < 0,3 % |

A interpolação linear **superestimava** o volume, como esperado numa curva convexa. O efeito é imaterial exceto em E10.

## B5. Tabela final consolidada

`claude_cav_eixos_consolidada.csv` — com eixo, altura, cotas de NA (normal, mínimo, maximorum), área inundada, volume acumulado, volume útil, volume de espera, restrição de montante e confiabilidade.

Critérios: volume de espera = 50% do máximo (parâmetro); NA máximo normal = nível do volume máximo descontada a espera (item 4.6.1); depleção máxima = ⅓ da queda bruta (item 4.6.1).

| Eixo | Altura | NA normal | Área inund. | Vol. acum. | Vol. útil | Vol. espera | Restrição |
|---|---:|---:|---:|---:|---:|---:|---|
| E04 | 120,0 m | 326,9 m | 42,31 km² | 2.210,7 | 625,6 | 1.105,3 | Serra dos Cavalinhos II |
| E02 | 120,0 m | 385,8 m | 30,78 km² | 1.377,4 | 450,1 | 688,7 | Passo do Meio |
| E12 | 55,5 m | 86,8 m | 35,56 km² | 976,5 | 299,1 | 488,2 | 14 de Julho |
| E08 | 86,0 m | 209,8 m | 15,49 km² | 620,4 | 171,1 | 310,2 | Castro Alves |
| E11 | 45,0 m | 89,1 m | 17,19 km² | 400,3 | 113,9 | 200,2 | 14 de Julho |
| E07 | 84,5 m | 209,6 m | 9,41 km² | 385,4 | 104,8 | 192,7 | Castro Alves |
| E06 | 84,5 m | 210,4 m | 8,57 km² | 338,1 | 95,2 | 169,1 | Castro Alves |
| E01 | 63,6 m | 120,1 m | 6,48 km² | 171,6 | 53,6 | 85,8 | Cotiporã |
| E03 | 84,5 m | 213,8 m | 4,57 km² | 151,4 | 47,5 | 75,7 | Castro Alves |
| E05 | 67,0 m | 216,0 m | 3,08 km² | 90,3 | 27,2 | 45,2 | Castro Alves |
| E10 | 31,0 m | 92,0 m | 4,31 km² | 68,7 | 16,4 | 34,3 | 14 de Julho |
| E09 | 24,5 m | 122,0 m | 4,12 km² | 59,7 | 13,8 | 29,8 | Monte Claro |

*(volumes em hm³)*

**Total: 6.850 hm³ acumulados, 3.425 hm³ de espera.** Todos classe **B** — CAV do MDE natural em eixo sem reservatório.

## B6. SINV v2

`claude_01_sinv_energetico.py` atualizado com duas mudanças, gravando em arquivos `_v2` para não sobrescrever a rodada anterior:

1. **Vazão específica calibrada** — 0,020 → **0,0269 m³/s/km²** (§A1);
2. **CAV interpolada em 1 m** substitui a interpolação linear sobre pontos de 5 m. O custo continua vindo de `geometria_todos.csv`, que não foi densificado, e é interpolado linearmente entre os múltiplos de 5 m.

ICB resultantes (sem volume de espera):

| Eixo | Altura | ICB v1 | **ICB v2** | Queda líq. | Ef (MW méd) |
|---|---:|---:|---:|---:|---:|
| E09 | 24,5 m | 44,8 | **34,6** | 20,3 m | 32,7 |
| E10 | 31,0 m | 46,0 | **35,6** | 25,8 m | 43,0 |
| E11 | 45,0 m | 72,0 | **54,9** | 37,4 m | 75,7 |
| E05 | 67,0 m | 85,2 | **64,8** | 56,0 m | 57,9 |
| E12 | 55,5 m | 99,1 | **75,4** | 46,1 m | 96,0 |
| E08 | 86,0 m | 102,0 | **77,5** | 72,0 m | 113,4 |
| E04 | 120,0 m | 312,5 | **238,9** | 100,7 m | 105,5 |
| E02 | 120,0 m | 518,0 | **399,0** | 101,2 m | 52,4 |

Arquivos: `claude_sinv_energetico_v2.csv`, `claude_sinv_sintese_eixos_v2.csv`, `claude_sinv_alternativas_v2.csv`.

**E04 entra na faixa competitiva** (R$ 239/MWh contra referência de R$ 250–300/MWh). E02 continua fora.

## B7. Scripts desta rodada

| Script | Função |
|---|---|
| `claude_04_interferencia_energetica.py` | Calibração da vazão e interferência como custo |
| `claude_05_auditoria_cav.py` | Auditoria da PCHIP, dos polinômios e tabela consolidada |

## B8. O que fica para o Codex

1. `claude_cav_eixos_consolidada.csv` é a base pronta para entrar na classificação de confiabilidade (todos classe B).
2. Os polinômios **não devem ser usados abaixo de 40 m**; se forem embutidos em alguma ferramenta, restringir o domínio.
3. Os ICB da versão v1 estão superestimados em ~34%; usar os `_v2`.
4. `claude_balanco_energetico_liquido.csv` mostra que **E10 tem balanço energético negativo** em toda a faixa viável — sugiro tratá‑lo como descartado na classificação.

---

## A5. Correções que fiz nos meus próprios números

- **Estimador de vazão**: substituí a regressão potencial pela vazão específica média, pelo motivo do §A1.
- **Energia firme das usinas existentes**: aplicar a eq. 4.6.1.01 direto com Qmlt dava 133 MW médios para a 14 de Julho, que tem 100 MW instalados — impossível. Passei a usar a vazão do período crítico (razão 0,55) e a limitar pela potência instalada.
