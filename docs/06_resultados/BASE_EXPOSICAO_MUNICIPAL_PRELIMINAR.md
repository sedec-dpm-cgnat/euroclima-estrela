# Base de exposição municipal preliminar

Produto de integração entre `manchas_por_municipio.csv` e `atlas_danos_municipios.csv`.

- Municípios na tabela: **19**.
- A área e a profundidade são saídas preliminares HAND/geométricas, não resultados HEC-RAS 1D.
- Os valores do Atlas são perdas declaradas por evento e município; não são dano evitável diretamente atribuível a uma barragem.
- População, domicílios, setores censitários, tipologias construtivas e custo de reposição ainda não foram integrados.
- O campo `dano_atlas_mai24_por_km2_inund_sem_hand` é apenas indicador descritivo e não deve ser usado como função de dano.

## Maiores áreas preliminares com a medida de referência

| Município | Área inundada com HAND (km²) | Profundidade média com HAND (m) | Dano Atlas mai/2024 (R$) |
|---|---:|---:|---:|
| Venâncio Aires | 55,01 | 1,77 | 0,00 |
| Taquari | 41,97 | 4,46 | 0,00 |
| Cruzeiro do Sul | 29,19 | 4,24 | 0,00 |
| Estrela | 26,00 | 5,53 | 0,00 |
| Bom Retiro do Sul | 19,61 | 4,93 | 0,00 |
| Arroio do Meio | 17,41 | 5,40 | 0,00 |
| Roca Sales | 12,20 | 6,61 | 0,00 |
| Lajeado | 10,88 | 8,75 | 0,00 |
| Marques de Souza | 9,06 | 4,39 | 0,00 |
| Muçum | 8,31 | 7,17 | 0,00 |

## Próximo passo

Cruzar a mancha HEC-RAS 1D com setores censitários IBGE 2022 e, quando disponível, edificações/cadastro municipal. A função de dano deve aplicar profundidade e duração por classe de ativo, usando os valores do Atlas apenas para conferir ordem de grandeza e cobertura.
