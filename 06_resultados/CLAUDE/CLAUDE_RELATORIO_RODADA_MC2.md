# Relatório da rodada MC2 — para o Codex

**Trilha de validação técnica independente · 31/07/2026**
**Escopo desta rodada:** validação do eixo exploratório `EIXO-MONTECLARO2.kmz`
**Arquivos compartilhados tocados:** nenhum. Nenhum `.qmd` editado. `10_eixos_cascata.py` não editado.

---

## 1. Entrega imediata

| Pergunta do plano de trabalho | Resposta |
|---|---|
| Código lógico | **MC2** (provisório — **não** promovido a E13) |
| Estaca no perfil principal | **294,5 km** — confirma os 294,48 km informados |
| Área contribuinte | **12.225,3 km²** (62,9% da bacia em Estrela) |
| Cota do eixo (MDE) | **107,5 m** |
| Altura admissível | **23,0 m** — limitada por Monte Claro |
| Volume admissível | **26,8 hm³** · área alagada 2,32 km² |
| Interferência | Só **Monte Claro**. 14 de Julho está a jusante; Castro Alves, muito acima |
| Energia líquida | **+15,0 MW médios** a 20 m |
| Efeito no roteamento | **Nulo na prática** — enche em 37 min no pico |
| **Recomendação** | **DESCARTAR da carteira principal**; manter como sensibilidade documental |

Parecer completo: `CLAUDE_PARECER_MC2.md`.

---

## 2. Bug no pipeline — precisa de correção antes da próxima rodada

**A rodada `OUTPUT_TAG=mc2` produziu área de drenagem ZERO para o MC2.** Esse número não deve ser usado.

Causa, em `10_eixos_cascata.py`, função `ancora()`:

```python
perto = bho[bho.geometry.distance(geom) < 400]
ln = perto.sort_values("nuareamont", ascending=False).iloc[0]
```

Escolhe o trecho BHO de **maior área** num raio de 400 m, e não o que **intercepta** a linha. No MC2 havia dois trechos do mesmo curso d'água:

| Trecho | Distância à linha | Área de montante | Escolhido |
|---|---:|---:|:--:|
| 786 | **0 m** | 12.318,5 km² | não |
| 786 | 397 m | **12.423,8 km²** | **sim** |

Com o trecho errado, o ponto de ancoragem foi projetado na extremidade da linha; a janela de busca de ±10 células (±286 m) não alcançou o canal, que está na estaca 387 m. A célula de melhor ajuste passou a ser encosta, com área ≈ 0.

**Correção proposta:** entre os trechos que efetivamente interceptam a linha (distância ≤ meia célula), escolher o de maior área; só recorrer ao critério por proximidade se nenhum interceptar.

```python
intercepta = bho[bho.geometry.distance(geom) <= px / 2]
if len(intercepta):
    ln = intercepta.sort_values("nuareamont", ascending=False).iloc[0]
else:
    ln = bho.sort_values("d").iloc[0]
```

Implementei em `claude_09_valida_mc2.py`. **Não editei o arquivo compartilhado** — a alteração é sua.

**Alcance do problema:** afeta qualquer eixo curto próximo a uma quebra de trecho da BHO ou a uma confluência. Os 12 eixos da carteira não foram afetados (aderências entre −0,8% e +0,1%), mas convém revalidar se novos pontos forem acrescentados.

**Verificação de sanidade sugerida no pipeline:** se `area_D8 / area_BHO` sair fora de 0,9–1,1, emitir aviso em vez de gravar o valor silenciosamente.

---

## 3. Por que MC2 é descartado

Três razões, em ordem de peso:

**É dominado por E09.** Estão a **1.033 m** um do outro, com a mesma área de drenagem (diferença de 0,9%) e a mesma restrição de montante:

| | Distância | Área | Cota | Altura adm. | Volume |
|---|---:|---:|---:|---:|---:|
| **MC2** | — | 12.225,3 km² | 107,5 m | 23,0 m | **26,8 hm³** |
| **E09** | 1.033 m | 12.330,0 km² | 106,0 m | 24,5 m | **59,7 hm³** |

E09 está 1,5 m mais baixo e num vale menos encaixado — **mais que o dobro do volume pela mesma restrição**. Se o trecho for aproveitado, é em E09.

**O volume é irrelevante para controle de cheias.** 26,8 hm³ são **0,83%** do necessário. Ao pico de ~12.135 m³/s, o reservatório **enche em 37 minutos** e passa a transferir tudo. E09 leva 82 minutos — também insuficiente.

**O ganho energético não se sustenta.** Cerca de **15 MW médios líquidos**: cada metro de altura gera energia nova e retira de Monte Claro quase a mesma quantidade. Acima de 40 m há veto por cota mínima operacional.

**Utilidade documental:** dois eixos propostos independentemente no mesmo trecho chegam ao mesmo limite de 23 a 25 m. Isso **reforça** a conclusão de que o trecho entre Monte Claro e 14 de Julho está energeticamente saturado.

---

## 4. Altitudes do KML — confirmada a advertência do plano

| Vértice | KML (Google Earth) | MDE | Diferença |
|---|---:|---:|---:|
| 1 | 801,5 m | 251,8 m | **+549,8 m** |
| 2 | 737,2 m | 229,5 m | **+507,6 m** |

Mais de 500 m de discrepância. As altitudes foram descartadas; todas as cotas do parecer vêm do MDE.

**Sugestão para o KMZ consolidado:** ao documentar as coordenadas do MC2, registrar explicitamente que as altitudes do KML não têm significado altimétrico, para evitar que sejam lidas como cota de projeto mais adiante.

---

## 5. Ressalva que pode alterar a ficha do MC2 e do E09

A restrição de ambos usa a cota de Monte Claro **amostrada no MDE: 132,5 m**. A cota oficial do SNIRH é **148,0 m** — discrepância de 15,5 m ainda sem explicação.

Se a cota oficial prevalecer:

| | Altura adm. atual | Altura adm. com 148,0 m | Volume atual | Volume revisto |
|---|---:|---:|---:|---:|
| MC2 | 23,0 m | ~38,5 m | 26,8 hm³ | ~78 hm³ |
| E09 | 24,5 m | ~40,0 m | 59,7 hm³ | ~140 hm³ |

**Nenhum dos dois muda de recomendação** — 78 hm³ ainda são 2,4% do necessário e 108 minutos de enchimento. Mas as fichas mudam, e a pendência precisa ser fechada antes do relatório final.

---

## 6. Estado da minha trilha — o que segue pendente

### 6.1 O bloqueio principal, ainda aberto

**O roteamento com as alturas revisadas não foi feito.** Sabe‑se que E02+E04 oferecem 1.794 hm³ de volume de espera, mas isso **não se converte diretamente em redução de pico**: depende do hidrograma, da regra operativa e da defasagem entre a parcela controlada (57% da bacia) e a livre (43%).

Enquanto isso não for feito, a carteira **não pode ser fechada** — e é o que sustentaria ou derrubaria a recomendação de E02+E04.

### 6.2 Insumos que faltam

| Insumo | Bloqueia | Origem |
|---|---|---|
| Séries de vazão ANA (`01_baixa_dados_ana.R` nunca executado) | calibração de tudo | ANA/HidroWeb |
| Datum de Monte Claro | fichas de MC2 e E09 | ANA / concessionária |
| Cota de tabuleiro e vão das pontes | estruturas no HEC‑RAS 1D | Eixo 1 |
| Batimetria / seções topobatimétricas | geometria do 1D | Eixo 1 |
| Curva‑chave em Estrela | condição de contorno e cota→vazão | Eixo 1 |

### 6.3 O que já entreguei e está disponível

**Documentos:** `CLAUDE_SELECAO_EIXOS.md` (texto técnico da seleção), `CLAUDE_ROTEIRO_HECRAS_1D.md` (roteiro + insumos levantados, §11), `CLAUDE_ACHADOS_PARA_CODEX.md` (achados da rodada anterior), `CLAUDE_PARECER_MC2.md`, `CLAUDE_STATUS.md`.

**Tabelas principais:** `claude_eixos_ficha_final.csv`, `claude_alternativas_finais.csv`, `claude_cav_eixos_consolidada.csv`, `claude_altura_admissivel_revisada.csv`, `claude_sinv_*_v2.csv`, `claude_hecras_*.csv`, `claude_mc2_*.csv`.

**Geometrias:** `claude_hecras_eixo.gpkg` (eixo, 102 seções, 4 travessias, 6 confluências — pronto para RAS Mapper).

---

## 7. Propostas de continuidade

Em ordem de retorno:

1. **Corrigir a ancoragem no pipeline** (§2) — é rápido e evita que a próxima rodada com novos pontos produza número errado silenciosamente.
2. **Rodar o roteamento das alternativas revisadas** — é o que fecha a carteira. Posso assumir na minha trilha.
3. **Baixar as séries ANA e recalibrar** — converte ICB e volumes de ordem de grandeza em números defensáveis.
4. **Esclarecer o datum de Monte Claro** — fecha as fichas de MC2 e E09.

Se concordar com a divisão, assumo 2 e 3; 1 e 4 dependem de você.
