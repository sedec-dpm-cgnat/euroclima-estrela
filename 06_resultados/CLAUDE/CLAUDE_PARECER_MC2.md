# Parecer técnico — eixo exploratório EIXO‑MONTECLARO2 (MC2)

**Projeto EUROCLIMA+ / AECID — componente técnico SEDEC/MIDR**
**Trilha de validação técnica independente · 31/07/2026**

**Arquivo avaliado:** `Documentos EUROCLIMA+/Espanha/kmz/EIXO-MONTECLARO2.kmz`
**Base:** `EUROCLIMA-rev.kmz` (12 eixos, carteira preservada)
**Rodada isolada:** `OUTPUT_TAG=mc2` → `01_dados/cav_mc2`, `01_dados/gis_derivado_mc2`

> **Código provisório: MC2.** Não foi promovido a E13. A carteira original de 12 eixos permanece intacta.

---

## Sumário do parecer

**Recomendação: DESCARTAR da carteira principal.** Manter apenas como registro de sensibilidade documental.

O motivo não é técnico‑construtivo: o eixo é viável em si. É que **MC2 é dominado por E09** — mesmo sítio, mesma restrição, metade do volume — e o volume que ambos oferecem é irrelevante para a finalidade de controle de cheias.

---

## 1. Achado prévio — falha de ancoragem no pipeline

Na rodada `OUTPUT_TAG=mc2`, o eixo recebeu **área de drenagem D8 igual a ZERO**, contra 12.423,8 km² indicados pela BHO. **Esse resultado não é válido e não deve ser usado.**

A causa está na função `ancora()` de `10_eixos_cascata.py`:

```python
perto = bho[bho.geometry.distance(geom) < 400]
ln = perto.sort_values("nuareamont", ascending=False).iloc[0]
```

Ela escolhe o trecho BHO de **maior área de montante** num raio de 400 m, e não aquele que efetivamente **intercepta** a linha. No caso do MC2 havia dois trechos do mesmo curso d'água:

| Trecho | Distância à linha | Área de montante |
|---|---:|---:|
| 786 | **0 m** | 12.318,5 km² |
| 786 | 397 m | **12.423,8 km²** ← escolhido |

Escolhido o segundo, o ponto de ancoragem foi projetado na extremidade da linha, e a janela de busca de ±10 células (±286 m) não alcançou o canal — que está na estaca 387 m da linha. O resultado saiu zero.

**Correção aplicada nesta validação:** entre os trechos que efetivamente interceptam a linha (distância ≤ meia célula), escolhe‑se o de maior área. Com isso a ancoragem funciona e a aderência à BHO fica em **−0,76%**, dentro da faixa dos demais eixos.

> **Para o Codex:** a correção está implementada em `claude_09_valida_mc2.py`, não em `10_eixos_cascata.py` — não editei o arquivo compartilhado. **A falha afeta qualquer eixo curto próximo a uma quebra de trecho da BHO**, e vale corrigir no pipeline antes da próxima rodada com novos pontos.

---

## 2. Geometria recebida

| Item | Valor |
|---|---:|
| Vértices | 2 |
| Extensão da linha | 821,5 m |
| Azimute | 115,2° |
| Ponto médio | −29,0455307 ; −51,5562985 |
| Altitudes no KML | 801,5 m → 737,2 m |

As altitudes do KML são do Google Earth. Confrontadas com o MDE:

| Vértice | KML | MDE | Diferença |
|---|---:|---:|---:|
| 1 | 801,5 m | 251,8 m | **+549,8 m** |
| 2 | 737,2 m | 229,5 m | **+507,6 m** |

A discrepância de mais de 500 m confirma que **as altitudes do KML não têm relação com o terreno** e não podem ser usadas como cota de projeto, como o plano de trabalho já advertia. Foram descartadas.

---

## 3. Validação — os sete itens

### 3.1 Código lógico e posição longitudinal

| Item | Valor |
|---|---:|
| Código provisório | **MC2** |
| Coordenadas do ponto ancorado | −29,045481 ; −51,556409 |
| Estaca no perfil principal | **294,5 km** |
| Distância ao traço do canal | 0 m |

A estaca de 294,5 km **confirma** os 294,48 km informados no plano de trabalho.

### 3.2 Área contribuinte

| Fonte | Área |
|---|---:|
| Grade D8 (MDE 28,6 m) | **12.225,3 km²** |
| BHO/ANA (trecho interceptado) | 12.318,5 km² |
| Aderência | **−0,76 %** |

Corresponde a **62,9%** da área de drenagem em Estrela (19.440 km²).

### 3.3 CAV e altura admissível

Curva derivada do MDE natural, densificada por PCHIP monotônica em passos de 1 m — mesma metodologia dos 12 eixos da carteira. Confiabilidade **classe B**.

| Altura | Cota NA | Área alagada | Volume |
|---:|---:|---:|---:|
| 10 m | 117,5 m | 1,10 km² | 5,3 hm³ |
| 20 m | 127,5 m | 1,97 km² | 20,4 hm³ |
| **23 m** | **130,5 m** | **2,32 km²** | **26,8 hm³** |
| 30 m | 137,5 m | 3,15 km² | 45,9 hm³ |
| 50 m | 157,5 m | 7,18 km² | 143,8 hm³ |

**Altura admissível: 23,0 m**, limitada pelo remanso da **UHE Monte Claro** (estaca 279,5 km, cota 132,5 m no MDE), com folga de 2 m.

Geometria da barragem nessa altura: crista de **243,4 m**, aterro de **0,289 hm³**, custo preliminar de **R$ 52 milhões**.

### 3.4 Interferência e remanso

| Usina | Leito no eixo | NA normal | Mínima operacional | Queda bruta |
|---|---:|---:|---:|---:|
| Monte Claro | 116,88 m | 148,0 m | 147,0 m | 31,12 m |
| 14 de Julho | 62,37 m | 104,0 m | 103,0 m | 41,63 m |
| Castro Alves | 187,05 m | 240,0 m | 239,0 m | 52,95 m |

**Monte Claro é a usina imediatamente a montante** e governa a restrição. A perda de queda começa quando o NA do MC2 ultrapassa a cota do leito de Monte Claro (116,88 m), ou seja, a partir de **9,4 m de altura**.

**14 de Julho não é afetada** — está a jusante do MC2 (leito em 62,37 m, abaixo da cota do eixo de 107,5 m).

**Castro Alves não é afetada** — leito em 187,05 m, muito acima de qualquer NA viável do MC2.

### 3.5 Energia nova, perdida e balanço líquido

Vazão específica calibrada de 0,0269 m³/s/km² (Qmlt oficial SNIRH), razão de período crítico 0,55.

| Altura | Gera | Retira de Monte Claro | **Líquido** | Veto | Dentro da adm. |
|---:|---:|---:|---:|:--:|:--:|
| 10 m | 15,6 | 0,9 | **+14,7** | não | sim |
| **20 m** | **31,2** | **16,2** | **+15,0** | não | **sim** |
| 30 m | 46,8 | 31,4 | +15,4 | não | não |
| 40 m | 62,4 | 46,6 | +15,8 | **sim** | não |
| 60 m | 93,6 | 47,3 | +46,3 | **sim** | não |
| 120 m | 187,2 | 47,3 | +139,9 | **sim** | não |

*MW médios.*

**O balanço líquido é positivo, mas quase constante em ~15 MW médios dentro da faixa admissível.** Cada metro adicional de altura gera energia nova e retira quase exatamente a mesma quantidade de Monte Claro. Acima de 40 m há **veto** — o remanso atinge a cota mínima operacional de Monte Claro (147,0 m).

Na altura admissível de 23 m, o ganho líquido é da ordem de **15 MW médios**, ao custo de R$ 52 M de obra civil mais equipamentos.

### 3.6 Efeito no roteamento de cheias

Este é o item decisivo.

| Item | Valor |
|---|---:|
| Volume na altura admissível | 26,8 hm³ |
| Fração do volume necessário (3.230 hm³) | **0,83 %** |
| Vazão de pico afluente ao MC2 | ~12.135 m³/s |
| **Tempo para encher o reservatório no pico** | **37 minutos** |

**O reservatório enche em pouco mais de meia hora durante o pico da cheia.** Depois disso passa a transferir integralmente a vazão afluente. Para efeito de controle de cheias, a contribuição é indistinguível de zero.

Para comparação, E09 — no mesmo trecho — enche em 82 minutos. Também insuficiente, mas o dobro.

### 3.7 Comparação com a carteira existente

| Eixo | Distância ao MC2 | Área | Cota | Altura adm. | Volume adm. |
|---|---:|---:|---:|---:|---:|
| **MC2** | — | 12.225,3 km² | 107,5 m | 23,0 m | **26,8 hm³** |
| **E09** | **1.033 m** | 12.330,0 km² | 106,0 m | 24,5 m | **59,7 hm³** |
| E08 | 7.741 m | 11.950,5 km² | 148,0 m | 86,0 m | 621,1 hm³ |
| E07 | 8.923 m | 8.173,5 km² | 149,5 m | 84,5 m | 385,4 hm³ |

**MC2 e E09 são praticamente o mesmo sítio** — 1.033 m de distância, mesma área de drenagem (diferença de 0,9%), mesma restrição de montante (Monte Claro).

**E09 é superior em tudo o que importa:** está 1,5 m mais baixo, o que lhe dá 1,5 m a mais de altura admissível, e o vale é menos encaixado — resultando em **59,7 hm³ contra 26,8 hm³, mais que o dobro** pela mesma restrição.

---

## 4. Recomendação

### **DESCARTAR da carteira principal.**

Três razões, em ordem de peso:

1. **É dominado por E09.** Mesmo sítio, mesma restrição, 45% do volume. Não há critério pelo qual MC2 supere E09 — se o trecho for aproveitado, é em E09, não aqui.

2. **O volume é irrelevante para controle de cheias.** 26,8 hm³ são 0,83% do necessário, e o reservatório satura em 37 minutos no pico. Mesmo somado a toda a carteira, não altera o resultado.

3. **O ganho energético não compensa isoladamente.** Cerca de 15 MW médios líquidos, porque cada metro de altura retira de Monte Claro quase o que gera. Um aproveitamento de 12.225 km² que entrega 15 MW médios líquidos não se justifica.

### O que fazer com ele

**Manter como registro de sensibilidade documental**, com duas utilidades:

- **Confirma a robustez da restrição de Monte Claro.** Dois eixos independentes no mesmo trecho, propostos separadamente, chegam ao mesmo limite de ~23 a 25 m. Isso reforça a conclusão de que o trecho entre Monte Claro e 14 de Julho está energeticamente saturado.
- **Serve de caso‑teste da falha de ancoragem** descrita no §1, que precisa ser corrigida no pipeline.

### O que **não** fazer

- Não promover a E13.
- Não incorporar à carteira de alternativas.
- Não usar os resultados da rodada `OUTPUT_TAG=mc2` para este eixo — a área saiu zero. Usar os desta validação.

---

## 5. Ressalvas

**Cota de Monte Claro.** A restrição de MC2 usa a cota amostrada no MDE (132,5 m). A cota oficial do SNIRH é **148,0 m** — diferença de 15,5 m ainda não esclarecida. Se a cota oficial prevalecer, a altura admissível do MC2 subiria para ~38,5 m e o volume para ~78 hm³. **Continuaria irrelevante** para controle de cheias (2,4% do necessário, 108 minutos de enchimento), mas a ficha mudaria. A pendência é a mesma que afeta E09.

**Volume classe B.** Derivado de MDE de 28,6 m, sem assoreamento, volume morto ou restrições de fundação.

**Sem verificação geotécnica, ambiental ou fundiária.** A área alagada de 2,32 km² é pequena, mas não foi cruzada com uso do solo nem com edificações.

**Parâmetros não calibrados.** Pico de referência (18.000 m³/s), volume necessário (3.230 hm³) e razão de período crítico (0,55) permanecem estimativas.

---

## 6. Arquivos entregues

Todos em `06_resultados/CLAUDE/`, sem sobrescrever nada da carteira:

| Arquivo | Conteúdo |
|---|---|
| `claude_mc2_validacao.csv` | Ficha completa do candidato |
| `claude_mc2_cav.csv` | CAV PCHIP de 1 m, 10 a 120 m |
| `claude_mc2_interferencia.csv` | Remanso, energia e balanço por altura |
| `claude_mc2_diagnostico.csv` | Diagnóstico da falha de ancoragem |
| `claude_mc2_varredura.csv` | Área D8 ao longo da linha, a cada 25 m |
| `CLAUDE_PARECER_MC2.md` | Este documento |

**Scripts:** `07_python/claude_08_diagnostico_mc2.py`, `07_python/claude_09_valida_mc2.py`.

Nenhum arquivo `.qmd` foi tocado. `10_eixos_cascata.py` não foi editado.
