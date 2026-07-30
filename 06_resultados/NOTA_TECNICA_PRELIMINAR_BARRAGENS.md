# Nota Técnica Preliminar — Potencial de barragens de montante na redução dos danos de cheias em Estrela/RS

**Projeto EUROCLIMA+ / AECID — Componente técnico (SEDEC/MIDR)**
**Elaboração:** Cássio Rampinelli — COMUC/SEDEC · Julho de 2026
**Status:** análise exploratória de ordem de grandeza, destinada a subsidiar a redação do Termo de Referência. **Não substitui** os estudos a serem contratados.

---

## 1. Objetivo

Responder, em nível de triagem, à pergunta que estrutura o Eixo 3 do estudo:

> *Quantas barragens, de que porte e com que volume de amortecimento seriam necessárias a montante para evitar — ou reduzir significativamente — os danos de uma cheia equivalente à de maio de 2024 em Estrela/RS?*

A resposta condiciona diretamente o escopo, o esforço de modelagem e o preço do contrato.

## 2. Base de dados utilizada

| Insumo | Origem | Resolução / porte |
|---|---|---|
| Modelo digital de elevação (`mdr.tif`) | base do projeto | 28,6 m, EPSG:32722 |
| Direções de fluxo D8 (`Fdr.tif`) | base do projeto | 28,6 m, EPSG:31982 |
| Base hidrográfica ottocodificada | BHO/ANA (`Drenagem_Bacia_Taquari.shp`) | 30.459 trechos |
| Eixos de barragem candidatos | `Barragem_A`, `Barragem_A2`, `Barragem_B` | 3 pontos |
| Série consistida de cotas do Taquari | Moraes, Collischonn, Buffon & Eckhardt (2024) | 1939–2023 |

Área de drenagem: **19.440 km²** no início do trecho modelado (Estrela) e **23.618 km²** na bacia Taquari-Antas completa.

## 3. Delineação das bacias contribuintes

Delineação por *upstream BFS* sobre o grafo D8, com *snap* dos eixos à célula de drenagem cuja área acumulada mais se aproxima da área ottocodificada da BHO. A aderência entre as duas fontes foi excelente (erro < 1%), o que valida a grade de direções de fluxo.

| Eixo | Latitude | Longitude | Cota do eixo | Área controlada | % da bacia em Estrela | Aderência à BHO |
|---|---|---|---|---|---|---|
| **BAR-A** | −29,16163 | −51,83560 | 47 m | **15.760 km²** | **81,1 %** | 15.852 km² (−0,6%) |
| **BAR-A2** | −29,08147 | −51,65664 | 72 m | 12.777 km² | 65,7 % | 12.877 km² (−0,8%) |
| **BAR-B** | −29,05970 | −51,71858 | 72 m | 2.549 km² | 13,1 % | 2.547 km² (+0,1%) |

> **Atenção — os eixos são aninhados.** BAR-A situa-se a jusante da confluência dos ramos controlados por BAR-A2 e BAR-B. Os volumes **não são aditivos**: BAR-A já engloba as outras duas. A área incremental entre elas é de apenas 433 km².
>
> Portanto, as alternativas mutuamente exclusivas reais são:
> - **(i)** uma barragem única em BAR-A (81,1% da bacia); **ou**
> - **(ii)** o par BAR-A2 + BAR-B (78,8% da bacia), evitando uma estrutura única de grande porte.

## 4. Curvas cota-área-volume

Obtidas por *flood-fill* hidraulicamente conectado a montante de cada eixo, sobre o MDE de 28,6 m.

**Volume armazenado (hm³) por altura de barragem:**

| Altura | BAR-A | BAR-A2 | BAR-B | A2+B |
|---:|---:|---:|---:|---:|
| 20 m | 92 | 33 | 11 | 44 |
| 30 m | 255 | 63 | 28 | 91 |
| 40 m | 493 | 156 | 56 | 212 |
| 50 m | 788 | 311 | 96 | 407 |
| 60 m | 1.150 | 502 | 149 | 651 |
| 70 m | 1.648 | 732 | 216 | 948 |
| 80 m | **2.231** | 1.004 | 301 | 1.304 |

Área alagada correspondente em BAR-A: 26,7 km² a 40 m; 45,2 km² a 60 m; 62,5 km² a 80 m.

## 5. Volume de amortecimento necessário

Evento de referência adotado (a recalibrar com a série consistida): pico de **18.000 m³/s** em Estrela (0,93 m³/s/km²), lâmina escoada de 260 mm, **volume escoado total de ≈ 5.050 hm³**, permanência acima de 4.000 m³/s por 116 h.

O volume que precisaria ser retirado do hidrograma, `V = ∫ max(0, Q − Q_alvo) dt`:

| Vazão-alvo em Estrela | Redução do pico | Volume necessário |
|---:|---:|---:|
| 4.000 m³/s *(sem dano relevante)* | 78 % | **3.230 hm³** |
| 6.000 m³/s | 67 % | 2.462 hm³ |
| 8.000 m³/s | 56 % | 1.811 hm³ |
| 9.000 m³/s *(metade do pico)* | 50 % | 1.524 hm³ |
| 12.000 m³/s | 33 % | 798 hm³ |

### 5.1 Existe um piso físico de redução

BAR-A controla 81,1% da bacia. Os **3.680 km² restantes (18,9%)** continuam produzindo escoamento mesmo com a barragem totalmente fechada — da ordem de **3.400 m³/s** de pico residual em Estrela. Nenhum arranjo de barragens nesses eixos reduz o pico abaixo desse valor.

## 6. Amortecimento efetivo — roteamento de Puls

Simulação de piscina nivelada com vertedouro de soleira livre (`Q = 2,1·L·H^1,5`) e descarga de fundo (`Q = 0,62·A·√(2gh)`). Testados dois arranjos: **convencional** (soleira a ¾ da altura, reservatório com volume morto) e **seca / *dry dam*** (reservatório normalmente vazio, descarga de fundo dimensionada para liberar ≈ 4.000 m³/s, vertedouro apenas junto à crista).

| Cenário | Vol. utilizado | Pico em Estrela | Redução | Saturou? |
|---|---:|---:|---:|:---:|
| A1 — BAR-A 40 m convencional | 493 hm³ | 18.000 m³/s | 0 % | **sim** |
| A2 — BAR-A 60 m convencional | 1.118 hm³ | 17.016 m³/s | 5,5 % | não |
| A3 — BAR-A 80 m convencional | 1.712 hm³ | 15.106 m³/s | 16,1 % | não |
| B1 — BAR-A2 60 m convencional | 489 hm³ | 17.804 m³/s | 1,1 % | não |
| B2 — BAR-B 60 m convencional | 105 hm³ | 17.976 m³/s | 0,1 % | não |
| **S1 — BAR-A 60 m seca** | 1.150 hm³ | 17.518 m³/s | 2,7 % | **sim** |
| **S2 — BAR-A 80 m seca** | **2.067 hm³** | **8.303 m³/s** | **53,9 %** | não |
| S3 — BAR-A2 80 m seca | 1.004 hm³ | 15.627 m³/s | 13,2 % | **sim** |
| S4 — A2 80 m + B 60 m secas | 1.152 hm³ | 17.113 m³/s | 4,9 % | **sim** |

*"Saturou" = o reservatório encheu durante o evento e passou a transferir a cheia integralmente para jusante, perdendo a função de amortecimento.*

## 7. Conclusões preliminares

**(1) Barragens convencionais são praticamente inócuas para um evento desta magnitude.** Com vertedouro de soleira livre, a redução de pico fica entre 0% e 16%, mesmo com 80 m de altura. O volume da cheia (≈ 5.050 hm³) é 2 a 10 vezes maior que o volume disponível nos reservatórios.

**(2) Só o arranjo de barragem seca de grande porte produz efeito relevante.** BAR-A com 80 m de altura, operada como *dry dam* (≈ 2.070 hm³ de volume dedicado, 62 km² de área inundável), reduz o pico em ≈ 54% — de 18.000 para 8.300 m³/s.

**(3) Ainda assim, isso não evita os danos da cheia de 2024.** Os 8.300 m³/s residuais continuam muito acima da vazão sem dano relevante (ordem de 4.000 m³/s). Para chegar lá seriam necessários ≈ 3.230 hm³ de amortecimento — **acima da capacidade física do melhor eixo, mesmo com 80 m de altura**.

**(4) O par BAR-A2 + BAR-B é claramente inferior a BAR-A isolada.** Controla área semelhante (78,8% vs. 81,1%), mas dispõe de apenas 1.304 hm³ contra 2.231 hm³ a 80 m, por causa da geometria dos vales. Ambos saturam no evento de referência.

**(5) Consequência para o Termo de Referência.** A hipótese "construir barragens a montante resolve o problema de Estrela" **não se sustenta isoladamente**. O TR deve, portanto:

- enquadrar o Eixo 3 como **análise comparativa de alternativas híbridas** (barragens + diques + realocação + controle de uso do solo + alerta precoce), e **não** como projeto de barragens;
- exigir explicitamente o cálculo do **volume de amortecimento necessário** e a **verificação de saturação do reservatório** para o evento de referência, com curvas cota-área-volume derivadas de MDE;
- exigir a **decomposição controlado / não-controlado** da bacia, de modo a explicitar o piso físico de redução;
- tratar a **operação do reservatório** (barragem seca, comportas, pré-deplecionamento) como variável de projeto, não como detalhe;
- incorporar a **análise custo-benefício** com curvas cota-dano, único critério capaz de arbitrar entre uma estrutura de 80 m de altura e um conjunto de medidas distribuídas.

## 8. Limitações desta análise

Esta é uma triagem de ordem de grandeza. Especificamente:

- o hidrograma de referência é **sintético** (gama de 2 parâmetros), ancorado em pico e lâmina escoada plausíveis; **deve ser substituído** pela série consistida ANA/CPRM do evento;
- a decomposição controlado/não-controlado é **proporcional à área**, ignorando o defasamento temporal entre sub-bacias — o que o HEC-HMS capturará;
- as curvas cota-área-volume vêm de MDE de **28,6 m**, adequado para triagem mas não para projeto;
- não há verificação **geotécnica, ambiental, fundiária ou de segurança de barragens** dos eixos; a área alagada de 62 km² em BAR-A implica desapropriações e possível remoção de população;
- o limiar de "vazão sem dano relevante" (4.000 m³/s) é **estimado** e deve ser determinado pela modelagem hidráulica 2D com o cadastro de edificações.

## 9. Reprodutibilidade

| Arquivo | Função |
|---|---|
| `07_python/02_bacias_barragens.py` | delineação D8, acumulação de fluxo, curvas CAV |
| `02_R/00_config.R` | parâmetros da bacia, eixos, limiares |
| `02_R/01_baixa_dados_ana.R` | download das séries ANA/HidroWeb |
| `02_R/02_volume_amortecimento.R` | volume necessário, piso físico, altura requerida |
| `02_R/03_roteamento_puls.R` | roteamento de reservatório, cenários |
| `01_dados/gis_derivado/bacias_barragens.gpkg` | bacias delineadas |
| `01_dados/gis_derivado/reservatorios_barragens.gpkg` | manchas dos reservatórios (20/30/40 m) |
| `01_dados/cav/cav_barragens.csv` | curvas cota-área-volume |

### Referência

MORAES, S. R.; COLLISCHONN, W.; BUFFON, F. T.; ECKHARDT, R. R. *Revisão e consolidação da série histórica dos níveis das cheias do rio Taquari em Lajeado de 1939 a 2023.* Porto Alegre, 2024. Nota técnica.
