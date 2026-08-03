# Relatório C1–C3 — roteamento, séries da ANA e calibração

**Trilha de modelagem hidráulica e energética · 01/08/2026**
**Arquivos compartilhados tocados:** nenhum. Nenhum `.qmd`. `10_eixos_cascata.py` não editado.
**Único arquivo pré-existente alterado:** `02_R/01_baixa_dados_ana.R` — correção de resolução de caminho (era meu, estava quebrado).

---

## Resumo executivo

**A pergunta central foi respondida.** Volume de espera se converte em redução de pico, mas **nenhuma alternativa leva o pico em Estrela abaixo do limiar de dano**.

| Alternativa | % da bacia | Volume usado | Pico resultante | **Redução** |
|---|---:|---:|---:|---:|
| E02 + E04 + E12 | 81,1 % | 2.366 hm³ | 6.328 m³/s | **61,2 %** |
| E02 + E04 + E08 | 61,5 % | 1.871 hm³ | 8.411 m³/s | 48,4 % |
| **E02 + E04** | 57,0 % | 1.694 hm³ | 9.272 m³/s | **43,1 %** |
| E04 isolado | 38,6 % | 1.148 hm³ | 11.541 m³/s | 29,2 % |
| E12 isolado | 81,1 % | 976 hm³ | 16.267 m³/s | **0,2 %** |

*Regra de barragem seca, parâmetros calibrados. Pico natural de referência: 16.299 m³/s.*

**Nenhuma das 30 combinações testadas atinge os 4.000 m³/s** estimados como limiar de dano relevante.

---

## 1. C2 — séries da ANA obtidas

O script em R retornava "sem dados" para todos os postos. **O endpoint funciona** — o problema era o parser, que procurava o elemento `<DadosHidrometereologicos>`. A resposta real usa `<SerieHistorica>` com atributos, e os valores diários vêm em `Vazao01`..`Vazao31` por registro mensal.

Reescrevi em Python (`claude_c2_baixa_ana.py`). Séries obtidas:

| Posto | Tipo | Registros | Período | Anos | Máxima |
|---|---|---:|---|---:|---:|
| **Muçum** (86510000) | vazão | 31.440 | 1940–2026 | 86,2 | **15.092 m³/s** |
| Encantado (86720000) | vazão | 24.530 | 1941–2026 | 84,3 | 14.003 m³/s |
| Passo Tainhas (86560000) | vazão | 31.188 | 1939–2026 | 86,4 | 1.548 m³/s |
| Bento Gonçalves (86440000) | vazão | 24.714 | 1940–2007 | 67,7 | 2.762 m³/s |
| **Estrela** (86879300) | vazão | 1.063 | 2020–2023 | **3,1** | **17.261 m³/s** |
| Lajeado antigo (86870000) | cota | 16.880 | 1939–1986 | 47,3 | — |

### 1.1 Áreas oficiais — correção de um erro meu

Obtidas do `HidroInventario` da ANA:

| Posto | Área oficial | Eu vinha usando |
|---|---:|---:|
| Muçum | **16.000 km²** | 12.000 (estimado) |
| **Estrela (posto)** | **22.472 km²** | — |
| Encantado | 19.100 km² | — |

**O posto de Estrela drena 22.472 km², não os 19.440 km² do ponto de análise** — que é o limite de montante do trecho modelado, uma seção distinta. O pico observado precisa ser transposto entre elas, e eu não estava fazendo isso.

### 1.2 Encantado é inutilizável nos anos de cheia

| Ano | Dias com dado | Máxima registrada |
|---|---:|---:|
| 2023 | **245** | 8.080 m³/s |
| 2024 | **223** | 10.519 m³/s |

Falhas de mais de um terço do ano, justamente nos eventos de interesse. Os máximos não são válidos — provavelmente o sensor foi perdido durante a cheia. Foram **descartados** pelo filtro de cobertura mínima (300 dias).

---

## 2. C3 — parâmetros calibrados

| Parâmetro | Antes (arbitrado) | **Calibrado** | Δ | Fonte |
|---|---:|---:|---:|---|
| Q_PICO | 18.000 m³/s | **16.300 m³/s** | −9,4 % | posto 86879300, transposto |
| LAMINA_MM | 260 mm | **227 mm** | −12,7 % | integração do hidrograma |
| Q_BASE | 600 m³/s | **926 m³/s** | +54 % | percentil 10 da janela |
| **TR_EVENTO** | **100 anos** | **333 anos** | **+233 %** | Gumbel L‑momentos, 86 anos |
| CV_GUMBEL | 0,45 | **0,526** | +17 % | máximas anuais de Muçum |

### 2.1 O pico e a lâmina estavam razoáveis

O hidrograma sintético que eu vinha usando errava por menos de 13% no pico e na lâmina. É uma validação do método.

### 2.2 O tempo de retorno estava muito errado

Pela série de 86 anos de Muçum, ajuste de Gumbel por momentos‑L:

| TR | Q em Muçum |
|---:|---:|
| 100 anos | 12.730 m³/s |
| 200 anos | 14.091 m³/s |
| 500 anos | 15.886 m³/s |

O evento de setembro de 2023 (15.092 m³/s) tem **TR de 333 anos**, não 100. O de maio de 2024 (13.963 m³/s), **TR de 187 anos**.

**Consequência direta:** o dano esperado anual (EAD) calculado com TR = 100 está **superestimado**. Um evento três vezes mais raro contribui três vezes menos para o EAD. Isso afeta toda a análise custo‑benefício e reduz o benefício das alternativas.

### 2.3 Setembro de 2023 foi maior que maio de 2024

Em Muçum, com série completa nos dois anos:

| Evento | Data do pico | Vazão |
|---|---|---:|
| **set/2023** | 05/09/2023 | **15.092 m³/s** |
| mai/2024 | 02/05/2024 | 13.963 m³/s |

O estudo vem chamando o evento de referência de "cheia de 2024". **Em Muçum o maior foi o de 2023.** O evento de referência precisa ser explicitado no relatório — as duas escolhas dão volumes e picos diferentes.

Lâminas escoadas em Muçum: **343 mm** em set/2023 e **446 mm** em mai/2024. O evento de 2024 teve **mais volume**, apesar do pico menor — o que importa para dimensionamento de reservatório.

### 2.4 O expoente de transposição é anômalo — e importa

Par observado no mesmo evento de 2023:

| Posto | Área | Vazão |
|---|---:|---:|
| Muçum | 16.000 km² | 15.092 m³/s |
| Estrela | 22.472 km² | 17.261 m³/s |

Razão de vazão **1,144** para razão de área **1,405** → expoente implícito de **0,395**, muito abaixo do 0,85 usualmente adotado.

Duas hipóteses, com consequências opostas:

- **(a) Forte amortecimento natural na planície** entre Muçum e Estrela. Se for isso, a planície já faz parte do trabalho que as barragens fariam, e o ganho marginal delas é menor.
- **(b) Incerteza na curva‑chave de Estrela.** O posto tem apenas 3,1 anos de vazão e 17.261 m³/s é quase certamente extrapolação muito além das medições. Se for isso, o pico real pode ser maior.

Vazões de projeto no ponto de análise pelas duas hipóteses:

| TR | Expoente 0,395 | Expoente 0,85 |
|---:|---:|---:|
| 100 anos | 13.749 m³/s | 15.022 m³/s |
| 500 anos | 17.157 m³/s | 18.746 m³/s |

**Resolver isso depende de medições de vazão em Estrela** — exatamente as 10 medições previstas no Eixo 1 do TR.

---

## 3. C1/C4 — roteamento verificado

Método: Puls de montante para jusante respeitando a topologia; afluência de cada eixo = efluentes dos imediatamente a montante + contribuição da área incremental; decomposição do hidrograma natural por área, de modo que a soma reproduza exatamente o natural.

### 3.1 A regra operativa domina o resultado

| Regra | Melhor redução |
|---|---:|
| Convencional (soleira livre) | **2,8 %** |
| Comportas com deplecionamento | 61,1 % |
| **Barragem seca** | **61,9 %** |

Confirma, agora com roteamento em cascata e parâmetros calibrados, o que a triagem já indicava: **barragem convencional é inócua** para eventos desta magnitude.

### 3.2 O achado de cascata

**E12 isolado reduz 0,2 % — praticamente nada.** Controla 81 % da bacia, mas seus 976 hm³ enchem antes do pico e o reservatório satura.

**E12 dentro de E02+E04+E12 leva a alternativa de 43,1 % para 61,2 %.** A diferença é que os eixos de montante já amorteceram a afluência antes que ela chegue a E12, que então não satura.

Ou seja: **o valor de E12 não está no seu volume, mas na sua posição** — e só se realiza se houver amortecimento a montante. Isoladamente ele não serve; em cascata, é o que fecha os 61 %.

### 3.3 O teto e o piso

| | Valor |
|---|---:|
| Redução máxima obtida | 61,9 % |
| Pico resultante | 6.213 m³/s |
| Limiar de dano estimado | 4.000 m³/s |
| Alternativas que atingem o limiar | **0 de 30** |

O piso é imposto pela parcela não controlada. Mesmo a carteira completa deixa 18,9 % da bacia sem controle.

### 3.4 Sensibilidade ao pico

| Pico de referência | E02+E04 | Carteira completa |
|---:|---:|---:|
| 10.000 m³/s | 34,2 % | 48,6 % |
| 14.000 m³/s | 40,7 % | 57,9 % |
| **16.300 m³/s** (calibrado) | **43,1 %** | **61,9 %** |
| 22.000 m³/s | 46,7 % | 66,3 % |

A eficácia **cresce** com a magnitude do evento — os reservatórios amortecem proporcionalmente mais em cheias maiores, dentro da faixa testada. A ordenação entre alternativas é estável.

---

## 4. O que isso muda para o relatório

1. **O TR de 333 anos reduz o EAD e o benefício das alternativas.** A análise custo‑benefício precisa ser refeita com a curva de frequência de Muçum. Isso é insumo direto para X7.

2. **O evento de referência precisa ser nomeado.** Setembro de 2023 (maior pico) ou maio de 2024 (maior volume)? A escolha muda o dimensionamento.

3. **E12 não pode ser avaliado isoladamente.** Sua ficha individual (976 hm³, 81 % da bacia) sugere um bom eixo; o roteamento mostra que sozinho não entrega nada. Vale um destaque no capítulo de alternativas.

4. **A recomendação de E02+E04 se sustenta, mas com ressalva.** Entregam 43,1 % de redução — resultado real, não desprezível. Mas não atingem o limiar de dano, o que reforça o enquadramento como **componente de arranjo híbrido**.

5. **O limiar de 4.000 m³/s continua não calibrado.** É o único parâmetro central ainda arbitrado, e depende do HEC‑RAS 1D com o cadastro de edificações.

---

## 5. Arquivos entregues

Todos em `06_resultados/CLAUDE/`:

| Arquivo | Conteúdo |
|---|---|
| `claude_c1_roteamento_alternativas.csv` | 30 combinações, parâmetros originais |
| `claude_c4_roteamento_calibrado.csv` | 30 combinações, parâmetros calibrados |
| `claude_c1_hidrogramas.csv` · `claude_c4_hidrogramas_calibrado.csv` | Séries do melhor arranjo |
| `claude_c1_sensibilidade_pico.csv` · `claude_c4_sensibilidade_calibrado.csv` | Sensibilidade ao pico |
| `claude_c2_series_resumo.csv` | Inventário das séries obtidas |
| `claude_c2_maximas_anuais.csv` | Máximas anuais por posto |
| `claude_c3_frequencia_mucum.csv` | Curva de frequência e transposição |
| `claude_c3_parametros_calibrados.csv` | **Parâmetros para adotar** |
| `claude_c3_hidrograma_observado.csv` | Lâminas e volumes dos eventos |

Séries brutas em `01_dados/ana_hidroweb/` (12 arquivos).

**Scripts:** `claude_c1_roteamento_alternativas.py`, `claude_c2_baixa_ana.py`, `claude_c3_calibra_evento.py`, `claude_c4_roteamento_calibrado.py`.

---

## 6. Ressalvas

**O limiar de dano (4.000 m³/s) segue arbitrado.** Todas as conclusões sobre "atingir o limiar" dependem dele.

**O expoente de transposição (0,395) é anômalo** e não foi resolvido — ver §2.4.

**A decomposição do hidrograma é proporcional à área**, ignorando a defasagem entre sub-bacias. O Rio Forqueta sozinho é 14,63 % da bacia e sua defasagem importa (item C6, ainda pendente).

**Volumes dos eixos são classe B**, derivados de MDE de 28,6 m.

**A área de Muçum (16.000 km²) é a oficial da ANA**, mas minha delineação D8 dá valores diferentes para seções próximas. A conciliação não foi feita.

---

## 7. Pendências da minha trilha

| # | Item | Situação |
|---|---|---|
| C5 | Casos HEC‑RAS 1D com os efluentes roteados | pronto para começar — depende de C1, que está feito |
| C6 | Defasagem dos tributários, especialmente o Forqueta | pendente |
| — | Reprocessar SINV com os parâmetros calibrados | pendente (era C4 na proposta; usei C4 para o roteamento calibrado) |
| — | Conciliar área de Muçum entre ANA e delineação D8 | pendente |
