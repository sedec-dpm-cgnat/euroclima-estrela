# Seleção dos eixos de barramento — texto técnico

**Projeto EUROCLIMA+ / AECID — componente técnico SEDEC/MIDR**
**Bacia do Taquari‑Antas · município piloto de Estrela/RS**
**Trilha de modelagem hidráulica, energética e de alternativas · julho de 2026**

> Triagem preliminar. Os volumes dos eixos novos são geométricos, derivados de modelo digital de elevação de 28,6 m, classificados como **confiabilidade B**. Não substituem levantamento topográfico nem estudo de remanso.

---

## 1. Objeto e método

O estudo avalia se, e em que medida, barramentos a montante podem reduzir os danos de uma cheia equivalente à de maio de 2024 no município de Estrela. Doze eixos foram propostos e delineados sobre a grade de direções de fluxo D8 do modelo digital de elevação, com ancoragem na Base Hidrográfica Ottocodificada da ANA. A aderência entre a área de drenagem delineada e a da BHO ficou entre −0,8% e +0,1%.

A seleção combina quatro critérios, nesta ordem:

1. **Interferência com a cascata existente** — a bacia já conta com 49 aproveitamentos em operação, entre eles Monte Claro (130 MW), Castro Alves (130 MW) e 14 de Julho (100 MW);
2. **Volume de espera disponível** na altura admissível;
3. **Cobertura da bacia** — fração da área de drenagem de Estrela efetivamente controlada;
4. **Viabilidade energética**, pelo índice custo‑benefício da metodologia SINV.

### 1.1 Curvas cota‑área‑volume

As curvas dos eixos novos vêm do relevo natural do MDE, com pontos a cada 5 m entre 10 e 120 m de altura, densificados por **interpolação monotônica PCHIP em passos de 1 m**. A interpolação foi auditada: reproduz exatamente os 23 nós originais de cada eixo, com erro máximo de 0,0 em área e volume nos 276 pontos verificados.

Ajustes polinomiais de graus 2 a 4 foram testados e **descartados como modelo operacional**. O erro absoluto é pequeno frente ao volume nas alturas altas, mas a curva cota‑volume é fortemente convexa: um erro de 8 hm³ representa 0,4% do volume a 120 m e mais de 100% a 20 m. O erro relativo do cúbico chega a 279% abaixo de 40 m, e quatro dos ajustes produzem **volume negativo** dentro do intervalo. Os polinômios permanecem apenas como forma compacta de documentação.

### 1.2 Determinação da altura admissível

A altura de cada eixo é limitada pela cota de restituição do aproveitamento imediatamente a montante, conforme o item 4.6.1 do Manual de Inventário Hidroelétrico (MME, 2007).

A identificação de quem está a montante foi revista. O critério anterior comparava **área de drenagem**, o que falha quando dois barramentos têm áreas próximas: a diferença cai dentro do erro do MDE e a ordem se inverte. O caso de E09 e Monte Claro é ilustrativo — Monte Claro tem área 0,7% maior, o que o classificava como jusante, mas está 24 km acima no talvegue. O critério passou a ser a **posição longitudinal** ao longo do perfil do canal principal.

Dois filtros adicionais foram necessários. Primeiro, apenas aproveitamentos **em operação** impõem restrição: os 34 registros "em estudo" da ANEEL têm coordenadas arredondadas a duas casas decimais, o que corresponde a cerca de 1 km, e a cota amostrada cai em encosta — chegando a 465 m para pontos que deveriam estar no leito. Segundo, exige‑se **coerência de cota**: o ponto precisa estar a menos de 40 m do talvegue na sua estaca. Dos 49 aproveitamentos em operação, restaram 7 válidos como restrição.

### 1.3 Avaliação energética

Segue a metodologia SINV, itens 4.6 e 4.11 do mesmo manual. A vazão específica foi calibrada com as vazões médias de longo termo oficiais das três usinas do rio das Antas, obtidas do SNIRH: **0,0269 m³/s/km²**, contra 0,020 arbitrado na primeira rodada. A energia firme estava subestimada em 34%.

---

## 2. Resultado por eixo

| Eixo | Classe | Área controlada | % da bacia | Altura adm. | Área inund. | Vol. acum. | Vol. espera | Potência | ICB |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **E04** | prioritário | 7.498 km² | 38,6 % | 120,0 m ¹ | 42,31 km² | 2.210,7 | 1.105,3 | 191,8 MW | 239 |
| **E02** | prioritário | 3.591 km² | 18,5 % | 120,0 m ¹ | 30,78 km² | 1.377,4 | 688,7 | 95,3 MW | 399 |
| **E01** | alternativa | 2.549 km² | 13,1 % | 63,6 m | 6,48 km² | 171,6 | 85,8 | 32,7 MW | 196 |
| E12 | condicionado | 15.760 km² | 81,1 % | 55,5 m | 35,56 km² | 976,5 | 488,2 | 174,5 MW | 75 |
| E08 | condicionado | 11.951 km² | 61,5 % | 86,0 m | 15,49 km² | 620,4 | 310,2 | 206,1 MW | 78 |
| E11 | condicionado | 15.457 km² | 79,5 % | 45,0 m | 17,19 km² | 400,3 | 200,2 | 137,6 MW | 55 |
| E07 | condicionado | 8.174 km² | 42,0 % | 84,5 m | 9,41 km² | 385,4 | 192,7 | 138,1 MW | 91 |
| E06 | condicionado | 8.159 km² | 42,0 % | 84,5 m | 8,57 km² | 338,1 | 169,1 | 137,8 MW | 102 |
| E03 | condicionado | 3.772 km² | 19,4 % | 84,5 m | 4,57 km² | 151,4 | 75,7 | 64,3 MW | 162 |
| **E05** | condicionado | 7.923 km² | 40,8 % | 67,0 m | 3,08 km² | 90,3 | 45,2 | 105,3 MW | 65 |
| E09 | condicionado | 12.330 km² | 63,4 % | 24,5 m | 4,12 km² | 59,7 | 29,8 | 59,4 MW | 35 |
| **E10** | **descartado** | 12.778 km² | 65,7 % | 31,0 m | 4,31 km² | 68,7 | 34,3 | 78,3 MW | 36 |

*Volumes em hm³; ICB em R$/MWh, sem alocação de volume de espera.*
¹ Teto técnico. O remanso não é o fator limitante — a usina de montante mais próxima está 196 m (E04) e 232 m (E02) acima.

### 2.1 Os eixos prioritários

**E02 e E04 são os únicos livres de interferência da cascata existente.** Em ambos, o aproveitamento em operação imediatamente a montante está a mais de 190 m de desnível, de modo que o remanso não impõe limite dentro de qualquer altura de barragem plausível. A altura de 120 m adotada é um **teto técnico**, correspondente ao limite até onde as curvas cota‑área‑volume foram calculadas, e não um limite de engenharia. Acima dele passam a governar topografia, geotecnia, custo e impacto socioambiental.

E04 é o maior volume individual do conjunto — 2.211 hm³ — e o único dos prioritários com índice custo‑benefício energético dentro da faixa usualmente considerada competitiva. E02 adiciona 1.377 hm³, mas com ICB de R$ 399/MWh, fora dessa faixa.

**E01 é alternativa em tributário**, com restrição operacional de Cotiporã a confirmar. Volume modesto (172 hm³) e área inundada pequena (6,5 km²), mas o melhor ICB entre os não condicionados à cascata principal.

**E05 permanece condicionado a Castro Alves.** Havia sido classificado como inviável pelo critério anterior, que lhe atribuía altura negativa. Pela posição longitudinal, a restrição real é Castro Alves e a altura admissível é de 67 m. O volume é pequeno (90 hm³) porque o vale é encaixado, mas o ICB de R$ 65/MWh é competitivo.

### 2.2 E10 sai da carteira

E10 apresenta **balanço energético líquido negativo em toda a faixa viável**. A elevação do nível no canal de fuga da UHE 14 de Julho retira daquela usina mais energia do que o novo aproveitamento gera:

| Altura | Gera | Retira de 14 de Julho | Líquido |
|---:|---:|---:|---:|
| 10 m | 16,3 | 33,7 | **−17,4** |
| 20 m | 32,6 | 51,2 | **−18,6** |
| 30 m | 48,9 | 68,8 | **−19,9** |
| 40 m | 65,2 | 73,2 | **−8,0** |

*MW médios.* A altura admissível de E10 pelo critério de veto é 31 m; acima de 40 m há veto por atingir a cota mínima operacional da usina de montante. **Não existe altura em que E10 produza ganho líquido.**

### 2.3 Nota metodológica sobre "interferência"

A classificação por altura admissível trata a interferência como proibição. Isso é uma simplificação. O item 4.6.1 do manual estabelece que o nível de água normal a jusante de um aproveitamento passa a ser o do reservatório imediatamente a jusante quando este é mais elevado — o efeito é **reduzir a queda**, e portanto a energia, da usina de montante. É um custo quantificável, não um impedimento.

O impedimento só se configura quando o remanso atinge a **cota mínima operacional**. Com as curvas oficiais do SNIRH foi possível separar as duas coisas:

| Usina | Leito no eixo | NA normal | Mínima operacional |
|---|---:|---:|---:|
| 14 de Julho | 62,37 m | 104,0 m | 103,0 m |
| Monte Claro | 116,88 m | 148,0 m | 147,0 m |
| Castro Alves | 187,05 m | 240,0 m | 239,0 m |

Para E12, a perda de energia em 14 de Julho **começa aos 15 m de altura**, não aos 55,5 m que a altura admissível indica. O veto por cota mínima operacional cai em 56 m, próximo do valor calculado — mas por coincidência, não por construção.

**Recomenda‑se que a tabela de alturas passe a ter duas colunas**: a altura de veto e a altura a partir da qual começa a perda de energia na usina de montante.

---

## 3. Carteira de alternativas

| Alternativa | Área controlada | % da bacia | Área inund. | Vol. espera | % do necessário | Potência | ICB | Competitiva |
|---|---:|---:|---:|---:|---:|---:|---:|:--:|
| E02 + E04 + E12 | 15.760 km² | 81,1 % | 108,6 km² | 2.282 hm³ | 70,7 % | 461,6 MW | 292 | sim |
| E02+E04+E01+E05+E08 | 14.499 km² | 74,6 % | 98,1 km² | 2.235 hm³ | 69,2 % | 631,2 MW | 247 | sim |
| E02 + E04 + E08 | 11.951 km² | 61,5 % | 88,6 km² | 2.104 hm³ | 65,1 % | 493,2 MW | 281 | sim |
| E02 + E04 + E01 | 13.638 km² | 70,2 % | 79,6 km² | 1.880 hm³ | 58,2 % | 319,8 MW | 391 | não |
| E02 + E04 + E05 | 11.514 km² | 59,2 % | 76,2 km² | 1.839 hm³ | 56,9 % | 392,4 MW | 319 | não |
| **E02 + E04** | 11.089 km² | **57,0 %** | 73,1 km² | 1.794 hm³ | 55,5 % | 287,1 MW | 406 | não |
| E04 isolado | 7.498 km² | 38,6 % | 42,3 km² | 1.105 hm³ | 34,2 % | 191,8 MW | 337 | não |
| E02 isolado | 3.591 km² | 18,5 % | 30,8 km² | 689 hm³ | 21,3 % | 95,3 MW | 540 | não |
| E12 isolado | 15.760 km² | 81,1 % | 35,6 km² | 488 hm³ | 15,1 % | 174,5 MW | 104 | sim |

*O "volume necessário" de referência é de 3.230 hm³, estimado para não ultrapassar 4.000 m³/s em Estrela no evento de referência. Ambos os valores são preliminares e não calibrados.*

### 3.1 A tensão central

**Os eixos prioritários têm volume, mas não têm cobertura.** E02 e E04 juntos controlam apenas **57% da área de drenagem de Estrela**. Os 43% restantes — cerca de 8.350 km² — continuam produzindo escoamento sem nenhum controle. Ainda que os dois reservatórios retivessem integralmente a sua parcela, a contribuição não controlada imporia um piso da ordem de **7.700 m³/s** em Estrela, quase o dobro do limiar estimado de dano relevante.

Inversamente, **os eixos com boa cobertura são os que conflitam com a cascata**. E12 controla 81% da bacia, mas sua altura é limitada a 55,5 m pelo remanso da 14 de Julho, o que reduz o volume de espera a 488 hm³ — apenas 15% do necessário.

Nenhum arranjo avaliado resolve as duas coisas ao mesmo tempo. As alternativas que combinam cobertura e volume — E02+E04+E12 e o arranjo de cinco eixos — dependem de eixos condicionados à cascata e implicam áreas inundadas de 98 a 109 km².

### 3.2 O que isso significa para o escopo do estudo

A hipótese de que barramentos a montante resolvem isoladamente o problema de Estrela **não se sustenta** com os dados disponíveis. O melhor arranjo composto apenas por eixos prioritários entrega 55,5% do volume necessário e controla 57% da bacia.

Isso não invalida os barramentos — indica que devem ser avaliados **como componente de um arranjo híbrido**, ao lado de diques na área urbana, realocação seletiva, controle de uso e ocupação do solo, sistema de alerta precoce e alocação de volume de espera nos reservatórios existentes.

Sobre este último ponto: as curvas oficiais do SNIRH indicam que o deplecionamento preventivo conjunto das três usinas do rio das Antas disponibiliza **105 hm³ com 10 m de rebaixamento** e 139 hm³ com 15 m, sem nenhuma obra civil. É pouco frente aos 3.230 hm³ necessários, mas é a medida de menor custo e menor prazo do conjunto avaliado, e não havia sido considerada.

---

## 4. Limitações

**Parâmetros não calibrados.** O pico do evento de referência (18.000 m³/s), a lâmina escoada, o limiar de dano relevante (4.000 m³/s) e o volume necessário (3.230 hm³) são estimativas. O hidrograma é sintético. As séries fluviométricas da ANA ainda não foram incorporadas.

**Volumes geométricos.** Os volumes dos eixos novos são derivados de MDE de 28,6 m e não consideram assoreamento, volume morto nem restrições de fundação. Classe B de confiabilidade.

**Discrepância de cota em Monte Claro.** A cota do NA normal oficial é 148,0 m; a amostrada no MDE, 132,5 m — diferença de 15,5 m. Pode envolver datum vertical, ponto de ancoragem ou identificação incorreta da superfície. Não foi corrigida artificialmente e **precisa ser esclarecida**, pois a restrição de E09 depende dela.

**Ausência de roteamento.** O volume de espera de uma alternativa não se converte diretamente em redução de pico: depende do hidrograma, da regra operativa e da defasagem entre a parcela controlada e a livre. A verificação exige roteamento hidrológico, ainda pendente.

**Interferência tratada de forma binária** na tabela de alturas admissíveis, conforme §2.3.

**Custo não densificado.** As curvas de custo existem apenas nos múltiplos de 5 m de altura e são interpoladas linearmente entre eles.

---

### Referências

MME — Ministério de Minas e Energia. *Manual de Inventário Hidroelétrico de Bacias Hidrográficas*, edição 2007. Capítulo 4, itens 4.6 e 4.11.

ANA — Agência Nacional de Águas e Saneamento Básico. Curvas cota‑área‑volume das UHEs 14 de Julho, Castro Alves e Monte Claro. SNIRH, registro `b8f0487a-df73-4f8d-8b22-bb49cf9f3683`.

ANEEL. Sistema de Informações de Geração — SIGA; Empreendimentos hidrelétricos em estudo. Dados abertos.

MORAES, S. R.; COLLISCHONN, W.; BUFFON, F. T.; ECKHARDT, R. R. *Revisão e consolidação da série histórica dos níveis das cheias do rio Taquari em Lajeado de 1939 a 2023.* Porto Alegre, 2024.
