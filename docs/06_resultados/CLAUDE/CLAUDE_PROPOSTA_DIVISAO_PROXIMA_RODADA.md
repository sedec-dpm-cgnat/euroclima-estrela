# Proposta de divisão de trabalho — próxima rodada

**Origem:** trilha de validação técnica independente (Claude)
**Data:** 31/07/2026
**Para:** decisão do gestor e acordo com o Codex

> Proposta. Nada foi iniciado sem acordo. Os itens marcados como **compartilhados** exigem comunicação antes de editar, conforme a regra já vigente no plano de trabalho paralelo.

---

## Objetivo da rodada

Fechar a carteira de alternativas com base defensável, ou seja: converter **volume de espera** em **redução de pico verificada**, e substituir os parâmetros arbitrados por dados observados. Sem isso, a recomendação de E02+E04 permanece sustentada apenas por volume geométrico.

---

## Divisão proposta

### Claude — trilha de modelagem hidráulica e energética

| # | Tarefa | Produto | Depende de |
|---|---|---|---|
| **C1** | **Roteamento das alternativas revisadas** — Puls com as alturas admissíveis, decomposição controlado/não‑controlado, regra operativa com comportas e deplecionamento preventivo | `claude_roteamento_alternativas.csv` · hidrogramas por cenário · redução de pico verificada por alternativa | nada — pode começar |
| **C2** | **Baixar e consolidar as séries ANA** (postos 86870000, 86879300, 86510000, 86720000) e digitalizar a série consistida 1939–2023 da UFRGS | `claude_series_ana.csv` · `claude_serie_consistida_lajeado.csv` | nada — pode começar |
| **C3** | **Recalibrar o evento de referência** — pico, lâmina escoada, curva de frequência e o limiar de dano relevante | `PAR_EVENTO` calibrado · nova curva Q(TR) | C2 |
| **C4** | **Reprocessar SINV e alternativas** com os parâmetros calibrados | `claude_sinv_*_v3.csv` · `claude_alternativas_finais_v2.csv` | C3 |
| **C5** | **Casos HEC‑RAS 1D** dos cenários com E02 e E04 — hidrogramas efluentes como condição de contorno de montante | `claude_hecras_planos.csv` · séries de contorno por plano | C1 |
| **C6** | **Revisar sincronização dos tributários** — defasagem de pico do Forqueta (14,63% da bacia) e dos demais | nota técnica curta + parâmetros de defasagem | C2 |

### Codex — trilha de relatório, figuras, geodados e integração

| # | Tarefa | Produto |
|---|---|---|
| **X1** | **Corrigir a ancoragem em `10_eixos_cascata.py`** — critério de interseção em vez de maior área no raio; verificação de sanidade `área_D8/área_BHO` fora de 0,9–1,1 | pipeline corrigido |
| **X2** | **Revalidar os 12 eixos** após a correção, confirmando que as aderências não mudam | log de revalidação |
| **X3** | **Esclarecer o datum de Monte Claro** — 132,5 m (MDE) contra 148,0 m (SNIRH) | nota de conciliação; fichas de MC2 e E09 atualizadas |
| **X4** | **Incorporar o parecer MC2** ao KMZ consolidado e aos capítulos, registrando que as altitudes do KML não têm significado altimétrico | `eixos_exploratorios_propostos.kmz` · capítulo |
| **X5** | **Capítulos `.qmd`, figuras e template** — divisão de quedas por alternativa, HAND, CAVs, limitações | site Quarto |
| **X6** | **Base territorial e curva cota‑dano** — Atlas, setores censitários, população, tipologias, SINAPI/CUB‑RS | base de exposição |
| **X7** | **Custo‑benefício auditável** — EAD por cenário com faixas de incerteza | planilha CBA |

### Compartilhados — avisar antes de editar

| Arquivo | Quem costuma tocar | Regra |
|---|---|---|
| `10_eixos_cascata.py` | Codex (X1) | Claude não edita; propõe por escrito |
| `cav_todos.csv`, `geometria_todos.csv` | Codex | Claude só lê |
| `prioridade_eixos_revisada.csv` | Codex | Claude só lê |
| `claude_*` e `06_resultados/CLAUDE/` | Claude | Codex só lê |
| `*.qmd` | Codex | Claude não edita |
| `HANDOFF.md`, `STATUS_ATUAL_PROJETO.md`, `PLANO_DE_ACAO.md` | Codex | Claude não edita |

---

## Sequência e dependências

```
C1 (roteamento) ──────────────► C5 (casos HEC-RAS)
                                      │
C2 (séries ANA) ──► C3 (calibração) ──► C4 (SINV v3)
        └─────────► C6 (defasagem tributários)

X1 (corrigir ancoragem) ──► X2 (revalidar eixos)
X3 (datum Monte Claro) ───► fichas MC2/E09
X6 (exposição) ───────────► X7 (custo-benefício) ◄── C4
```

**Caminho crítico:** C1 e C2 são independentes e podem correr em paralelo desde já. X1 é rápido e desbloqueia qualquer rodada futura com novos pontos. X7 depende de C4 e X6 — é o último item.

---

## Ponto de convergência

O produto que fecha a rodada é a **tabela de alternativas com redução de pico verificada e custo‑benefício**, combinando:

- de Claude: redução de pico por alternativa (C1), parâmetros calibrados (C3), energia e ICB (C4);
- do Codex: dano evitado por cenário (X6, X7).

Sugiro que essa tabela seja construída pelo Codex, consumindo `claude_alternativas_finais_v2.csv`, para manter num só lugar a rastreabilidade da origem de cada número.

---

## O que esta rodada deve resolver

| Pergunta em aberto | Quem responde |
|---|---|
| E02+E04 controlam 57% da bacia — quanto isso de fato reduz o pico em Estrela? | **C1** |
| O pico de 18.000 m³/s e os 3.230 hm³ necessários se confirmam? | **C3** |
| A vazão específica de 0,0269 m³/s/km² se confirma fora das três UHEs? | **C2, C3** |
| O limiar de 4.000 m³/s sem dano relevante é o correto? | **C5** e **X6** |
| Monte Claro está em 132,5 ou 148,0 m? | **X3** |
| O pipeline erra em eixos curtos perto de quebras da BHO? | **X1, X2** |

---

## Riscos da divisão

**As séries da ANA podem não vir.** O endpoint SOAP legado do HidroWeb é instável e nunca foi testado neste projeto. Se falhar, C3 e C4 travam. Plano B: usar a série consistida da UFRGS (cotas, 1939–2023) com curva‑chave estimada — pior, mas viável.

**C1 pode invalidar a recomendação de E02+E04.** Se o roteamento mostrar que 57% de cobertura não entrega redução relevante, a carteira muda. É o resultado esperado do trabalho, não um problema — mas convém que o Codex não consolide o capítulo de alternativas antes de C1.

**X3 pode alterar duas fichas.** Se a cota oficial de Monte Claro prevalecer, MC2 e E09 mudam de altura e volume. Nenhum muda de recomendação, mas as tabelas mudam.
