# Análise de Alternativas — Reservatórios de Amortecimento a Montante de Estrela/RS

**Projeto EUROCLIMA+ / AECID — Componente técnico (SEDEC/MIDR)**
**Elaboração:** Cássio Rampinelli — COMUC/SEDEC · Julho de 2026
**Status:** análise exploratória de ordem de grandeza para subsidiar o Termo de Referência. Os parâmetros econômicos são preliminares e estão explicitados no §6.

---

## 1. Escopo da análise

Foram avaliadas **160 alternativas**, combinando:

- **3 eixos** fornecidos em KMZ (`Ponto-Barragem1/2/3`), aqui designados **B1**, **B2** e **B3**;
- **10 alturas** de barragem, de 30 m a 120 m, em passos de 10 m;
- **2 arranjos operacionais** — barragem convencional e barragem seca (*dry dam*);
- **combinações** entre eixos não aninhados (B3 + B2), com alturas independentes.

Para cada alternativa foram calculados, a partir do MDE de 28,6 m: geometria da barragem (comprimento de crista, volume de aterro), curva cota-área-volume do reservatório, roteamento hidrológico de Puls sobre nove cenários de frequência, dano esperado anual e indicadores econômicos.

## 2. Os eixos

| Eixo | Arquivo | Latitude | Longitude | Cota do eixo | Área controlada | % da bacia em Estrela |
|---|---|---:|---:|---:|---:|---:|
| **B1** | `Ponto-Barragem1.kmz` | −29,15308 | −51,75308 | 57,0 m | **15.457 km²** | **79,5 %** |
| **B3** | `Ponto_Barragem3.kmz` | −29,08853 | −51,63962 | 72,5 m | 12.774 km² | 65,7 % |
| **B2** | `Ponto_Barragem2.kmz` | −29,07525 | −51,71192 | 69,0 m | 2.562 km² | 13,2 % |

A aderência à Base Hidrográfica Ottocodificada da ANA foi de −0,6% (B1), −0,8% (B3) e +0,1% (B2), confirmando o posicionamento na drenagem. O deslocamento de *snap* ficou entre 148 e 188 m.

> **Estrutura aninhada.** B1 está a jusante da confluência de B3 e B2. A área incremental entre eles é de apenas **121 km² (0,8% de B1)**. Portanto os volumes **não são aditivos** e as alternativas mutuamente exclusivas são:
> - **B1 isolada** (79,5% da bacia), ou
> - **B3 + B2** (78,9% da bacia), evitando uma estrutura única de grande porte.
>
> Não faz sentido combinar B1 com B2 ou B3.

### 2.1 Comparação com os eixos em shapefile

Os KMZ ficam próximos, mas **não coincidem** com os pontos anteriores (`Barragem_A/A2/B`), e a diferença importa:

| Papel | Shapefile | Volume a 80 m | KMZ | Volume a 80 m | Diferença |
|---|---|---:|---|---:|---:|
| Eixo principal | BAR‑A | 2.231 hm³ | **B1** | 1.600 hm³ | **−28,3 %** |
| Ramo Antas | BAR‑A2 | 1.004 hm³ | B3 | 970 hm³ | −3,4 % |
| Tributário | BAR‑B | 301 hm³ | B2 | 326 hm³ | +8,4 % |

**O eixo B1 do KMZ é hidraulicamente pior que o BAR‑A do shapefile**: armazena 28% menos com a mesma altura, porque está num trecho de vale mais encaixado, 10 m acima em cota. Vale reavaliar a posição — deslocar B1 para jusante recupera volume significativo.

## 3. Geometria e custo das barragens

Extraídos do perfil transversal do vale, perpendicular à direção do escoamento, com seção trapezoidal (crista 10 m, taludes 1V:2,5H montante e 1V:2,0H jusante, borda livre 3 m).

| Altura | B1 — crista / aterro / custo | B3 — crista / aterro / custo | B2 — crista / aterro / custo |
|---:|---|---|---|
| 40 m | 558 m · 1,48 hm³ · R$ 280 M | 473 m · 1,54 hm³ · R$ 271 M | 458 m · 0,81 hm³ · R$ 126 M |
| 60 m | 673 m · 3,57 hm³ · R$ 644 M | 587 m · 3,52 hm³ · R$ 559 M | 1.360 m · 6,18 hm³ · R$ 805 M |
| 80 m | 788 m · 6,85 hm³ · R$ 1.125 M | 702 m · 6,54 hm³ · R$ 980 M | 1.432 m · 12,2 hm³ · R$ 1.563 M |
| 100 m | 845 m · 11,5 hm³ · R$ 1.790 M | 902 m · 10,8 hm³ · R$ 1.568 M | 1.503 m · 20,8 hm³ · R$ 2.636 M |
| 120 m | 931 m · 17,7 hm³ · R$ 2.649 M | 1.074 m · 16,8 hm³ · R$ 2.363 M | 1.589 m · 32,1 hm³ · R$ 4.042 M |

> **Descontinuidade em B2 entre 45 m e 50 m.** O comprimento de crista salta de **501 m para 1.274 m** e o custo de R$ 162 M para R$ 539 M. Isso indica que, acima de ~45 m, o reservatório transborda por uma **sela topográfica** para um vale adjacente, exigindo **dique de sela**. É um ponto de inflexão de projeto: B2 acima de 45 m fica desproporcionalmente cara.

Descontinuidade análoga, mas menos severa, ocorre em B3 entre 30 m e 35 m (área alagada salta de 2,9 para 11,0 km²) e em B1 entre 45 m e 50 m (17,1 → 26,6 km²).

## 4. Desempenho hidrológico

### 4.1 O arranjo operacional domina o resultado

| Arranjo | Melhor redução de pico obtida | Observação |
|---|---:|---|
| **Convencional** (vertedouro de soleira livre a ¾ da altura) | **37,8 %** — B1 a 120 m, R$ 2.649 M | a maioria satura e transfere a cheia integralmente |
| **Seca** (*dry dam*, descarga de fundo dimensionada, vertedouro junto à crista) | **55,1 %** — B1 a 110 m, R$ 2.194 M | única configuração com desempenho relevante |

**Nenhuma alternativa convencional é economicamente viável.** Todas as alternativas com razão benefício-custo acima de 1 são de barragem seca.

### 4.2 Melhor alternativa por faixa de redução

| Faixa de redução | Melhor alternativa | Volume utilizado | Área alagada | Custo | B/C |
|---|---|---:|---:|---:|---:|
| < 10 % | B1 — 70 m seca | 1.166 hm³ | 40,0 km² | R$ 865 M | 2,35 |
| 20–30 % | **B1 — 80 m seca** | 1.600 hm³ | 46,8 km² | R$ 1.125 M | **2,70** |
| 40–50 % | B3 — 100 m seca | 1.583 hm³ | 39,7 km² | R$ 1.568 M | 1,99 |
| 50–60 % | **B1 — 90 m seca** | 1.977 hm³ | 54,0 km² | R$ 1.431 M | **2,45** |

### 4.3 Alternativas de maior valor presente líquido

Para alternativas **mutuamente exclusivas**, o critério correto de seleção é o **VPL líquido**, não a razão B/C.

| # | Alternativa | Redução do pico | Vol. utilizado | Área alagada | Custo | VPL líquido | B/C |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | **B1 — 90 m seca** | **52,7 %** | 1.977 hm³ | 54,0 km² | R$ 1.431 M | **R$ 2.339 M** | 2,45 |
| 2 | B1 — 80 m seca | 23,4 % | 1.600 hm³ | 46,8 km² | R$ 1.125 M | R$ 2.153 M | 2,70 |
| 3 | B1 — 100 m seca | 54,0 % | 2.145 hm³ | 63,0 km² | R$ 1.790 M | R$ 2.086 M | 2,03 |
| 4 | **B3 — 100 m seca** | **43,6 %** | 1.583 hm³ | 39,7 km² | R$ 1.568 M | R$ 1.740 M | 1,99 |
| 5 | B1 — 110 m seca | 55,1 % | 2.145 hm³ | 71,7 km² | R$ 2.194 M | R$ 1.728 M | 1,70 |
| 6 | B3 — 90 m seca | 22,1 % | 1.253 hm³ | 34,2 km² | R$ 1.250 M | R$ 1.700 M | 2,21 |

## 5. Alternativas recomendadas para detalhamento

Três alternativas merecem ser levadas ao estudo contratado, por representarem escolhas estruturalmente distintas:

### Alternativa I — B1, 90 m, barragem seca
- **Redução do pico: 52,7 %** (de 18.000 para ~8.500 m³/s)
- Volume utilizado 1.977 hm³ · área alagada 54,0 km² · crista 816 m · aterro 9,0 hm³
- Custo R$ 1.431 M · **VPL líquido R$ 2.339 M · B/C 2,45**
- **Prós:** melhor VPL líquido do universo; estrutura única, um só sítio de obra e de licenciamento.
- **Contras:** barragem de 90 m é obra de grande porte, classe de alto dano potencial pela Lei nº 12.334/2010; 54 km² de área inundável implicam desapropriação e possível remoção de população; risco concentrado em uma única estrutura.

### Alternativa II — B3, 100 m, barragem seca
- **Redução do pico: 43,6 %**
- Volume utilizado 1.583 hm³ · **área alagada 39,7 km²** (26% menor que a Alternativa I) · crista 902 m
- Custo R$ 1.568 M · VPL líquido R$ 1.740 M · B/C 1,99
- **Prós:** menor impacto territorial por unidade de benefício; deixa o tributário B2 livre.
- **Contras:** desempenho 9 pontos percentuais inferior; controla 65,7% da bacia, contra 79,5% de B1.

### Alternativa III — B3 100 m + B2 30 m, ambas secas
- **Redução do pico: 43,6 %**
- Volume utilizado 1.645 hm³ · área alagada 43,4 km² · custo R$ 1.639 M · B/C 1,90
- **Prós:** distribui o risco em duas estruturas menores; B2 a 30 m fica **abaixo da sela** (crista de 301 m, custo R$ 71 M) e é barata.
- **Contras:** dois sítios de obra e de licenciamento; ganho marginal sobre a Alternativa II é pequeno.

> **Alternativa descartada — B2 acima de 45 m.** O dique de sela necessário multiplica o custo por 3,3 sem ganho hidrológico proporcional. Se B2 entrar em qualquer arranjo, deve ficar **em 30–45 m**.

## 6. Hipóteses econômicas e sensibilidade

**Toda a análise econômica depende de dois parâmetros ainda não medidos.**

| Parâmetro | Valor adotado | Situação |
|---|---:|---|
| Dano direto do evento de referência em Estrela | R$ 2.500 M | **estimativa — a medir no Eixo 3** |
| Tempo de retorno atribuído ao evento | 100 anos | **a determinar na análise de frequência** |
| Vazão sem dano relevante em Estrela | 4.000 m³/s | **a determinar com o HEC-RAS 2D** |
| Horizonte de análise | 50 anos | padrão |
| Taxa de desconto social | 6 % a.a. | padrão de infraestrutura |
| Custo de aterro compactado | R$ 90/m³ | ordem de grandeza — revisar com SINAPI |
| Desapropriação | R$ 45.000/ha | ordem de grandeza — revisar |
| BDI e obras complementares | +35 % | ordem de grandeza |

### 6.1 Dano mínimo para que cada alternativa se pague

| Alternativa | Redução | Custo | **Dano mínimo do evento para B/C = 1** |
|---|---:|---:|---:|
| B1 — 80 m seca | 23,4 % | R$ 1.125 M | **R$ 926 M** |
| B1 — 90 m seca | 52,7 % | R$ 1.431 M | **R$ 1.020 M** |
| B3 — 90 m seca | 22,1 % | R$ 1.250 M | R$ 1.132 M |
| B1 — 100 m seca | 54,0 % | R$ 1.790 M | R$ 1.229 M |
| B3 — 100 m seca | 43,6 % | R$ 1.568 M | R$ 1.259 M |
| B1 — 110 m seca | 55,1 % | R$ 2.194 M | R$ 1.471 M |

**Leitura:** se o dano direto de um evento como o de 2024 em Estrela for inferior a ≈ R$ 1 bilhão, **nenhuma barragem se justifica economicamente**. Acima de R$ 1,5 bilhão, várias se justificam com folga.

Essa é a pergunta empírica que decide o projeto — e é exatamente o que o **Eixo 3 do TR** precisa medir, por meio das curvas cota-dano construídas sobre o cadastro do Eixo 1.

## 7. Conclusões

**(1) O arranjo operacional importa mais do que o tamanho.** Uma barragem convencional de 120 m rende menos que uma barragem seca de 90 m, e custa quase o dobro. A distinção **barragem seca × barragem convencional** deve ser tratada no TR como variável de projeto de primeira ordem.

**(2) O teto de desempenho é ~55 % de redução do pico.** Nenhuma alternativa, em nenhuma altura até 120 m, ultrapassa isso — porque 20,5% da bacia não é controlada por nenhum dos eixos e produz, sozinha, pico residual da ordem de 3.500 m³/s.

**(3) Nenhuma alternativa isolada evita os danos da cheia de 2024.** A melhor reduz o pico de 18.000 para ~8.500 m³/s, ainda muito acima do limiar de dano relevante. **Barragens só fazem sentido como parte de um arranjo híbrido** com diques, realocação, controle de uso do solo e alerta precoce.

**(4) A escolha é entre concentrar ou distribuir.** B1 a 90 m maximiza o VPL líquido, mas concentra risco e impacto territorial em uma estrutura de grande porte. B3 a 100 m entrega 83% do benefício com 74% da área inundada e sem barrar o eixo principal.

**(5) A viabilidade é frágil a um parâmetro.** Todo o resultado econômico se inverte se o dano de referência estiver abaixo de R$ 1 bilhão. Enquanto esse número não for medido, **nenhuma decisão de investimento deve ser tomada** — e o TR deve deixar isso explícito.

**(6) Reavaliar a posição de B1.** O eixo do KMZ armazena 28% menos que o ponto marcado anteriormente no shapefile (`Barragem_A`), a mesma altura. Um deslocamento do eixo para jusante melhora substancialmente a relação volume/altura. **A locação ótima do eixo deve ser objeto de estudo específico**, e não fixada a priori no TR.

## 8. Limitações

- Hidrograma de referência **sintético**; a substituir pela série consistida ANA/CPRM.
- Curva de frequência **Gumbel ancorada** no evento de referência, com CV arbitrado em 0,45.
- Curvas cota-área-volume derivadas de MDE de **28,6 m** — adequado para triagem, não para projeto.
- Geometria da barragem por **perfil transversal único** perpendicular ao escoamento; não substitui levantamento topográfico do sítio.
- **Sem investigação geotécnica** — a viabilidade da fundação em qualquer dos eixos é desconhecida e pode inviabilizar alturas elevadas.
- **Sem avaliação ambiental ou fundiária** — 40 a 72 km² de área inundável implicam impactos não quantificados aqui.
- Custos unitários de **ordem de grandeza**; não substituem orçamento paramétrico.
- O roteamento não considera **defasagem temporal** entre sub-bacias, que o HEC-HMS capturará.

## 9. Reprodutibilidade

| Arquivo | Função |
|---|---|
| `07_python/05_bacias_kmz.py` | leitura dos KMZ, delineação D8, curvas CAV |
| `07_python/06_geometria_barragens.py` | perfil transversal, crista, aterro, custo |
| `02_R/04_cenarios_kmz.R` | comparação KMZ × shapefile, roteamento |
| `02_R/05_analise_alternativas.R` | universo de 160 alternativas, EAD, CBA |
| `02_R/06_sensibilidade.R` | sensibilidade ao dano e limiar de viabilidade |
| `06_resultados/tabelas/analise_alternativas_completa.csv` | resultado completo |
| `06_resultados/tabelas/dano_limiar_viabilidade.csv` | limiares de viabilidade |
| `01_dados/gis_derivado/bacias_kmz.gpkg` | bacias delineadas |
| `01_dados/gis_derivado/reservatorios_kmz.gpkg` | manchas dos reservatórios (30/50/70 m) |
