# Auditoria da entrada candidata ao Kirsch–Nowak

**Script:** `07_python/45_audita_entrada_kirsch_nowak.py`  
**Regra:** diagnóstico somente; nenhum dado original foi alterado ou preenchido.

## Resultado por série

| Posto | Nome | Papel | Período | Registros | Lacunas | Completude | 29/02 | Negativos | Status |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| 86510000 | Muçum / Antas | treinamento; componente do Antas | 1940-01-01 a 2026-03-31 | 31440 | 62 | 99.8% | 22 | 0 | ok |
| 86720000 | Encantado / Antas | treinamento ou validação intermediária; posto aninhado | 1941-10-15 a 2026-01-31 | 24530 | 6260 | 79.67% | 17 | 0 | ok |
| 86745000 | Passo do Coimbra / Forqueta | treinamento; componente lateral do Forqueta | 1957-07-10 a 2026-03-31 | 24713 | 389 | 98.45% | 17 | 0 | ok |
| 86580000 | Santa Lúcia / Guaporé | treinamento; componente lateral do Guaporé | 1940-01-01 a 2024-04-30 | 30591 | 211 | 99.31% | 21 | 0 | ok |
| 86879300 | Estrela | validação do exutório; não recomendado para treinamento longo | 2020-11-25 a 2023-12-31 | 1063 | 69 | 93.9% | 0 | 0 | ok |

## Janela comum preliminar

Considerando Muçum, Encantado, Forqueta e Guaporé como candidatos de treinamento, a janela bruta comum é **1957-07-10 a 2024-04-30**, aproximadamente **66.9 anos de calendário de 365 dias**. Ela ainda precisa ser recalculada depois da auditoria de lacunas e consistência; portanto não equivale a 66,9 anos completos utilizáveis.

A série de Estrela (86879300) é curta e deve ser reservada para validação do exutório. O gerador exige uma entrada diária harmonizada, sem anos bissextos e com tratamento documentado das lacunas; este script apenas identifica esses pontos. Também não resolve a escolha entre vazões de postos aninhados e incrementos hidrológicos, que deve ser feita pela topologia do modelo.
