# Triagem do GU1 — rio Guaporé + Antas

A série DPM do posto Santa Lúcia (86580000) tem **30,591 registros válidos**, de 1940-01-01 a 2024-04-30, com máximo de **5,077.1 m³/s**. O máximo de novembro de 2023 foi 896.9 m³/s.

A decomposição usa 19,440.0 km² na seção de análise, separando **2,486.7 km² do Guaporé** e **16,953.3 km² de vertente residual**. O GU1 controla preliminarmente 1,993.7 km² (80.2% do Guaporé).

## Melhor resultado por evento

| Evento | Antas | Forqueta | Altura GU1 | Defasagem | Pico natural | Pico com GU1 | Redução | Excesso sobre 4.000 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| novembro_2023_santa_lucia | E02+E04+E01+E05+E08+E12 | FQ2 | 30 m | 24 h | 16,558 | 5,449 | 67.1% | 1,449 |
| pico_historico_santa_lucia | E02+E04+E01+E05+E08+E12 | FQ2 | 120 m | 24 h | 15,603 | 5,551 | 64.4% | 1,551 |

No melhor cenário da rodada, **E02+E04+E01+E05+E08+E12 + FQ2**, GU1 com 30 m e regra seca produziu 5,449 m³/s em Estrela, ainda 1,449 m³/s acima do limiar preliminar. O resultado é uma triagem, pois o GU1 usa CAV sintética, pico diário transposto e não inclui remanso nem operação real das usinas Guaporé/Monte Cuco.
A matriz contém 384 combinações e nenhuma ficou abaixo de 4.000 m³/s. O valor de novembro de 2023 apresentado na tabela usa a defasagem que minimizou o pico nessa sensibilidade; com defasagem zero, o resultado a 120 m foi 6,438 m³/s.

A inclusão do GU1 é metodologicamente válida porque a sub-bacia foi retirada da vertente residual antes do roteamento. Não se somou o hidrograma do Guaporé ao hidrograma agregado original. A decomposição, entretanto, ainda deve ser recalibrada com séries subdiárias, transposição regional e pareamento com Muçum/Encantado/Estrela.

Arquivos: `tabelas/roteamento_guapore_antas.csv`, `tabelas/eixo_guapore_proposto.csv` e `01_dados/dpm_db/86580000_vazao.csv`.
