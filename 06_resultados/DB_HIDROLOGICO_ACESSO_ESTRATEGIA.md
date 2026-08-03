# Banco hidrológico DPM — acesso e estratégia de uso

**Data da verificação:** 2026-08-01  
**Projeto:** EUROCLIMA+ / AECID — sistema Estrela e alternativas de controle de cheias

## Resultado do teste de acesso

O endereço e a porta PostgreSQL foram alcançados pela rede privada. A autenticação foi
confirmada no banco `geodb_dpm_sas_vps`, com PostgreSQL 16.4. A verificação foi feita
com `default_transaction_read_only=on` e não houve criação, alteração ou exclusão de
objetos ou dados.

As credenciais não foram gravadas neste repositório, neste arquivo ou em scripts. Para
reproduzir a consulta, elas devem ser fornecidas apenas como variáveis de ambiente na
sessão de trabalho, conforme o script `07_python/36_inventaria_db_hidrologico.py`.

## Conteúdo relevante localizado

| Esquema/tabela | Conteúdo | Ordem de grandeza / observação |
|---|---|---|
| `hidro.vazoes_d_cb` | séries diárias de vazão (`codigo`, `data`, `valor`) | ~46,1 milhões de registros; índices por `codigo` e `codigo,data` |
| `hidro.chuvas_d_cb` | séries diárias de precipitação (`codigo`, `data`, `valor`) | ~156,1 milhões de registros; índices por `codigo` e `codigo,data` |
| `hidro.inventario` | estação, rio, município, coordenadas, área de drenagem e tipo de dado | 16.953 estações/itens |
| `info_dados_flu_ana.estacoes_flu_qrefsazonal_consistido` | estatísticas e metadados ANA, incluindo `QMLT`, `Q95`, `Qmin`, `Qmax` e período | 3.261 estações; útil para auditoria independente |
| `dados_xavier.grid_ponto` | pontos da grade espacial de clima | 71.007 pontos; grade de aproximadamente 0,1 grau |
| `dados_xavier.clima_diario_grade_1981` … `_2024` | precipitação (`pr`) e ETo (`eto`) diárias por ponto de grade | cerca de 25,9 milhões de linhas por ano; consultar somente `grid_id` e datas necessárias |
| `atlas_desastres.atlas_valores_corrigidos` | base de danos e prejuízos do Atlas de Desastres | ~76 mil registros; pode complementar a base municipal já consolidada |

## Estações de vazão prioritárias

As contagens e datas abaixo foram consultadas diretamente em `hidro.vazoes_d_cb`. A
coluna “máximo observado” é apenas um controle de consistência da série; não é, por
si só, uma vazão de projeto.

| Estação | Código | Área (km²) | Registros | Período disponível | Máximo (m³/s) |
|---|---:|---:|---:|---|---:|
| Castro Alves — barramento | 86305000 | 7.742,6 | 30.860 | 1931-01-01 a 2015-06-30 | 4.962,0 |
| Monte Claro — barramento | 86448000 | 12.113,7 | 30.860 | 1931-01-01 a 2015-06-30 | 7.753,1 |
| 14 de Julho — barramento | 86470800 | 12.757,8 | 30.860 | 1931-01-01 a 2015-06-30 | 12.358,0 |
| Muçum | 86510000 | 16.000,0 | 31.471 | 1940-01-01 a 2026-02-28 | 15.092,3 |
| Encantado | 86720000 | 19.100,0 | 30.804 | 1941-10-01 a 2026-01-31 | 14.003,0 |
| Passo do Coimbra — Forqueta | 86745000 | 791,0 | 25.021 | 1957-07-01 a 2025-12-31 | 1.292,3 |
| Santa Lúcia — Guaporé | 86580000 | 2.470,0 | 31.047 | 1940-01-01 a 2024-12-31 | 5.077,1 |
| Estrela | 86879300 | 22.472,0 | 1.156 | 2020-11-01 a 2023-12-31 | 17.260,9 |
| Lajeado | 86870000 | 19.700,0 | 61 | 1977-10-01 a 1977-11-30 | 1.982,0 |

As estações de Monte Claro, Castro Alves e 14 de Julho são especialmente importantes
para verificar a restrição de cascata e a resposta conjunta das usinas existentes. A
estação 86745000 é a primeira referência observada para a vazão lateral do Forqueta.
Muçum é a série longa mais adequada para a frequência preliminar; Estrela tem apenas
uma janela curta e não deve governar sozinha a análise estatística.

As estatísticas consistidas da ANA confirmam, entre outros, os períodos de 1940–2023
para Muçum, 1942–2022 para Encantado, 1958–2022 para Passo do Coimbra e 2022–2023
para Estrela. As diferenças entre o fim da série bruta e o período estatístico devem
ser mantidas explícitas no relatório.

## Chuva e grade espacial

`hidro.chuvas_d_cb` contém séries longas, mas várias estações próximas aos eixos têm
períodos que terminam antes dos eventos de 2023–2024. Exemplos verificados:

- 2851059 — UHE Monte Claro Balsa do Prata: 2009-03 a 2012-12;
- 2851060 — UHE Castro Alves RS-122: 2009-08 a 2012-12;
- 2851063 — PCH Linha Emília Jusante: 2012-04 a 2019-12;
- 2851037 — Cotiporã: 1951-03 a 1978-12.

Para reconstruir chuva espacial dos eventos recentes, a alternativa mais promissora é
`dados_xavier`. Foram identificados os pontos de grade mais próximos dos locais de
interesse:

| Local de referência | `grid_id` | Latitude | Longitude |
|---|---:|---:|---:|
| Muçum | 4700220 | -29,15 | -51,85 |
| Encantado | 4600220 | -29,25 | -51,85 |
| Estrela / análise | 4400219 | -29,45 | -51,95 |
| Forqueta FQ1 | 4400218 | -29,45 | -52,05 |
| Forqueta FQ2 | 4500218 | -29,35 | -52,05 |

O acesso deve ser feito por blocos anuais e poucos `grid_id`s, nunca por uma leitura
integral da grade. A partição de 2025 está sem linhas estimadas no catálogo e deve ser
tratada como indisponível até confirmação do administrador.

## Como isso entra no estudo

1. **C5 — auditoria independente das séries:** baixar apenas as séries dos códigos
   86510000, 86720000, 86879300 e 86745000 e comparar datas, máximos, falhas e volumes
   com os CSVs já usados pelo Claude.
2. **C6 — cascata existente:** usar 86305000, 86448000 e 86470800 para verificar se a
   resposta da cascata histórica é compatível com as restrições identificadas no
   perfil longitudinal. Isso não substitui regras operativas e curvas-chave das usinas.
3. **Forqueta:** usar 86745000 como série lateral observada, com defasagem física até
   a confluência e cenário de incerteza para a área não controlada pelos eixos FQ1/FQ2.
4. **Guaporé:** usar 86580000 como série longa para investigar a contribuição a montante
   e transpor a vazão para o GU1-PROPOSTO.
5. **Eventos 2023–2024:** combinar vazão observada com a chuva espacial `dados_xavier`
   somente para calibração/diagnóstico. Não misturar chuva de grade, chuva de posto e
   vazão observada sem registrar a escala temporal e o período de cobertura.
6. **Danos:** o Atlas disponível no mesmo banco pode ser usado para atualizar a base
   municipal, mas os registros devem continuar separados por evento, município,
   categoria e fonte antes de entrar na curva cota–dano.

## Próxima rodada recomendada

O próximo passo seguro é uma extração seletiva, sem alterar o banco:

- séries diárias completas das sete estações prioritárias;
- máximas anuais e volumes em janelas de 3, 5 e 7 dias;
- pareamento dos eventos de Muçum, Encantado e Estrela;
- série lateral do Forqueta e estimativa de defasagem;
- série longa do Guaporé (86580000) e transposição para GU1;
- chuva `pr` nos cinco `grid_id`s acima, apenas nos períodos dos eventos.

Os resultados devem alimentar a rodada C5/C6 e, depois, o HEC-RAS 1D. A frequência
continua sendo calculada com a estação longa de Muçum e a transposição para a seção de
análise; Estrela deve ser usada como controle de evento, não como amostra estatística
principal.
