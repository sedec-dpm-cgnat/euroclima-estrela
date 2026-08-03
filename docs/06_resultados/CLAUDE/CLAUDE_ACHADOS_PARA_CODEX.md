# Achados da trilha de modelagem — para integração pelo Codex

**Origem:** trilha de modelagem hidráulica, energética e de alternativas
**Data:** 30/07/2026
**Escopo respeitado:** apenas `07_python/claude_*.py`, `07_python/27_ajusta_cav_eixos_novos.py` (executado e auditado), `06_resultados/CLAUDE/`. Nenhum arquivo do Codex foi editado. `cav_todos.csv`, `geometria_todos.csv`, `prioridade_eixos_revisada.csv` e os resultados históricos do MDE **não foram sobrescritos**.

---

## 1. Achados que exigem decisão ou revisão de arquivos existentes

### 1.1 Interferência é custo energético, não veto binário — CONCEITUAL

A tabela de altura admissível trata a interferência como proibição. O item 4.6.1 do Manual de Inventário estabelece que o NAjn de um aproveitamento passa a ser o do reservatório imediatamente a jusante quando este é mais elevado: o efeito é **reduzir a queda** da usina de montante, não impedir a obra. Veto só quando o remanso atinge a **cota mínima operacional**.

**O nível de comparação estava errado.** Comparava-se contra o **NA do reservatório** de montante; o correto é o **leito no eixo daquela usina**, onde fica o canal de fuga:

| Usina | Leito (base da CAV) | NA normal | Mínima operacional |
|---|---:|---:|---:|
| 14 de Julho | **62,37 m** | 104,0 m | 103,0 m |
| Monte Claro | **116,88 m** | 148,0 m | 147,0 m |
| Castro Alves | **187,05 m** | 240,0 m | 239,0 m |

Para E12 (eixo em 47 m), a perda em 14 de Julho **começa aos 15 m de altura**, não aos 55,5 m. O veto por cota mínima operacional cai em 56 m — próximo do valor tabelado, mas por coincidência.

**Recomendação:** a tabela de alturas deve ter **duas colunas** — altura de veto e altura de início de perda energética.

**Arquivos:** `claude_interferencia_energetica.csv`, `claude_balanco_energetico_liquido.csv`.

### 1.2 E10 tem balanço energético negativo — DESCARTE CONFIRMADO, motivo diferente

| Altura | Gera | Retira de 14 de Julho | Líquido |
|---:|---:|---:|---:|
| 10 m | 16,3 | 33,7 | **−17,4** |
| 20 m | 32,6 | 51,2 | **−18,6** |
| 30 m | 48,9 | 68,8 | **−19,9** |
| 40 m | 65,2 | 73,2 | **−8,0** |

*MW médios.* Altura admissível por veto: 31 m. **Não existe altura viável com ganho líquido.** O motivo do descarte é energético, não de remanso.

### 1.3 Vazão específica calibrada — os ICB da v1 estão errados

| Usina | Área | Qmlt oficial | q específica |
|---|---:|---:|---:|
| 14 de Julho | 12.758 km² | 370,86 m³/s | 0,0291 |
| Monte Claro | 12.113 km² | 320,55 m³/s | 0,0265 |
| Castro Alves | 7.742,6 km² | 185,57 m³/s | 0,0240 |

**Média ponderada por área: 0,0269 m³/s/km²**, contra 0,020 arbitrado. **A energia firme da v1 estava subestimada em 34% e os ICB superestimados na mesma proporção.**

Ajustei uma relação regional potencial (`Qmlt = 0,0013·A^1,322`) e **descartei**: expoente 1,32 é fisicamente implausível (esperado 0,8 a 1,0) e três pontos entre 7.700 e 12.800 km² não sustentam extrapolação para E01/E02/E03 (2.500 a 3.800 km²). Uso a vazão específica média.

**Ação:** usar `claude_sinv_*_v2.csv`. Os `_v1` ficam como histórico.

### 1.4 Discrepância de cota em Monte Claro — NÃO RESOLVIDA

CAV oficial: 148,0 m. MDE: 132,5 m. **Diferença de 15,5 m.** A restrição de E09 depende disso. Não corrigi artificialmente. Precisa ser esclarecida — datum vertical, ponto de ancoragem ou identificação da superfície.

---

## 2. Auditoria do `27_ajusta_cav_eixos_novos.py`

**Executado. Código correto** — PCHIP de Fritsch‑Carlson bem implementada, incluindo fórmulas de extremidade e limitador `3·delta`; ajuste polinomial com escalonamento para [−1,1]; não extrapola. Sem reparos.

276 pontos originais → **1.332 interpolados** (12 eixos × 111 alturas).

### 2.1 Fidelidade

**A PCHIP reproduz exatamente os 23 nós de cada eixo** — erro máximo 0,0 em área e volume nos 276 pontos, tolerância 1e‑6. Verificado.

### 2.2 Polinômios — confirmo o descarte como modelo operacional

| Grau | Não monotônicos | Geram valor negativo | Pior erro relativo até 40 m |
|---:|---:|---:|---:|
| 2 | 14 de 24 | 2 | **3.350 %** |
| 3 | 2 de 24 | 4 | **279 %** |
| 4 | 1 de 24 | 1 | **491 %** |

O erro absoluto é pequeno; o relativo não. A curva cota‑volume é fortemente convexa: 8 hm³ de erro são 0,4% do volume a 120 m e mais de 100% a 20 m. Quatro cúbicos produzem **volume negativo** (E05, E06, E07, E10).

**Se os polinômios forem embutidos em alguma ferramenta, restringir o domínio a alturas ≥ 40 m.**

**Arquivo:** `claude_auditoria_polinomios_cav.csv`.

### 2.3 Coerência com as alturas admissíveis

Todas as 12 alturas caem dentro do intervalo interpolado — **sem extrapolação**. A interpolação linear de 5 m **superestimava** o volume, como esperado numa curva convexa:

| Eixo | Linear 5 m | PCHIP | Diferença |
|---|---:|---:|---:|
| E10 | 70,0 | 68,7 | **−1,87 %** |
| E05 | 91,0 | 90,3 | −0,72 % |
| demais | — | — | < 0,3 % |

---

## 3. Tabela final consolidada

**`claude_cav_eixos_consolidada.csv`** e **`claude_eixos_ficha_final.csv`** — prontas para entrar na classificação de confiabilidade. Todos os 12 eixos são **classe B** (CAV do MDE natural, eixo sem reservatório).

Critérios: volume de espera = 50% do máximo (parâmetro); NA máximo normal = nível do volume máximo descontada a espera (item 4.6.1); depleção máxima = ⅓ da queda bruta.

| Eixo | Classe | Altura | NA normal | Área inund. | Vol. acum. | Vol. útil | Vol. espera | ICB v2 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| E04 | prioritário | 120,0 m | 326,9 m | 42,31 km² | 2.210,7 | 625,6 | 1.105,3 | 239 |
| E02 | prioritário | 120,0 m | 385,8 m | 30,78 km² | 1.377,4 | 450,1 | 688,7 | 399 |
| E01 | alternativa | 63,6 m | 120,1 m | 6,48 km² | 171,6 | 53,6 | 85,8 | 196 |
| E12 | condicionado | 55,5 m | 86,8 m | 35,56 km² | 976,5 | 299,1 | 488,2 | 75 |
| E08 | condicionado | 86,0 m | 209,8 m | 15,49 km² | 620,4 | 171,1 | 310,2 | 78 |
| E11 | condicionado | 45,0 m | 89,1 m | 17,19 km² | 400,3 | 113,9 | 200,2 | 55 |
| E07 | condicionado | 84,5 m | 209,6 m | 9,41 km² | 385,4 | 104,8 | 192,7 | 91 |
| E06 | condicionado | 84,5 m | 210,4 m | 8,57 km² | 338,1 | 95,2 | 169,1 | 102 |
| E03 | condicionado | 84,5 m | 213,8 m | 4,57 km² | 151,4 | 47,5 | 75,7 | 162 |
| E05 | condicionado | 67,0 m | 216,0 m | 3,08 km² | 90,3 | 27,2 | 45,2 | 65 |
| E09 | condicionado | 24,5 m | 122,0 m | 4,12 km² | 59,7 | 13,8 | 29,8 | 35 |
| E10 | **descartado** | 31,0 m | 92,0 m | 4,31 km² | 68,7 | 16,4 | 34,3 | 36 |

*Volumes em hm³; ICB em R$/MWh sem alocação de espera.*

**Total: 6.850 hm³ acumulados, 3.425 hm³ de espera.**

---

## 4. A tensão central da carteira — para o relatório

| Alternativa | Área controlada | % da bacia | Área inund. | Vol. espera | % do necessário | ICB |
|---|---:|---:|---:|---:|---:|---:|
| E02 + E04 + E12 | 15.760 km² | 81,1 % | 108,6 km² | 2.282 hm³ | 70,7 % | 292 |
| E02+E04+E01+E05+E08 | 14.499 km² | 74,6 % | 98,1 km² | 2.235 hm³ | 69,2 % | 247 |
| E02 + E04 + E08 | 11.951 km² | 61,5 % | 88,6 km² | 2.104 hm³ | 65,1 % | 281 |
| **E02 + E04** | 11.089 km² | **57,0 %** | 73,1 km² | 1.794 hm³ | 55,5 % | 406 |
| E12 isolado | 15.760 km² | 81,1 % | 35,6 km² | 488 hm³ | 15,1 % | 104 |

**Os eixos prioritários têm volume mas não têm cobertura.** E02 + E04 controlam **57%** da bacia em Estrela. Os 43% restantes — ~8.350 km² — impõem piso da ordem de **7.700 m³/s**, quase o dobro do limiar estimado de dano relevante.

**Inversamente, os eixos com boa cobertura são os que conflitam com a cascata.** E12 controla 81% mas fica em 488 hm³ — 15% do necessário.

**Nenhum arranjo resolve as duas coisas.** Os que combinam cobertura e volume dependem de eixos condicionados e inundam de 98 a 109 km².

Consequência: barramentos devem ser tratados como **componente de arranjo híbrido**, não como solução isolada. O texto técnico está em `CLAUDE_SELECAO_EIXOS.md`.

---

## 5. Insumos do HEC‑RAS 1D — prontos

Geometrias em `claude_hecras_eixo.gpkg` (camadas `eixo_rio`, `secoes`, `travessias`, `confluencias`), prontas para QGIS e RAS Mapper.

| Item | Valor |
|---|---:|
| Extensão do trecho | **39,40 km** |
| Cota do talvegue | 22,0 → 13,5 m |
| Declividade média | **0,216 m/km** |
| Seções propostas | **102** (37 no detalhado) |
| Espaçamento | 200 m detalhado / 500 m estendido |

**Travessias (4):**

| Tipo | ID | Estaca RAS | Dist. montante | Conferir |
|---|---|---:|---:|:--:|
| Estadual | S/I | 18.762 m | 20,64 km | não |
| Estadual | S/I | 16.933 m | 22,47 km | **sim** |
| **Federal** | **BR‑386** | 13.099 m | 26,30 km | não |
| Estadual | RS‑130 | 8.367 m | 31,04 km | não |

**Confluências (6):** Rio Forqueta 2.844,8 km² (**14,63%** da bacia — entrar concentrado), Boa Vista 576,5 km² (2,97%), Sampaio 254,8 km², Estrela 241,0 km², Grande 60,9 km², do Meio 24,3 km².

> O traçado do KMZ vinha de jusante para montante e foi invertido, com verificação pela cota das extremidades. O estaqueamento é entregue nas duas convenções.

### 5.1 Alertas do HEC‑RAS

**A condição de jusante é frágil.** A declividade dos últimos 10 km é de **6,3 × 10⁻⁵ m/m**, obtida por regressão sobre a cota bruta — o talvegue forçado a monotônico ficou **exatamente plano** e daria `normal depth` com S = 0, que o HEC‑RAS não aceita. Nessa ordem de grandeza, **o nível em Estrela pode ser governado pelo remanso de jusante**, não pela capacidade local. Testar sensibilidade variando S em uma ordem de grandeza; considerar estender até a foz.

**Uma travessia precisa de conferência** — a de 22,47 km tem cota 10,5 m acima do talvegue local. Ponto de interseção fora do leito, ou greide de aterro sobre a planície.

**As cotas de 14,0 m nas travessias são a superfície da água**, não leito nem tabuleiro. Servem só para localizar.

---

## 6. Pendências que bloqueiam o fechamento

| Insumo | Bloqueia | Origem |
|---|---|---|
| Séries de vazão ANA (`01_baixa_dados_ana.R` nunca executado) | calibração de tudo | ANA/HidroWeb |
| Roteamento das alternativas revisadas | conversão volume → redução de pico | trilha de modelagem |
| Cota de tabuleiro e vão das pontes | estruturas no 1D | Eixo 1 |
| Batimetria / seções topobatimétricas | geometria do 1D | Eixo 1 |
| Curva‑chave em Estrela | condição de contorno e cota→vazão | Eixo 1 |
| Esclarecimento do datum de Monte Claro | restrição de E09 | ANA / concessionária |

**O mais crítico:** ninguém rodou o **roteamento com as alturas revisadas**. Sabe‑se que E02+E04 dão 1.794 hm³ de espera, mas o volume **não se converte diretamente em redução de pico** — depende do hidrograma, da regra operativa e da defasagem entre a parcela controlada e a livre. Sem isso, a carteira não pode ser fechada.

---

## 7. Correções que fiz nos meus próprios números

Registradas porque indicam onde revisar:

1. **Dupla contagem do volume de espera** no SINV — o manual desconta o Vesp ao definir o NAmxn (4.6.1) e novamente na eq. 4.6.1.03. Com um único valor de Vesp isso é dupla contagem; passei a descontar uma vez só.
2. **Energia firme acima da potência instalada** — aplicar a eq. 4.6.1.01 direto com a Qmlt dava 133 MW médios para a 14 de Julho, que tem 100 MW. Passei a usar a vazão do período crítico (razão 0,55) e limitar pela potência instalada.
3. **Regressão regional descartada** pelo expoente implausível (§1.3).
4. **Declividade de jusante zero** no HEC‑RAS, por causa do talvegue monotônico (§5.1).
5. **Colocação por área de drenagem** no perfil longitudinal projetava usinas de tributários em estacas erradas; troquei por colocação geométrica.

---

## 8. Arquivos gerados

Todos em `06_resultados/CLAUDE/`.

**Documentos:** `CLAUDE_SELECAO_EIXOS.md` (texto técnico), `CLAUDE_ROTEIRO_HECRAS_1D.md` (roteiro + insumos, §11), `CLAUDE_STATUS.md` (histórico completo com adendos), `CLAUDE_ACHADOS_PARA_CODEX.md` (este).

**Tabelas:** `claude_eixos_ficha_final.csv`, `claude_alternativas_finais.csv`, `claude_cav_eixos_consolidada.csv`, `claude_altura_admissivel_revisada.csv`, `claude_comparacao_altura_admissivel.csv`, `claude_auditoria_polinomios_cav.csv`, `claude_interferencia_energetica.csv`, `claude_balanco_energetico_liquido.csv`, `claude_vazao_especifica_calibrada.csv`, `claude_sinv_*_v2.csv`, `claude_hecras_*.csv`, `claude_perfil_principal.csv`, `claude_quedas_por_trecho.csv`.

**Geometrias:** `claude_hecras_eixo.gpkg`.

**Figura:** `claude_divisao_quedas.png`.

**Scripts:** `07_python/claude_01` a `claude_07`.
