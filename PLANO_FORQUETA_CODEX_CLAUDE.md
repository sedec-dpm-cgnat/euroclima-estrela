# Divisão de tarefas — eixo exploratório no Forqueta

## Contexto comum

Foram propostos dois eixos de triagem no rio Forqueta a partir da rede BHO:

| Código | Coordenadas do ponto médio | Área a montante | Fração do Forqueta | Papel |
|---|---|---:|---:|---|
| FQ1-PROPOSTO | -52,029566; -29,403114 | 2.353,6 km² | 82,7% | opção condicionada |
| FQ2-PROPOSTO | -52,090824; -29,322861 | 2.226,7 km² | 78,3% | sensibilidade exclusiva |

As geometrias são perpendiculares ao talvegue e foram criadas exclusivamente
para triagem. Não são locações de engenharia. O KMZ está em
`06_resultados/GIS/eixos_forqueta_propostos.kmz` e a tabela em
`06_resultados/tabelas/eixos_forqueta_propostos.csv`.

## Claude — modelagem hidrológica e energética — concluído em 01/08/2026

1. Ler as saídas isoladas em `01_dados/cav_forqueta/` e verificar FQ1/FQ2. **Concluído.**
2. Incluir FQ1 como eixo de controle de tributário no roteamento calibrado. **Concluído.**
3. Rodar os cenários ALT-J, FQ1, FQ2 e combinações. **Concluído.**
   - ALT-J sem Forqueta;
   - ALT-J + FQ1;
   - ALT-J + FQ2;
   - ALT-J + FQ1 + FQ2, somente como sensibilidade;
   - FQ1 isolado e FQ2 isolado.
4. Estimar a defasagem do hidrograma usando a série observada 86745000. **Concluído:**
   0 dia em 13 eventos, com lacuna crítica em novembro de 2023.
5. Testar regras de barragem seca, comportas e operação convencional. **Concluído.**
6. Entregar os resultados, sem editar `.qmd`, `HANDOFF.md` ou `STATUS_ATUAL_PROJETO.md`.
   **Concluído:**
   - `claude_fq_roteamento_calibrado.csv`;
   - hidrogramas dos cenários;
   - sensibilidade ao tempo de defasagem;
   - nota curta com pico residual, volume usado, saturação e implicações para
     energia/SINV.

## Codex — integração e próxima investigação

1. **Concluído:** manter os produtos isolados e auditar cota, área contribuinte,
   ancoragem BHO e CAV de FQ1/FQ2.
2. **Concluído nesta rodada:** integrar a nota de Claude ao relatório, retirar FQ1/FQ2
   da alternativa de referência e registrar a incompatibilidade geométrica.
3. Corrigir a interface hidrológica do relatório: 19.440 km² é o ponto de análise a
   montante; 22.472 km² é a seção de Estrela, onde o Forqueta entra lateralmente.
4. Investigar o Guaporé (posto Santa Lúcia 86580000) como alternativa a montante:
   BHO/D8, CAV preliminar, posição dos aproveitamentos, energia e roteamento.
5. Registrar como pendência crítica a reativação da curva-chave e de dados subdiários
   de Barra do Fão (86780000), sem transformar a lacuna em dado estimado.
6. Atualizar a análise de danos e custo–benefício sem tratar 4.000 m³/s como limiar
   definitivo antes do HEC-RAS 1D.
7. Renderizar e verificar o site Quarto após a investigação do Guaporé.

## Regra de integração

Claude não edita `.qmd`, `HANDOFF.md`, `STATUS_ATUAL_PROJETO.md` nem o pipeline
canônico de eixos. Codex não edita os scripts `claude_*` nem os CSVs de
`06_resultados/CLAUDE/`. Os resultados só entram na recomendação após verificar
remanso, defasagem, licenciamento, segurança, perdas de geração e curva
cota–dano.
