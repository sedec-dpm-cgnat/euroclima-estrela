# Plano de trabalho paralelo — Codex e Claude

## Objetivo comum

Fechar a nota técnica navegável em Quarto, com base hidrológica, HAND, alternativas
energéticas e de cheias, novos pontos exploratórios, HEC-RAS 1D e análise custo–benefício
auditável. Nenhum ponto exploratório ou alternativa é recomendação de obra antes da
validação hidráulica, ambiental, geotécnica e econômica.

## Estado da rodada de 01/08/2026

Claude concluiu C1–C4. A rodada calibrada, registrada em
`06_resultados/CLAUDE/CLAUDE_RELATORIO_C1_C2_C3.md`, passa a ser a referência de
triagem para os capítulos hidrológicos: pico de 16.300 m³/s, lâmina de 227 mm,
vazão de base de 926 m³/s e roteamento de 30 combinações. ALT-A, ALT-D, ALT-E e
ALT-J reduziram o pico em 43,1%, 48,4%, 61,2% e 61,9%, respectivamente; nenhuma
combinação atingiu 4.000 m³/s.

O Codex já integrou os resultados aos capítulos `03-alternativas.qmd`,
`04-hidrologia-hand.qmd`, `05-cascatas-comportas.qmd`, `07-danos-economia.qmd`,
`08-conclusoes.qmd` e `90-limitacoes.qmd`, atualizou `HANDOFF.md` e
`STATUS_ATUAL_PROJETO.md`, gerou a figura calibrada ALT-J e confirmou a
renderização de `docs/index.html`.

## Codex — frente de relatório, figuras e geodados

- manter os capítulos `.qmd` e o template visual do relatório;
- incorporar hidrogramas sem barragem e com cascatas;
- documentar HAND, continuidade de massa, CAVs e limitações;
- gerar/atualizar figuras de divisão de quedas para cada alternativa;
- gerar e revisar o arquivo `eixos_exploratorios_propostos.kmz`;
- documentar as coordenadas do `EIXO-MONTECLARO2.kmz`, preservando a geometria original no KMZ consolidado;
- detalhar no relatório as fórmulas energéticas e de custo–benefício;
- renderizar e revisar o site Quarto.

## Claude — frente de validação técnica independente

- conferir a geometria separada `Documentos EUROCLIMA+/Espanha/kmz/EIXO-MONTECLARO2.kmz` e usá-la como KMZ extra, sem substituir `EUROCLIMA-rev.kmz`;
- rodar o pipeline de eixos com a base `EUROCLIMA-rev.kmz` mais o KMZ extra e atribuir um código lógico ao candidato, sem promovê-lo automaticamente a E13;
- auditar as coordenadas, cotas e áreas contribuintes dos novos eixos;
- validar o perfil longitudinal e os máximos locais de queda com ANADEM/MDE e BHO;
- recalcular CAVs e volumes dos novos pontos com a mesma metodologia PCHIP;
- atualizar a matriz de interferência com Monte Claro, Castro Alves e 14 de Julho;
- revisar `q = 0,0269 m³/s/km²`, hidrogramas, sincronização dos tributários e cenários de comportas;
- preparar os casos HEC-RAS 1D correspondentes aos novos pontos, sem introduzir HEC-RAS 2D;
- revisar energia firme, perda de queda, ICB e sensibilidade econômica.

### Próxima divisão após C1–C4

Claude deve concentrar a próxima rodada em:

- C5: planos e séries de contorno para HEC-RAS 1D usando os efluentes calibrados;
- C6: defasagem do Forqueta e dos demais tributários, substituindo a
  decomposição puramente proporcional por área;
- reprocessamento do SINV com os parâmetros calibrados;
- conciliação das áreas ANA–D8 de Muçum e confirmação da transposição para o
  ponto de análise.

O Codex continuará com:

- X6: base territorial de exposição, integração Atlas–manchas–municípios e
  preparação da curva cota–dano;
- X7: custo–benefício auditável depois da entrada de C5/C6 e da exposição;
- revisão final das figuras, alternativas, referências e limitações.

Entrega parcial de X6 já disponível: `07_python/34_consolida_exposicao_municipal.py`,
`06_resultados/tabelas/base_exposicao_municipal_preliminar.csv` e
`06_resultados/BASE_EXPOSICAO_MUNICIPAL_PRELIMINAR.md`. A integração de setores
IBGE 2022, população/domicílios, tipologias e custos de reposição ainda depende
das bases territoriais correspondentes.

Para a nova frente de tributário, a divisão detalhada está em
`PLANO_FORQUETA_CODEX_CLAUDE.md`. A rodada do Claude foi concluída em 01/08/2026:
FQ1 e FQ2 ficaram fora da alternativa de referência, são mutuamente exclusivos e
dependem de resolver a lacuna de novembro de 2023 no Forqueta. O novo eixo exploratório
prioritário passa a ser o Guaporé, a montante do ponto de análise.

### Comando recomendado para a rodada do Claude

Definir `EXTRA_KMZ` apontando para `Documentos EUROCLIMA+/Espanha/kmz/EIXO-MONTECLARO2.kmz`,
definir `OUTPUT_TAG=mc2` e executar `07_python/10_eixos_cascata.py` mantendo
`EUROCLIMA-rev.kmz` como base. O `OUTPUT_TAG` grava a rodada em `01_dados/cav_mc2` e
`01_dados/gis_derivado_mc2`, sem sobrescrever a carteira atual. A geometria
recebida tem ponto médio aproximado em `−29,0455307; −51,5562985`, estaca 294,48 km, e não
deve usar as altitudes do KML como cota de projeto sem conferir o datum. O retorno mínimo deve
conter: código do candidato, estação, cota MDE, área contribuinte, CAV, altura admissível,
interferência com Monte Claro/14 de Julho, perda de queda, energia e recomendação de aprofundar,
manter como sensibilidade ou descartar.

## Interface de entrega

Claude deve devolver:

1. tabela validada de novos eixos, com código, coordenadas, cota, área e restrição;
2. tabela de CAVs e alturas admissíveis;
3. parecer sobre cada ponto exploratório: aprofundar, manter como sensibilidade ou descartar;
4. arquivos que podem ser incorporados sem sobrescrever os capítulos Quarto.

Codex incorpora esses resultados nos capítulos e registra a origem de cada número. Alterações
em arquivos compartilhados devem ser comunicadas antes de editar para evitar conflito.
