# STATUS ATUAL — Projeto EUROCLIMA+ / AECID

**Atualizado em:** 07/09/2026
**Diretório de trabalho:** `C:/Users/cassi/OneDrive/Documents/SEDEC/PROJETO_EUROCLIMA/05_MODELAGEM`

## Retomada — 07/09/2026

O site Quarto foi publicado e está acessível em
`https://sedec-dpm-cgnat.github.io/euroclima-estrela-site/`. O repositório técnico
`euroclima-estrela` continua privado e o conteúdo publicado é a saída estática
gerada em `docs/`.

O próximo passo técnico é a montagem do HEC-RAS 1D, começando pelo HEC-00 sem
obras e depois pelo HEC-01 (E02 + E04). A auditoria registrada em
`06_resultados/VALIDACAO/AUDITORIA_CONTORNOS_HECRAS.md` encontrou 256,7 km² a
explicar no fechamento preliminar das áreas e confirmou que o C01 disponível
continua sendo uma série de triagem, não uma condição de contorno calibrada.
Ainda faltam séries efluentes por nó, seções topobatimétricas, cadastro de
pontes, dados de jusante e a curva cota–dano.

## Decisões metodológicas fixadas

1. O alteamento das UHEs existentes fica em segundo plano, apenas como
   sensibilidade de custo, segurança e área adicional.
2. A modelagem hidráulica adotada é **HEC-RAS 1D**. Não desenvolver HEC-RAS
   2D nesta linha de trabalho. O FloodAdapt/SFINCS poderá ser exigido no
   contrato como produto complementar, mas deverá ser confrontado com os
   resultados do HEC-RAS 1D.
3. CAV oficial deve prevalecer sempre que existir.
4. Para eixos novos sem reservatório atual, a CAV derivada do MDE natural é
   aceitável para triagem, desde que classificada como classe B e substituída
   por topografia/engenharia na fase executiva.
5. PCHIP monotônica é a curva de interpolação operacional. Polinômios são
   apenas apoio documental e sensibilidade; não extrapolar.
6. A documentação pública será um site Quarto versionado no GitHub, seguindo
   o modelo do [Minicurso TRIGRS](https://sedec-dpm-cgnat.github.io/tutorial-trigrs/):
   capítulos em `.qmd`, navegação lateral, referências e histórico completo
   de commits. O template deverá manter `DPM-Circular.png` e
   `logo_marca_sedec.png`; a logo da UFF não será usada.

## O que está concluído

- Revisão longitudinal das alturas admissíveis e das restrições de remanso;
- priorização preliminar dos eixos, com E02 e E04 como candidatos principais;
- CAV oficial SNIRH/ANA para 14 de Julho, Castro Alves e Monte Claro;
- volume oficial de deplecionamento das três UHEs;
- CAV derivada do MDE natural para os 12 eixos novos;
- interpolação PCHIP em passos de 1 m;
- base única com 15 curvas e 5.032 pontos;
- validação de monotonicidade de cota, área e volume;
- SINV v2 com vazão específica calibrada e CAV interpolada;
- roteiro e insumos preliminares do HEC-RAS 1D, incluindo eixo, 102 seções,
  4 travessias, 6 confluências e condições de contorno;
- HAND preliminar com manchas, perfil de linha d'água e tabelas por município;
- extração preliminar do Atlas de Desastres para os municípios do corredor;
- organização da base GIS em GeoPackage, Shapefiles e KMZ de entrega.
- inventário da rede de eixos e dos cenários de cascatas com comportas, a partir
  do `EUROCLIMA-rev.kmz`.
- roteamento preliminar conjunto dos cenários C01–C05, com conservação de massa
  e registro de saturação/galgamento; a rodada antiga permanece como histórico.
- rodada calibrada C1–C4 executada pelo Claude, com séries ANA, frequência de
  vazões em Muçum, evento de referência e roteamento das alternativas.
- hidrograma calibrado sem barragem versus ALT-J em
  `06_resultados/figuras/16_hidrograma_calibrado_ALTJ.png`.
- base municipal preliminar que combina HAND/manchas e Atlas em
  `06_resultados/tabelas/base_exposicao_municipal_preliminar.csv`, com campos
  IBGE e custos unitários explicitamente pendentes.
- dois eixos de retenção no Forqueta, FQ1 e FQ2, com KMZ, CSV, CAV isolada e
  mapa específico; FQ1 controla 82,7% da área BHO do tributário.
- definição do padrão de documentação pública no GitHub/Quarto.

## Resultados que podem entrar como triagem

- CAV oficial das três UHEs: aproximadamente 12 hm³ a 1 m, 36 hm³ a 3 m,
  58 hm³ a 5 m, 105 hm³ a 10 m e 139 hm³ a 15 m de deplecionamento conjunto;
- E02: cerca de 1.377 hm³ acumulados no teto geométrico de 120 m;
- E04: cerca de 2.211 hm³ acumulados no teto geométrico de 120 m;
- E12: cerca de 977 hm³, limitado pelo remanso de 14 de Julho;
- E08: cerca de 620 hm³, limitado pelo remanso de Castro Alves;
- E10: retirar da carteira principal até revisão, pois o balanço energético
  preliminar ficou negativo na faixa viável.
- vazão específica regional preliminar calibrada: 0,0269 m³/s/km²; usar os
  arquivos SINV v2 e não os ICB da v1;
- a interferência com usinas existentes deve ser reportada em duas dimensões:
  altura de veto por cota mínima operacional e altura de início da perda de
  energia na usina de montante;
- a discrepância de 15,5 m entre a CAV oficial e a cota do MDE em Monte Claro
  continua sem solução e bloqueia a confiança na restrição de E09.

Os valores dos eixos novos são geométricos e preliminares. Não representam
volume de espera operacional nem comprovam redução de danos.

## Próximas entregas para fechar o relatório técnico

### Rodada calibrada C1–C4 — 01/08/2026

Os arquivos `06_resultados/CLAUDE/CLAUDE_RELATORIO_C1_C2_C3.md` e os CSVs
`claude_c1_*` a `claude_c4_*` passam a ser a referência hidrológica de triagem,
substituindo o hidrograma sintético de 18.000 m³/s como resultado principal.
Os principais números são:

- pico de referência no ponto de análise: **16.300 m³/s**;
- lâmina efetiva do evento: **227 mm**;
- vazão de base: **926 m³/s**;
- série de Muçum com aproximadamente **86,2 anos** e máximo observado de
  **15.092 m³/s**;
- período de retorno preliminar do evento ajustado por L-momentos: **333 anos**;
- setembro de 2023 teve o maior pico observado; maio de 2024 teve maior volume,
  portanto pico e volume não devem ser tratados como o mesmo evento de projeto.

Na carteira calibrada, ALT-A (E02+E04) reduz o pico para 9.272 m³/s (43,1%),
ALT-D para 8.411 m³/s (48,4%), ALT-E para 6.328 m³/s (61,2%) e ALT-J, com a
carteira completa e operação de barragem seca, para 6.213 m³/s (61,9%). E12
isolado praticamente não reduz o pico porque satura antes da passagem da onda.
Nenhuma das 30 combinações testadas alcançou 4.000 m³/s. Esses resultados ainda
são de roteamento de triagem: faltam defasagem dos tributários, remanso,
HEC-RAS 1D, regra operativa validada e teste com a área-alvo de 19.440 km².

### 1. Fechamento hidrológico e hidráulico

- usar o HAND já produzido como triagem geomorfológica e controle de coerência,
  não como substituto do modelo hidráulico;
- calibrar por sensibilidade o limiar de drenagem, os valores de Manning e os
  limiares HAND, reportando sensibilidade/especificidade contra a mancha de
  maio de 2024;
- completar a transposição das séries ANA para o ponto de análise e revisar a
  calibração com as áreas de 19.440 km² e 22.472 km²;
- confirmar o datum vertical e a discrepância da cota de Monte Claro;
- revisar no QGIS os insumos preliminares já gerados para o HEC-RAS 1D;
- obter cota de tabuleiro e vãos das pontes, seções topobatimétricas, curva-chave
  em Estrela e séries ANA;
- montar o HEC-RAS 1D com seções, pontes, diques, confluências e condições de
  contorno;
- testar a sensibilidade da condição de jusante, pois o trecho final tem
  declividade estimada de apenas 6,3×10⁻⁵ m/m e pode ser governado por remanso;
- calibrar contra níveis, curva-chave e mancha de maio de 2024;
- simular remanso e operação conjunta para E02, E04 e alternativas;
- incorporar a defasagem dos tributários e a condição de jusante ao roteamento
  em rede para barragens com comportas, incluindo C01–C05;

### 2. Curva cota–dano

- consolidar Atlas de Desastres, municípios, setores censitários IBGE,
  população/domicílios e tipologias construtivas;
- usar `base_exposicao_municipal_preliminar.csv` como ponte auditável até a
  integração dos setores censitários e agregados do Censo 2022;
- usar SINAPI/CUB-RS e bases territoriais como aproximação de reposição;
- cruzar profundidade/duração do HEC-RAS 1D com exposição;
- gerar dano por cenário e EAD com faixas de incerteza; a economia só deve ser
  recalculada depois de fixar o hidrograma calibrado, a curva cota–dano e a
  resposta hidráulica do HEC-RAS 1D.

### 3. Relatório e TR

- atualizar tabelas e figuras com os resultados v2;
- separar números oficiais, derivados do MDE e parâmetros não calibrados;
- redigir alternativas híbridas: eixos novos, operação de reservatórios,
  alerta, ordenamento territorial, retenções distribuídas e medidas urbanas;
- fechar recomendações, limitações, dados de campo e especificações do TR.
- incluir a figura de divisão de quedas com todas as alternativas, outra figura
  destacando a alternativa recomendada/selecionada e a bibliografia completa;
- seguir o roteiro de figuras e referências em
  `RELATORIO_FIGURAS_REFERENCIAS.md`.

### 4. Site Quarto no GitHub

- estrutura criada e renderizada: `index.qmd`, capítulos numerados, `_quarto.yml`,
  `logos/`, `referencias.qmd` e saída `docs/`;
- decisões, métodos, dados, resultados e limitações documentados com links para os artefatos;
- logos DPM e Proteção e Defesa Civil preservadas; logo da UFF excluída;
- publicação concluída em `https://sedec-dpm-cgnat.github.io/euroclima-estrela-site/`;
  a próxima publicação ocorrerá somente após a atualização técnica do HEC-RAS,
  danos e custo-benefício.

### 5. Novas entregas incorporadas nesta versão

- livro Quarto renderizado em `docs/index.html`, seguindo o template do Minicurso TRIGRS;
- hidrogramas sem barragem versus C01–C05 e detalhe de C02 em `06_resultados/figuras/14_hidrogramas_natural_vs_cascatas.png` e `15_hidrograma_natural_vs_C02.png`;
- desenho comparativo da divisão de quedas por alternativa em `VALIDACAO/DIVISAO_QUEDAS_ALTERNATIVAS.png`;
- matriz explícita dos eixos de cada alternativa e cenário em `VALIDACAO/MATRIZ_ALTERNATIVAS_EIXOS.png`;
- validação isolada da ancoragem BHO/D8 em `VALIDACAO/validacao_ancoragem_eixos.csv`;
- quatro pontos exploratórios derivados do perfil, incluindo `MC2-PROPOSTO`, com CSV, KML e KMZ em `06_resultados/tabelas/` e `06_resultados/GIS/`;
- plano de trabalho paralelo em `PLANO_TRABALHO_PARALLELO_CODEX_CLAUDE.md`.

O arquivo separado `EIXO-MONTECLARO2.kmz` foi auditado e integrado aos produtos de conferência.
Ele contém uma linha sobre o canal principal; o ponto médio está na estaca aproximada 294,48 km,
a cerca de 12 m do talvegue, entre Monte Claro e 14 de Julho. O `EUROCLIMA-rev.kmz` continua
com 12 linhas de rótulo genérico `EIXO`; por isso, MC2 é um candidato adicional e ainda depende
de CAV, remanso, energia e interferência antes de receber código definitivo no pipeline.

## Divisão de trabalho com Claude Code

### Claude Code deve fazer

- auditar e consolidar os arquivos SINV v2;
- selecionar a carteira preliminar sem E10;
- revisar E02/E04/E01/E05 com as alturas admissíveis e restrições longitudinais;
- transformar o roteiro `CLAUDE_ROTEIRO_HECRAS_1D.md` em lista de insumos,
  seções, estruturas e condições de contorno;
- preparar tabelas e textos técnicos para a seção de alternativas;
- não iniciar HEC-RAS 2D e não substituir a PCHIP por polinômio.

### Codex deve fazer

- montar a base territorial de danos e a curva cota–dano;
- estruturar entradas e saídas do HEC-RAS 1D;
- integrar CAV, SINV, danos, custo e benefício em tabelas comparáveis;
- revisar consistência do relatório, figuras, mapas, fontes e limitações;
- manter a base única e a rastreabilidade dos resultados.

### Próxima rodada proposta pelo Claude

O arquivo `06_resultados/CLAUDE/CLAUDE_PROPOSTA_DIVISAO_PROXIMA_RODADA.md` fixa o caminho
crítico: Claude deve executar o roteamento das alternativas (C1) e consolidar as séries ANA
(C2), enquanto o Codex corrige a ancoragem, integra figuras, base territorial e relatório.
Ainda não se deve consolidar uma recomendação final antes do C1, porque o volume de espera
nominal não equivale automaticamente a redução de pico em Estrela.

### Auditoria X1/X2 da ancoragem

Foi criada uma rodada isolada com critério de interseção da geometria do eixo com a BHO, sem
substituir `01_dados/cav/eixos_todos.csv`. Os 12 eixos intersectaram a BHO e apresentaram
razão `área_D8/área_BHO` entre **0,988 e 1,001**. Houve pequenas mudanças de ponto e cota
em alguns eixos, especialmente E01 (+1,6 km²; −1,0 m) e E05 (−1,5 m), que devem ser
incorporadas ao pipeline canônico somente junto com a próxima rodada de CAV/SINV.

## Arquivos centrais

- `06_resultados/tabelas/cav_base_unica.csv`;
- `06_resultados/tabelas/catalogo_cavs.csv`;
- `06_resultados/tabelas/VALIDACAO_CAVS.md`;
- `06_resultados/CLAUDE/claude_sinv_energetico_v2.csv`;
- `06_resultados/CLAUDE/claude_sinv_sintese_eixos_v2.csv`;
- `06_resultados/CLAUDE/claude_sinv_alternativas_v2.csv`;
- `06_resultados/CLAUDE/CLAUDE_ROTEIRO_HECRAS_1D.md`;
- `06_resultados/GIS/eixos_forqueta_propostos.kmz`;
- `06_resultados/tabelas/eixos_forqueta_propostos.csv`;
- `01_dados/cav_forqueta/cav_todos.csv`;
- `06_resultados/CASCATAS_COMPORTAS_METODOLOGIA.md`;
- `06_resultados/CASCATAS_COMPORTAS_TRIAGEM.md`;
- `06_resultados/CLAUDE/CLAUDE_ROTEIRO_HECRAS_1D.md`;
- `06_resultados/CLAUDE/claude_hecras_eixo.gpkg`;
- `06_resultados/CLAUDE/claude_hecras_secoes.csv`;
- `06_resultados/CLAUDE/claude_hecras_travessias.csv`;
- `06_resultados/CLAUDE/claude_hecras_confluencias.csv`;
- `06_resultados/CLAUDE/claude_hecras_contornos.csv`;
- `06_resultados/tabelas/rede_imediata_cascatas_comportas.csv`;
- `06_resultados/tabelas/cascatas_candidatas_comportas.csv`;
- `06_resultados/tabelas/roteamento_cascata_comportas_triagem.csv`;
- `06_resultados/tabelas/roteamento_cascata_comportas_detalhe.csv`;
- `HANDOFF.md`;
- `PLANO_DE_ACAO.md`.

### Acesso ao banco hidrológico DPM

O acesso read-only ao PostgreSQL privado foi validado em 2026-08-01. O inventário seletivo
está em `06_resultados/DB_HIDROLOGICO_ACESSO_ESTRATEGIA.md` e em
`06_resultados/tabelas/catalogo_db_hidrologico.csv`; o script reprodutível é
`07_python/36_inventaria_db_hidrologico.py`. As credenciais não foram persistidas.

O banco contém séries diárias de Muçum, Encantado, Estrela, Forqueta e dos barramentos
de Castro Alves, Monte Claro e 14 de Julho. Isso abre a rodada C5/C6 para auditar a
calibração, verificar a cascata existente e tratar o Forqueta como afluência lateral
observada. A extração integral das tabelas de chuva e grade não deve ser feita: usar
consultas por código, `grid_id` e janela temporal.

### Atualização da rodada Forqueta — 01/08/2026

O Claude concluiu a validação de FQ1/FQ2 em
`06_resultados/CLAUDE/CLAUDE_NOTA_FORQUETA.md`. A série observada do posto 86745000
indicou defasagem central de 0 dia em 13 eventos e pico transposto de 3.837 m³/s.
Com exutório em Estrela, ALT-J reduziu 58,6% do pico; ALT-J+FQ1 reduziu 59,3% e
ALT-J+FQ2, 59,7%. FQ1 e FQ2 são mutuamente exclusivos por interferência de cota e
ficam fora da alternativa de referência.

A lacuna de novembro de 2023 no Passo do Coimbra permanece crítica, pois coincide com
o maior pico observado em Estrela. O próximo dado prioritário é a reativação de curva-chave
e observação subdiária em Barra do Fão. O Guaporé, com contribuição de ordem semelhante e
a montante do ponto de análise, foi incluído como nova frente exploratória do Codex. A
estação Santa Lúcia (86580000) tem 31.047 registros de 1940 a 2024, área ANA de 2.470 km²
e máximo de 5.077,1 m³/s. O GU1-PROPOSTO apresentou área D8 de 1.993,4 km², razão D8/BHO
de 0,9999 e cota MDE de 227,5 m; permanece apenas como triagem.

### Busca ampliada de carteiras — 01/08/2026

O Codex executou a busca de 32 adições à ALT-J com E03, E06, E07, E09 e E11, além do
envelope de 64 combinações incluindo E10 e de 192 combinações com Forqueta. Nenhuma
atingiu 4.000 m³/s em Estrela. O melhor resultado permanece ALT-J + FQ2, sob barragem
seca, com 6.802 m³/s. O próximo teste estrutural é o GU1, mas sua sub-bacia deve ser
desagregada do hidrograma sintético do Antas antes do roteamento para evitar dupla
contagem.

### Primeira rodada numérica do GU1

A desagregação foi executada. No máximo histórico do Santa Lúcia, ALT-J + GU1 a 100 m
produziu 4.532 m³/s em Estrela; no evento de novembro de 2023, com defasagem zero e
120 m apenas como envelope geométrico, produziu 4.763 m³/s. Foram testadas 384
combinações e nenhuma ficou abaixo de 4.000 m³/s. O GU1 é agora a prioridade para
HEC-RAS 1D, com validação pendente de altura admissível, energia, operação e remanso.

### Matriz HEC-RAS 1D explicitada — 02/08/2026

Foi criada a matriz de simulação que separa o caso sem obra, os casos estruturais
comparáveis e as sensibilidades laterais:

- **HEC-00 / REF:** situação atual, para calibrar maio de 2024;
- **HEC-01 / ALT-A / C01:** E02 + E04, primeiro caso com obra;
- **HEC-02 / ALT-D / C03:** E02 + E04 + E08, ganho incremental de E08;
- **HEC-03 / ALT-E / C02:** E02 + E04 + E12, cobertura ampliada;
- **HEC-04:** ALT-J + GU1, extensão estrutural prioritária após a calibração;
- **HEC-05:** ALT-J + FQ2, sensibilidade lateral no trecho de Estrela;
- **HEC-06:** C04, C05, FQ1 e combinações selecionadas, somente como sensibilidade.

O primeiro caso com obra, portanto, é **E02 + E04**. Nenhum arranjo está selecionado
para implantação antes do HEC-RAS 1D, da curva cota–dano e da análise de custo,
energia, segurança e remanso. O diagrama está em
`06_resultados/VALIDACAO/DIAGRAMA_TOPOLOGICO_ALTERNATIVAS_HECRAS.svg`.

### Avaliação do gerador Kirsch–Nowak — 07/09/2026

Foi avaliado o gerador estocástico localizado em
`Ajumar/Kirsch-Nowak_Streamflow_Generator-master`. Ele é adequado como **C7 —
ensemble probabilístico** para séries diárias multissítio correlacionadas, frequência de
excedência, coincidência de picos, volume, duração, energia e danos. Não substitui C3/C4
nem o HEC-RAS 1D: assume estacionariedade, não gera escala subdiária e não representa
diretamente comportas, remanso ou pontes.

A avaliação está em `06_resultados/AVALIACAO_KIRSCH_NOWAK_EUROCLIMA.md`. O próximo passo
é auditar as séries ANA/DPM e preparar componentes não aninhados de Antas, Forqueta e
Guaporé, sem dupla contagem. Só depois da validação estatística o ensemble deve ser usado
para atualizar custo-benefício ou selecionar alternativa.

### Relatório consolidado e manchas HAND — 07/09/2026

Foi criado `09-relatorio-consolidado.qmd`, reunindo o histórico da análise, a leitura
imparcial dos resultados, a comparação preliminar de manchas HAND sem novas barragens e
com ALT-J, a matriz HEC-00–HEC-06, a hipótese de diques/soluções híbridas e o plano de
continuidade. A triagem espacial resultou em 288,4 km² sem novas barragens e 245,4 km²
com ALT-J, redução de 43,0 km² (14,9%) no corredor; em Estrela, 30,77 para 24,60 km²
(20,1%). Esses números são HAND, não manchas hidráulicas finais.

O relatório foi renderizado e a saída estática foi publicada no site público. As figuras
estão em `06_resultados/VALIDACAO/MAPA_HAND_SEM_VS_ALTJ.png`,
`MAPA_HAND_DIFERENCA_ALTJ.png` e `REDUCAO_MANCHA_HAND_ALTJ_MUNICIPIOS.png`.
