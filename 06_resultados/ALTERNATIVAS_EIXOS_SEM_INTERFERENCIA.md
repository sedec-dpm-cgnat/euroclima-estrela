# Carteira preliminar de eixos sem interferência direta

**Status:** triagem de escopo; nenhuma classe abaixo comprova ausência de interferência.

## Decisão preliminar

O alteamento das UHEs existentes passa a ser uma análise de sensibilidade. A carteira principal deve investigar novos eixos, começando pelos que não têm conflito operacional comprovado com a cascata existente.

No conjunto atual, **E02 é o único candidato classificado como prioridade 1**: é independente na topologia extraída e sua restrição aparece como estudo, não como operação. Isso não significa que seja automaticamente viável; significa que é o melhor primeiro alvo para confirmar interferência, remanso, licenciamento, geologia e volume útil.

E01 e E04 são independentes na topologia, mas já aparecem limitados por usinas em operação. E10, E11 e E12 permanecem cenários de alta interferência, sobretudo pela cascata Monte Claro–Castro Alves–14 de Julho. E05 é inviável na altura admissível atualmente calculada.

## Critério

- `eixo_independente`: não possui eixo proposto a montante na tabela de topologia; não equivale a bacia sem usina existente.
- `candidato_prioritario_baixa_interferencia`: prioridade de verificação, não aprovação.
- `interferencia_operacional_a_confirmar`: a restrição registrada aponta usina em operação.
- `cascata_critica_alta_interferencia`: a cota admissível é governada por uma das usinas dominantes da cascata.

## Próxima verificação obrigatória

Para cada candidato, levantar NA, curva cota–área–volume, regras de operação e perfil de remanso da usina existente mais próxima. Só depois disso a classe poderá ser convertida em `sem_interferencia_confirmada`, `interferencia_gerenciável` ou `inviável`.

A tabela reproduzível está em `tabelas/prioridade_eixos_sem_interferencia.csv`.
