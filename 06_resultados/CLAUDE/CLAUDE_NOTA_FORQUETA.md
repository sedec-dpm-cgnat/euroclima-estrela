# Nota — eixos exploratórios no rio Forqueta (FQ1 / FQ2)

Resposta ao `PLANO_FORQUETA_CODEX_CLAUDE.md`, coluna Claude, itens 1 a 6.
Data: 01/08/2026.

---

## 1. Resumo executivo

**Os eixos do Forqueta não se sustentam como medida de amortecimento, e FQ1 e FQ2
são mutuamente incompatíveis.** Três achados independentes convergem:

| Achado | Consequência |
|---|---|
| A defasagem medida entre o pico do Forqueta e o de Estrela é **0 dia** em 13 eventos | O ganho de FQ1 sobre ALT-J cai para **+0,7 pp** |
| O NA de FQ1 com 30 m (52,5 m) fica **12,5 m acima** da cota do eixo de FQ2 (40,0 m) | Os dois eixos **não podem coexistir** |
| A queda disponível é baixa e a área alagada grande | Melhor ICB de FQ1: **R$ 616/MWh**, contra referência de R$ 250–300/MWh |

**Ressalva que muda tudo:** o evento de 19/11/2023, o maior já registrado em
Estrela (17.261 m³/s) e justamente aquele em que os tributários de jusante
dominaram, **não tem dado no Forqueta** — há lacuna em Passo do Coimbra em
novembro de 2023. Ver seção 6.

---

## 2. Correção estrutural: o Forqueta está fora do domínio anterior

Todo o roteamento de C1/C4 tinha como exutório o início do trecho modelado,
19.440 km². O Forqueta deságua **abaixo** desse ponto:

```
19.440,0 (ponto de análise) + 2.845,6 (Forqueta) + 186,4 (margem) = 22.472,0 km² (posto de Estrela)
```

O fechamento é exato contra a área oficial do posto 86879300. Portanto, no
domínio de 19.440 km² os eixos do Forqueta seriam invisíveis. O roteamento foi
movido para o **posto de Estrela, 22.472 km²**.

**Consequência de projeto:** os eixos do Antas (E01–E12) e os do Forqueta
protegem trechos **complementares**. Muçum e Encantado dependem só do Antas;
Lajeado, Estrela e Bom Retiro do Sul recebem as duas contribuições. Nenhuma
alternativa com FQ1 altera o pico no ponto de análise (redução 0,0%), como
esperado de um tributário de jusante.

---

## 3. Armadilha de códigos — atenção ao integrar

O pipeline isolado em `01_dados/cav_forqueta/` **renumerou os eixos**:

| Pipeline Forqueta | Canônico | Área |
|---|---|---|
| `E01` | **FQ2** | 2.204,2 km² |
| `E02` | **FQ1** | 2.350,1 km² |
| `E03` | `E01` | 2.550,4 km² |
| `E04` | `E02` | 3.590,9 km² |
| … | … | … |

Os rótulos `#NN` do KMZ também mudaram, porque o índice de placemark se deslocou
ao acrescentar os arquivos FQ. **A única chave estável entre os dois pipelines é
a área de drenagem.** O de-para completo está em `claude_fq_mapa_codigos.csv`.
Integrar por código sem traduzir produzirá resultados silenciosamente errados —
`E02` no pipeline do Forqueta é FQ1, mas `E02` no canônico é um eixo do rio das
Antas com 3.591 km².

---

## 4. Séries do Forqueta obtidas (novidade)

`claude_fq_busca_posto.py` localizou postos que não estavam no conjunto de C2:

| Código | Nome | Área | Vazão |
|---|---|---:|---|
| 86745000 | **PASSO DO COIMBRA** | 791 km² | **68,7 anos, 97,8% consistido, até 2026** |
| 86780000 | BARRA DO FÃO | 2.077 km² | só cota — **sem vazão publicada** |
| 86700000 | Ponte Jacaré (arroio Jacaré) | 436 km² | 71,9 anos |

Verificação independente útil: o rendimento específico médio é **0,0275
m³/s/km²** em Passo do Coimbra e **0,0273** em Ponte Jacaré, contra os **0,0269**
calibrados nas UHEs do Antas para o SINV. O parâmetro `Q_ESPEC` está consistente.

**Pico de projeto do Forqueta, agora medido:** máxima de 1.292,3 m³/s em Passo do
Coimbra (2010), transposta para 2.845,6 km² com expoente 0,85 (fator 2,969) →
**3.837 m³/s**. Coincide com o Gumbel de TR 100 anos daquela série (1.289 m³/s).
O valor regionalizado que eu vinha usando (3.183 m³/s) era 17% baixo.

**Recomendação direta para o Eixo 1 do TR:** reativar a curva-chave de **Barra do
Fão** (2.077 km², 73% da bacia). É o posto adequado; hoje obriga a extrapolar
3,6× em área a partir de Passo do Coimbra.

---

## 5. Resultados do roteamento

Parâmetros: exutório no posto de Estrela; Antas com pico 16.300 m³/s e lâmina
227 mm (calibração C3/C4); Forqueta com pico 3.837 m³/s e tempo de pico próprio;
defasagem 0 h (medida). Regra de barragem seca, alturas FQ1 = FQ2 = 30 m.

Validação: pico natural em Estrela = **16.903 m³/s** contra máximo observado de
**17.261 m³/s** — diferença de **−2,1%**.

| Cenário | Volume total | Volume FQ | Pico Estrela | Redução | Satura |
|---|---:|---:|---:|---:|---|
| ALT-J sem Forqueta | 2.604,0 hm³ | — | 7.005 m³/s | **58,6%** | sim |
| ALT-J + FQ1 | 2.816,3 hm³ | 212,3 | 6.880 m³/s | **59,3%** | sim |
| ALT-J + FQ2 | 2.752,5 hm³ | 148,4 | 6.816 m³/s | **59,7%** | sim |
| ALT-J + FQ1 + FQ2 *(inviável)* | 2.833,5 hm³ | 229,5 | 6.880 m³/s | 59,3% | sim |
| **FQ1 isolado** | 212,3 hm³ | 212,3 | 17.012 m³/s | **−0,6%** | não |
| **FQ2 isolado** | 148,4 hm³ | 148,4 | 16.919 m³/s | **−0,1%** | sim |
| ALT-A (E02+E04) + FQ1 | 1.880,6 hm³ | 212,3 | 9.974 m³/s | 41,0% | não |

### Eficiência marginal

| | Ganho | Volume | pp por 100 hm³ |
|---|---:|---:|---:|
| ALT-J (eixos do Antas) | 58,6 pp | 2.604 hm³ | **2,25** |
| FQ1 sobre ALT-J | +0,7 pp | 212 hm³ | **0,33** |
| FQ2 sobre ALT-J | +1,1 pp | 148 hm³ | **0,74** |

FQ1 é cerca de **7× menos eficiente por hm³** que a carteira do Antas.

### Regra operativa

| Cenário | seca | comportas | convencional |
|---|---:|---:|---:|
| ALT-J sem Forqueta | 58,6% | 50,9% | 6,3% |
| ALT-J + FQ1 | 59,3% | 53,3% | 6,2% |
| FQ1 isolado | −0,6% | −0,1% | −0,1% |

A conclusão anterior se mantém: a **regra operativa domina**. Operação
convencional (reservatório cheio) entrega ~6% em qualquer arranjo.

### Por que FQ1 isolado chega a piorar

Com defasagem nula, reter o Forqueta e liberá-lo depois **desloca sua
contribuição para junto do pico do Antas**. É efeito real de operação não
coordenada, não artefato numérico. Reforça que qualquer barragem no Forqueta
exigiria operação conjunta com a cascata do Antas.

### Altura ótima

A varredura mostra cotovelo em **30 m** para FQ1: abaixo disso o reservatório
satura (21,0 hm³ a 15 m, 122,8 a 25 m); acima, o benefício estagna (215,3 hm³ a
30 m contra 1.833,5 a 70 m, com ganho praticamente idêntico). A área alagada a
30 m é de **21,6 km²** — expressiva, num vale largo.

---

## 6. Sensibilidade à defasagem — e a lacuna que importa

| Defasagem | −12 h | 0 h | +12 h | +24 h | +35 h |
|---|---:|---:|---:|---:|---:|
| Pico natural em Estrela (m³/s) | 16.650 | **16.903** | 17.910 | 19.641 | 20.292 |
| ALT-J sem Forqueta | 61,0% | **58,6%** | 52,5% | 51,0% | 50,4% |
| ALT-J + FQ1 | 58,8% | **59,3%** | 59,5% | 61,8% | 63,4% |
| Ganho de FQ1 | **−2,2 pp** | **+0,7 pp** | +7,0 pp | **+10,8 pp** | +13,0 pp |

**O valor de FQ1 depende inteiramente da defasagem.** E aqui está o problema:

- A defasagem **medida** em 13 eventos com dado simultâneo é de **0 dia**
  (`claude_fq_defasagem_medida.csv`). Contribuição do Forqueta ao pico de
  Estrela: mediana **10%**, faixa 6% a 20%.
- Mas o evento de **19/11/2023**, o maior já medido em Estrela, **não está
  nesses 13** — Passo do Coimbra tem lacuna em todo novembro de 2023.
- E os dados de Muçum e Estrela nesse evento mostram exatamente o padrão de
  defasagem positiva:

| Data | Muçum | Estrela |
|---|---:|---:|
| 18/11/2023 | 9.401 | 12.094 |
| 19/11/2023 | **9.069** ↓ | **17.261** ↑ |

Estrela subiu 5.167 m³/s enquanto Muçum **caía**. Praticamente 8.000 m³/s vieram
de jusante de Muçum, com defasagem de +1 dia.

**Portanto a evidência está dividida:** os 13 eventos medidos dizem defasagem 0 e
FQ1 quase inútil; o único evento que realmente importa aponta defasagem positiva,
onde FQ1 valeria +10,8 pp. **Resolver isso exige dado sub-diário em Barra do
Fão** — é o parâmetro mais sensível de todo o dimensionamento do Forqueta.

---

## 7. Interferência com aproveitamentos existentes

Verificação por **cota**, não por distância (`claude_fq_interferencia_pch.py`).

### 7.1 PCHs em operação no Forqueta — sem conflito

| Aproveitamento | Potência | Área | Cota |
|---|---:|---:|---:|
| Vale do Leite | 6,40 MW | 753,4 km² | 130,9 m |
| Salto Forqueta | 6,08 MW | 672,3 km² | 190,0 m |
| Rastro de Auto | 7,02 MW | 647,6 km² | 277,4 m |

Com 30 m de altura, o NA de FQ1 fica em 52,5 m e o de FQ2 em 70,0 m — muito
abaixo das três. **Nenhuma é afogada, nem mesmo com 70 m de altura.** Há ainda
seis sítios "em estudo" na bacia (cotas 135,7 a 347,5 m), também livres.

### 7.2 O conflito real é entre FQ1 e FQ2

| | Cota do eixo |
|---|---:|
| FQ1 (jusante, 2.350,1 km²) | 22,5 m |
| FQ2 (montante, 2.204,2 km²) | 40,0 m |
| **Desnível** | **17,5 m** |

FQ1 com 20 m já afoga o eixo de FQ2; com 30 m, o NA fica **12,5 m acima** dele.
Com a margem de 5 m para remanso, a altura máxima de FQ1 compatível com FQ2 é
**0 m** — ou seja, **são alternativas mutuamente exclusivas**, não combináveis.
Isso explica por que "ALT-J + FQ1 + FQ2" não acrescenta nada sobre "ALT-J + FQ1".

**Ressalvas.** `cota_terreno_m` é a cota do terreno no ponto, não o NA operativo
nem a cota da casa de força. Confirmar junto à CERTEL e à ANEEL. O remanso de FQ1
sobre a planície do Forqueta precisa ser calculado em regime permanente — cabe ao
Codex.

---

## 8. Energia / SINV

Mesmos parâmetros de `claude_01_sinv_energetico.py`. NAjn adotado como nível
natural (nenhum aproveitamento a jusante causa remanso no eixo).

FQ1, altura 30 m, Qmlt = 63,2 m³/s:

| Fração de espera | Queda líq. média | Ef | P | ICB |
|---:|---:|---:|---:|---:|
| 0,00 | 25,3 m | 7,9 MWmed | 14,4 MW | R$ 807/MWh |
| 0,50 | 20,3 m | 6,3 MWmed | 11,4 MW | R$ 1.017/MWh |
| 0,80 | 15,5 m | 4,8 MWmed | 8,7 MW | R$ 1.340/MWh |

Melhor ICB de FQ1 em toda a varredura: **R$ 616/MWh** (25 m, sem espera).
Melhor de FQ2: **R$ 531/MWh**. A referência de competitividade adotada no projeto
é de **R$ 250–300/MWh**.

**Leitura:** a queda disponível no Forqueta é baixa e a área alagada grande. Os
eixos **não se justificam pela energia** — nem como uso múltiplo. Priorizar
controle de cheias custa 39% da energia firme, mas a energia já não era
competitiva de início. É o inverso do que ocorre nos eixos do Antas.

---

## 9. Recomendação

1. **Não incluir FQ1 nem FQ2 na alternativa de referência.** Com os parâmetros
   medidos, o ganho é de 0,7 a 1,1 pp para 148–212 hm³, eficiência 3 a 7× pior
   que os eixos do Antas, e a energia não é competitiva.
2. **Manter FQ1 como opção condicionada**, a ser reavaliada *se e somente se* o
   dado sub-diário de Barra do Fão confirmar defasagem positiva no evento de
   projeto. Nesse cenário o ganho sobe para +10,8 pp e a decisão muda.
3. **Descartar a combinação FQ1 + FQ2** — são geometricamente incompatíveis.
   Entre os dois, **FQ2 é o mais eficiente por hm³** (0,74 contra 0,33 pp/100 hm³)
   e o único livre de interferência, invertendo a priorização do plano.
4. **Incluir no Eixo 1 do TR:** reativação da curva-chave de Barra do Fão e
   registro sub-diário no Forqueta e em Estrela.

---

## 10. Achado colateral — o rio Guaporé

Ao investigar a contribuição de jusante, apareceu o **rio Guaporé**: 2.489 km²
(posto ANA Santa Lúcia, 86580000, 2.470 km²), comparável ao Forqueta e com
aproveitamentos próprios (Monte Cuco 30 MW, Guaporé 0,67 MW).

O Guaporé deságua no Taquari **entre Muçum e Encantado**, ou seja, **dentro** do
domínio de 19.440 km² — mas **nenhum eixo da carteira E01–E12 o controla**. São
12,8% da bacia do ponto de análise inteiramente livres.

Diferentemente do Forqueta, o Guaporé está a **montante** do ponto de análise, e
portanto um eixo ali protegeria Encantado, Lajeado, Estrela e Bom Retiro do Sul.
**Sugiro avaliá-lo antes de investir mais no Forqueta.** Não estava no plano;
fica para decisão sua e do Codex.

---

## 11. Arquivos entregues

Todos em `06_resultados/CLAUDE/`, prefixo `claude_fq_`:

| Arquivo | Conteúdo |
|---|---|
| `claude_fq_roteamento_calibrado.csv` | 7 cenários × 3 regras operativas |
| `claude_fq_hidrogramas.csv` | hidrogramas em Estrela, todos os cenários |
| `claude_fq_sensibilidade_defasagem.csv` | 9 defasagens × 7 cenários |
| `claude_fq_altura_volume.csv` | varredura de altura FQ1 e FQ2 |
| `claude_fq_mapa_codigos.csv` | **de-para dos códigos entre pipelines** |
| `claude_fq_series_resumo.csv` | séries ANA obtidas no Forqueta |
| `claude_fq_defasagem_medida.csv` | 13 eventos pareados |
| `claude_fq_postos_candidatos.csv` | inventário ANA na região |
| `claude_fq_interferencia_pch.csv` | interferência por cota |
| `claude_fq_altura_livre_interferencia.csv` | altura máxima livre |
| `claude_fq_sinv.csv` | avaliação energética SINV |

Scripts em `07_python/`: `claude_fq_roteamento_calibrado.py`,
`claude_fq_sinv.py`, `claude_fq_busca_posto.py`, `claude_fq_baixa_serie.py`,
`claude_fq_interferencia_pch.py`. Séries novas em `01_dados/ana_hidroweb/`
(86745000, 86700000).

Nenhum arquivo do Codex foi editado. Nenhum `.qmd`, `HANDOFF.md` ou
`STATUS_ATUAL_PROJETO.md` foi tocado.

---

## 12. Nota sobre um resultado meu que se inverteu

Na primeira rodada usei defasagem de 31 h, estimada por escalonamento do tempo de
pico (tp ∝ A^0,3), e concluí que FQ1 era 2,5× mais eficiente que a carteira do
Antas. **Estava errado.** Aquela estimativa produzia pico natural em Estrela de
19.639 m³/s, 13,8% acima do maior valor já registrado. Com a defasagem medida
(0 h) o modelo reproduz o observado com −2,1% e o ganho de FQ1 cai de +10,7 pp
para +0,7 pp. Os números desta nota são os que valem.
