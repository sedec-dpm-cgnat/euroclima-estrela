# CAV oficial do SNIRH × triagem do projeto

## Resultado executivo

O registro do SNIRH/ANA forneceu curvas cota–área–volume para as três UHEs
principais da cascata do rio das Antas. A leitura oficial muda a avaliação da
alternativa de deplecionamento: o MDE reproduz a ordem de grandeza apenas em
parte e não deve ser usado para substituir a batimetria onde a CAV oficial já
existe.

| Usina | CAV atualizada | NA normal SL (m) | Volume normal (hm³) | Projeto/MDE (m) | Diferença MDE − normal (m) | Espera oficial a 10 m (hm³) | Espera sintética a 10 m (hm³) |
|---|---|---:|---:|---:|---:|---:|---:|
| 14 de Julho | 2020-10-01 | 104,00 | 74,84 | 104,5 | +0,5 | 46,27 | 81,7 |
| Castro Alves | dezembro de 2016 | 240,00 | 105,05 | 236,0 | −4,0 | 46,20 | 38,7 |
| Monte Claro | 2020-09-01 | 148,00 | 16,94 | 132,5 | −15,5 | 12,50 | 2,2 |

O desvio de 15,5 m em Monte Claro é o principal alerta. Ele pode resultar de
diferença de datum, ponto de ancoragem, representação da superfície da água
ou erro de identificação da usina no MDE; não deve ser corrigido por ajuste
arbitrário. O próximo passo é confirmar a referência vertical e o ponto de
controle com a CERAN/ANA.

## Volume oficial de espera por deplecionamento

Valores calculados na curva em Sistema Local, usando o nível normal da ficha
técnica e a diferença entre o volume normal e o volume na cota rebaixada.

| Depleção | 14 de Julho | Castro Alves | Monte Claro | Total |
|---:|---:|---:|---:|---:|
| 1 m | 5,57 hm³ | 5,26 hm³ | 1,59 hm³ | **12,41 hm³** |
| 3 m | 16,17 hm³ | 15,44 hm³ | 4,59 hm³ | **36,20 hm³** |
| 5 m | 25,94 hm³ | 25,03 hm³ | 7,28 hm³ | **58,25 hm³** |
| 10 m | 46,27 hm³ | 46,20 hm³ | 12,50 hm³ | **104,97 hm³** |
| 15 m | 59,95 hm³ | 63,47 hm³ | 15,62 hm³ | **139,04 hm³** |

Esses volumes são capacidade geométrica de armazenamento temporariamente
liberável, não volume automaticamente disponível para controle de cheias. A
decisão operacional depende de previsão, antecedência, vazões afluentes,
restrições de geração, segurança de barragem, reenchimento e remanso conjunto.

## Arquivos de rastreabilidade

- Curvas consolidadas: `01_dados/cav_snirh/curvas/cav_snirh_consolidada.csv`;
- Fichas técnicas: `01_dados/cav_snirh/cav_snirh_ficha_tecnica.csv`;
- Comparação completa: `06_resultados/tabelas/comparacao_cav_snirh_projeto.csv`;
- Deplecionamento completo: `06_resultados/tabelas/volume_deplecionamento_cav_snirh.csv`;
- Importação: `07_python/24_importa_cav_snirh.py`;
- Cálculo: `07_python/25_compara_cav_snirh_e_deplecionamento.py`.
