# Triagem combinada Antas + Forqueta

Rodada preliminar com hidrogramas próprios do Antas e do Forqueta, defasagem medida de 0 h e exutório em Estrela (22.472 km²). O ponto de 19.440 km² permanece a montante do Forqueta.

- Pico natural sintético em Estrela: **16,903 m³/s**; máximo observado em 19/11/2023: **17,261 m³/s**.
- Limiar preliminar de comparação: **4,000 m³/s**; não é limite legal nem substitui a curva cota-dano calibrada.
- Altura de triagem adotada: **30 m** para FQ1 e FQ2; os dois eixos são mutuamente exclusivos por interferência de cota.

## Melhores combinações fisicamente admissíveis

| Regra | Alternativa Antas | Forqueta | Pico em Estrela (m³/s) | Redução (%) | Acima de 4.000 (m³/s) | Volume total (hm³) |
|---|---|---|---:|---:|---:|---:|
| seca | ALT-J | FQ2 | 6,802 | 59.8 | 2,802 | 2,751 |
| comportas | ALT-E | FQ1 | 7,887 | 53.3 | 3,887 | 2,219 |
| convencional | ALT-D | SEM_FORQUETA | 15,799 | 6.5 | 11,799 | 468 |

## Leitura preliminar

A menor vazão entre as combinações fisicamente admissíveis foi **6,802 m³/s**, em **ALT-J + FQ2**, com regra **seca**. Esse valor permanece **2,802 m³/s acima** do limiar preliminar de 4.000 m³/s e corresponde a 60.6% de redução em relação ao pico observado de 2023.

Portanto, nesta parametrização não há combinação que leve o pico em Estrela a uma magnitude próxima da não ocorrência de cheia. O Forqueta melhora a proteção de Estrela, mas o ganho marginal é pequeno diante do controle já obtido pela carteira ALT-J. A conclusão é de triagem: deve ser reavaliada no HEC-RAS 1D com remanso, operação e curva cota-dano.

Os resultados completos estão em `tabelas/roteamento_combinado_antas_forqueta.csv`; as séries para os gráficos estão em `tabelas/hidrogramas_combinados_antas_forqueta.csv`.
