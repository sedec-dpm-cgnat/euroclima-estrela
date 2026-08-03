# Avaliação preliminar de alteamento e alternativas

**Projeto:** EUROCLIMA+ / AECID — redução do risco de cheias em Estrela e bacia do Taquari-Antas  
**Estado:** triagem reproduzível, sem valor de orçamento executivo  
**Entradas principais:** `volume_espera_existentes.csv` e `altura_maxima_admissivel.csv` (o custo desta última é o benchmark interno dos eixos admissíveis)

## Resultado executivo

O alteamento das barragens existentes não fecha a lacuna de armazenamento identificada no projeto. Mesmo o cenário geométrico de **+20 m em toda a cascata** soma somente **635,2 hm³**, ou **19,7%** dos **3.230 hm³** de referência.

Os números acima são **limites superiores geométricos**, porque o MDE vê a água no NA atual e não contém batimetria abaixo dela. Eles não autorizam concluir que esse volume pode ser operado como volume de espera.

## Decisão de escopo — atualização de 30/07/2026

O alteamento das UHEs existentes fica em segundo plano, como diagnóstico de sensibilidade e indicação de que seriam necessárias intervenções expressivas. A carteira principal passa a ser formada por novos eixos/barragens que não afoguem diretamente as usinas existentes. A triagem reproduzível está em `tabelas/prioridade_eixos_sem_interferencia.csv`.

Uma revisão longitudinal posterior corrigiu a ordem de montante/jusante usando o perfil geométrico do talvegue. A auditoria independente reproduziu o resultado. Na nova triagem, **E02 e E04 são os candidatos prioritários de baixa interferência da cascata existente até o teto hipotético de 120 m**; E01 permanece como alternativa em tributário; E05 volta a ser viável, mas limitado por Castro Alves; E09 e E10 passam a ser limitados por Monte Claro e 14 de Julho, respectivamente. A tabela revisada está em `tabelas/prioridade_eixos_revisada.csv`.

O volume geométrico positivo revisado chega a **6.855 hm³**, com **3.588 hm³ em E02 + E04**. Esses números não substituem uma análise de engenharia: 120 m é teto de triagem, as curvas geométricas terminam nesse limite e ainda faltam confirmação de conectividade, aproveitamentos intermediários, geotecnia, hidrologia conjunta e remanso.

Portanto, **nenhum eixo é declarado sem interferência comprovada** antes da validação hidráulica, cadastro atualizado e campo. A versão anterior de 2.565 hm³ é mantida apenas como comparação histórica do critério antigo.

Para a lacuna abaixo do NA, foi executada uma adaptação de triagem inspirada em Domeneghetti (2016), que infere geometria submersa a partir de relevo e superfície. O `mdr.tif` reconstruiu 6 de 20 usinas; a sensibilidade com o recorte ANADEM reconstruiu 17 de 20. A comparação está em `COMPARACAO_MDES_BATIMETRIA.md`. As divergências mostram que a cobertura e a fonte do MDE são incertezas relevantes; os resultados servem para orientar batimetria e sensibilidade, não para substituir curvas cota×volume.

Os maiores contribuintes a +10 m são: **14 de Julho (81,7 hm³); Castro Alves (38,7 hm³); Da Ilha (17,3 hm³)**. A concentração da capacidade em poucos reservatórios reforça a necessidade de verificar a cascata do rio das Antas e os limites de remanso antes de qualquer estudo de engenharia.

## Faixa paramétrica de custo

| Faixa de alteamento | Volume-limite acima do NA | % dos 3.230 hm³ | Custo triagem baixo | Custo triagem base | Custo triagem alto |
|---:|---:|---:|---:|---:|---:|
| +1 m | 6,9 | 0,2% | R$ 10 M | R$ 20 M | R$ 36 M |
| +2 m | 19,9 | 0,6% | R$ 28 M | R$ 57 M | R$ 104 M |
| +3 m | 36,5 | 1,1% | R$ 52 M | R$ 105 M | R$ 190 M |
| +5 m | 79,6 | 2,5% | R$ 113 M | R$ 230 M | R$ 415 M |
| +8 m | 158,8 | 4,9% | R$ 225 M | R$ 458 M | R$ 829 M |
| +10 m | 219,9 | 6,8% | R$ 311 M | R$ 634 M | R$ 1.147 M |
| +15 m | 401,2 | 12,4% | R$ 568 M | R$ 1.157 M | R$ 2.094 M |
| +20 m | 635,2 | 19,7% | R$ 899 M | R$ 1.831 M | R$ 3.315 M |

O benchmark interno foi calculado em **11 eixos admissíveis**, com custo de novos eixos entre **0,59 M R$/hm³ e 3,89 M R$/hm³**; os percentis 25/50/75 usados na tabela são **0,94 M R$/hm³ / 1,44 M R$/hm³ / 1,74 M R$/hm³**. Sobre essas taxas foram aplicados fatores de alteamento **1,5 / 2,0 / 3,0**.

Esses valores são uma **faixa de sensibilidade**, não uma estimativa de CAPEX. O custo de um alteamento depende principalmente de tipo e estado da barragem, fundações, comprimento de crista, vertedouro, comportas, instrumentação, acessos, desapropriações, realocação de infraestrutura, operação durante a obra, licenciamento e medidas de segurança. Nenhum desses dados está disponível de forma suficiente para orçar as 20 usinas.

O placeholder de dano de **R$ 2.500 M** não deve ser usado para validar economicamente o alteamento antes da recalibração do dano evitável por cenário. A comparação correta deve seguir o ICB do Manual de Inventário, depois que o benefício for obtido por simulação hidrológico-hidráulica e não por proporção simples de hm³.

## Como fazer, se a alternativa sobreviver à triagem

1. **Dados e diagnóstico:** obter projeto “as built”, tipo estrutural, cotas, instrumentação, inspeções, curvas cota-área-volume, batimetria e topobatimetria de cada reservatório candidato.
2. **Segurança e hidráulica:** verificar estabilidade, fundação, percolação, borda livre, capacidade do vertedouro, comportas, dissipação, cheias de projeto e propagação do remanso na cascata.
3. **Operação:** definir NA normal e máximo, volume de espera, regra de deplecionamento, reenchimento em até 36 meses quando aplicável, vazões remanescentes, geração perdida e coordenação entre operadores.
4. **Território e ambiente:** mapear a área adicional inundada, imóveis, pontes, estradas, linhas, captações, unidades de conservação, patrimônio e necessidade de reassentamento.
5. **Anteprojeto e decisão:** comparar CAPEX, OPEX, energia, dano evitado, segurança e licenciamento com alternativas sem alteamento; eliminar alternativas dominadas antes do detalhamento.
6. **Execução:** somente após aprovação de segurança e licenciamento definir a sequência construtiva, desvios, rebaixamento temporário, reforço de crista/ombreiras, extravasores e comissionamento.

## Limites que impedem uma decisão executiva hoje

- **Volume:** +10 m = aproximadamente 220 hm³ e +20 m = aproximadamente 635 hm³ na aproximação atual; a ordem de grandeza permanece muito abaixo da necessidade de referência.
- **Dados:** não há batimetria/cotas-volume confiáveis abaixo do NA atual; não há inventário estrutural suficiente para assumir que as barragens aceitam alteamento.
- **Cascata:** o remanso e a inundação de usinas existentes dominam a altura admissível dos eixos novos; esse mesmo cuidado deve ser aplicado a qualquer alteamento.
- **Hidráulica:** sem roteamento em cascata, vertedouro e operação coordenada, volume armazenado não equivale a redução do pico em Estrela.
- **Território:** a área adicional, edificações e infraestrutura por metro ainda precisam ser cruzadas com cadastro e manchas hidráulicas; a tabela atual só informa o espelho atual.
- **Regulação e segurança:** qualquer intervenção em barragem existente exige avaliação específica de segurança, responsabilidades do empreendedor, operação, emergência e licenciamento.

## Alternativas sem alteamento

| Prioridade | Alternativa | Tipo | Efeito esperado |
|---:|---|---|---|
| 1 | CAV real + deplecionamento preventivo | operacional | Mobiliza parte do volume já existente antes de eventos previstos; quantificação ainda bloqueada pela ausência de batimetria. |
| 2 | Operação coordenada de comportas e vertedouros | operacional | Sincroniza a liberação dos reservatórios com a onda de cheia e evita contribuição atrasada da cascata. |
| 3 | Previsão, alerta e protocolo de resposta | gestão de risco | Reduz exposição e tempo de resposta mesmo sem reduzir o pico hidrológico. |
| 4 | Ordenamento territorial e adaptação urbana | redução de exposição | Evita novas perdas e protege infraestrutura crítica nas cotas de inundação. |
| 5 | Medidas naturais e retenções distribuídas na bacia | baseada na natureza | Retarda escoamento e reduz contribuição de sub-bacias, especialmente em eventos frequentes e moderados. |
| 6 | Barragem seca ou novo eixo admissível | obra nova | Cria controle dedicado de cheias sem elevar a crista das usinas existentes. |

### Carteira de eixos sem interferência direta — triagem

| Ordem | Eixo | Classe atual | Volume admissível | Decisão |
|---:|---|---|---:|---|
| 1 | E02 | candidato prioritário de baixa interferência | 31,6 hm³ | Validar primeiro; não é aprovação. |
| 2 | E01 / E04 | independente, mas com conflito operacional | 129,1 / 124,8 hm³ | Só avançar após remanso e regra operativa. |
| 3 | E10 / E11 / E12 | cascata crítica | 480,9 / 400,3 / 977,7 hm³ | Cenários condicionados à cascata; não carteira principal. |
| — | E05 | inviável na altura admissível atual | — | Retirar da carteira. |

### Recomendação de sequência

1. Solicitar as curvas cota×volume e regras operativas à ANA, ONS e concessionárias, começando pela CERAN (Monte Claro, Castro Alves e 14 de Julho).
2. Rodar a alternativa de deplecionamento preventivo com CAV real e o SINV somente dentro das alturas fisicamente admissíveis.
3. Avançar em paralelo com previsão/alerta, HEC-RAS 1D, ordenamento territorial e medidas distribuídas, pois essas frentes não dependem de demonstrar viabilidade de alteamento.
4. Só contratar inspeção/anteprojeto de alteamento para um conjunto pequeno de reservatórios que sobreviva à comparação de benefício, segurança, remanso, área adicional e custo.

## Rastreabilidade

- `07_python/14_avaliacao_alteamento.py` — script desta análise.
- `06_resultados/tabelas/volume_espera_existentes.csv` — volumes acima do NA atual; limite geométrico.
- `06_resultados/tabelas/altura_maxima_admissivel.csv` — restrições de remanso dos eixos estudados.
- `06_resultados/tabelas/altura_maxima_admissivel.csv` — custos dos eixos admissíveis usados apenas como benchmark interno de novos eixos.
- `01_dados/cav/geometria_todos.csv` — origem do pipeline geométrico que alimenta o custo dos novos eixos; não é custo histórico das UHEs.
- `07_python/14_batimetria_sintetica.py` — adaptação de triagem inspirada em Domeneghetti (2016); resultados sintéticos, ainda não calibrados.
- `07_python/15_prioriza_eixos_sem_interferencia.py` — classificação de escopo dos eixos.
- `07_python/16_extrai_atlas_danos.py` — extração documentada do Atlas por município e recorte temporal.
- `07_python/17_organiza_gis.py` — GeoPackage mestre e exportações SHP/KMZ.
- `06_resultados/CURVA_COTA_DANO_ESTRATEGIA.md` — estratégia IBGE/IpeaGEO/Atlas para a curva cota–dano.
- Manual de Inventário Hidroelétrico e Bacias Hidrográficas, capítulos 4.6, 4.11 e 5.3 — volumes de espera, comparação econômica e simulação final.
