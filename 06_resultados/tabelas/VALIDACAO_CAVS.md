# Validação das CAVs consolidadas

A verificação testa cota crescente, área crescente, volume crescente e a relação de ordem de grandeza `dV/dc ≈ A`.
A última relação não é um teste de precisão batimétrica; ela identifica inconsistências de unidade, sinal ou interpolação.

| categoria | nome | n_pontos | cota_min_m | cota_max_m | area_monotona | volume_monotono | cota_regular | erro_rel_mediano_dv_area | erro_rel_maximo_dv_area |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Eixo novo sem reservatório existente | E01 | 111 | 82.5 | 192.5 | True | True | True | 0.002838 | 0.03129 |
| Eixo novo sem reservatório existente | E02 | 111 | 303 | 413 | True | True | True | 0.002949 | 0.0423 |
| Eixo novo sem reservatório existente | E03 | 111 | 159.5 | 269.5 | True | True | True | 0.005721 | 0.05533 |
| Eixo novo sem reservatório existente | E04 | 111 | 249 | 359 | True | True | True | 0.00225 | 0.02215 |
| Eixo novo sem reservatório existente | E05 | 111 | 177 | 287 | True | True | True | 0.005011 | 0.1991 |
| Eixo novo sem reservatório existente | E06 | 111 | 159.5 | 269.5 | True | True | True | 0.004413 | 0.1546 |
| Eixo novo sem reservatório existente | E07 | 111 | 159.5 | 269.5 | True | True | True | 0.004122 | 0.1436 |
| Eixo novo sem reservatório existente | E08 | 111 | 158 | 268 | True | True | True | 0.002842 | 0.08785 |
| Eixo novo sem reservatório existente | E09 | 111 | 116 | 226 | True | True | True | 0.001292 | 0.05198 |
| Eixo novo sem reservatório existente | E10 | 111 | 81.5 | 191.5 | True | True | True | 0.002078 | 0.3176 |
| Eixo novo sem reservatório existente | E11 | 111 | 67.5 | 177.5 | True | True | True | 0.001685 | 0.08115 |
| Eixo novo sem reservatório existente | E12 | 111 | 57 | 167 | True | True | True | 0.00155 | 0.1467 |
| UHE existente | 14 de Julho | 1107 | 62.37 | 110 | True | True | True | 5.675e-05 | 0.6006 |
| UHE existente | Castro Alves | 1265 | 187.1 | 246.4 | True | True | True | 4.629e-05 | 0.773 |
| UHE existente | Monte Claro | 1328 | 116.9 | 157.2 | True | True | True | 2.654e-05 | 0.3209 |

As curvas que falharem monotonicidade não devem ser usadas para interpolação operacional.