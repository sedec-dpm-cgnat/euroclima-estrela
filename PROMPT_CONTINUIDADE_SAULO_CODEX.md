# Prompt de continuidade — Saulo Aires de Souza / Codex

Copie o texto abaixo como a primeira mensagem do seu Codex após clonar este
repositório.

---

Você está dando continuidade ao estudo técnico **EUROCLIMA+ / AECID —
alternativas de redução do risco de inundação em Estrela/RS**, desenvolvido no
âmbito do **DPM/SEDEC/MIDR**. Trabalhe como apoio técnico de engenharia,
hidrologia, geoprocessamento, modelagem hidráulica e elaboração de Termo de
Referência. Seja rigoroso, reproduzível e imparcial. Não trate nenhum resultado
preliminar como decisão de implantação.

## Objetivo final

Concluir a rodada de simulações **HEC-RAS 1D**, comparar a situação atual com as
alternativas de reservação e alternativas híbridas, estimar a redução de níveis,
manchas, duração e danos, e transformar os resultados em um **Termo de
Referência tecnicamente defensável** para contratação dos estudos detalhados.

O estudo deve permitir concluir, com transparência, uma destas possibilidades:

1. barragens de montante com benefício suficiente;
2. barragens complementadas por diques, proteção local e medidas não estruturais;
3. barragens tecnicamente, ambientalmente, socialmente ou economicamente
   inviáveis; ou
4. necessidade de dados e estudos adicionais antes de qualquer decisão.

## Regra de partida: leia antes de alterar

Na ordem abaixo, leia integralmente e produza primeiro um diagnóstico curto,
sem modificar arquivos:

1. `README.md`;
2. `HANDOFF.md`;
3. `STATUS_ATUAL_PROJETO.md`;
4. `PLANO_DE_ACAO.md`;
5. `09-relatorio-consolidado.qmd`;
6. `03-alternativas.qmd`;
7. `04-hidrologia-hand.qmd`;
8. `06-hecras-1d.qmd`;
9. `08-conclusoes.qmd`;
10. `91-reprodutibilidade.qmd`;
11. `06_resultados/DB_HIDROLOGICO_ACESSO_ESTRATEGIA.md`;
12. os documentos em `06_resultados/CLAUDE/` relacionados a Forqueta,
    Guaporé, alternativas, contornos, HEC-RAS e custos;
13. o conteúdo de `03_HECRAS/` e os scripts relevantes de `02_R/` e
    `07_python/`.

Depois confira o estado do Git, a branch atual e os arquivos modificados. Não
apague, reverta ou sobrescreva alterações de terceiros. Se houver divergência
entre o relatório, as tabelas e os scripts, registre a divergência e resolva-a
pela fonte reproduzível mais recente, mantendo uma nota de auditoria.

## Estado técnico conhecido

- Área de drenagem de referência em Estrela: aproximadamente **19.440 km²**.
- O trecho de estudo está no sistema Taquari–Antas, com contribuição do rio
  Taquari, do rio Forqueta, do rio Guaporé e de seus afluentes.
- As usinas existentes Monte Claro, Castro Alves e 14 de Julho são restrições
  longitudinais relevantes. Não se pode simular uma barragem a montante sem
  verificar remanso, afogamento, operação, segurança e interferência com a
  cascata existente.
- Os eixos E01–E12 vieram do KMZ do projeto, foram ancorados na BHO/ANA e
  passaram por delineação de bacias, perfil, topologia, CAV preliminar e
  verificação de interferências.
- A carteira **ALT-J** é uma referência de triagem, não uma alternativa de
  implantação escolhida.
- **GU1**, no rio Guaporé, é a hipótese estrutural independente mais promissora
  para complementar o controle a montante do ponto de análise.
- FQ1 e FQ2, no rio Forqueta, são alternativas laterais e mutuamente exclusivas
  por interferência de cota; devem ser testadas com a série observada do posto
  ANA 86745000 e com sensibilidades de defasagem.
- MC2, CA2 e 14J2, bem como comportas e outros pontos exploratórios, continuam
  como sensibilidades até que geometria, CAV, remanso e operação sejam
  confirmados.
- O alteamento de reservatórios existentes deve permanecer em segundo plano,
  apenas documentado como alternativa de sensibilidade. A triagem indicou
  baixo volume ganho por metro em relação ao volume necessário.

## O que já foi calculado — interpretar com cautela

Os resultados atuais são de triagem e não substituem o HEC-RAS calibrado:

- HAND sem novas barragens: cerca de **288,4 km²** de área inundável na área
  comparada;
- HAND com ALT-J na condição de triagem: cerca de **245,4 km²**;
- redução espacial preliminar: aproximadamente **43,0 km² / 14,9%**;
- em Estrela, a redução preliminar é da ordem de **30,77 para 24,60 km²**;
- hidrograma de triagem: pico natural próximo de **16.299 m³/s** e pico com
  ALT-J próximo de **6.213 m³/s**, valor a ser recalculado e substituído por
  resultado hidráulico consistente;
- o HAND não representa remanso, pontes, diques, propagação hidráulica,
  velocidades, duração ou operação de reservatórios. Não o chamar de mancha
  HEC-RAS no relatório.

Os valores de dano, custo, energia, benefício e vazão-alvo são preliminares.
Sempre informar origem, período, unidade, hipótese e incerteza. Não transforme
uma cifra de triagem em valor de projeto.

## Matriz obrigatória do HEC-RAS 1D

Monte, documente e execute os casos abaixo nesta ordem:

| Plano | Composição | Finalidade |
|---|---|---|
| **HEC-00 / REF** | Situação atual, sem novos reservatórios | Calibrar nível, vazão, tempo, mancha, pontes e condição de jusante |
| **HEC-01** | E02 + E04 | Primeiro caso com obra; medir ganho do arranjo-base |
| **HEC-02** | E02 + E04 + E08 | Medir ganho incremental de E08, condicionado à cascata existente |
| **HEC-03** | E02 + E04 + E12 | Medir ganho incremental de E12, condicionado à 14 de Julho |
| **HEC-04** | ALT-J + GU1 | Testar contribuição independente do Guaporé sem dupla contagem |
| **HEC-05** | ALT-J + FQ2 | Testar o Forqueta como afluência lateral antes de Estrela |
| **HEC-06** | C04/C05, FQ1, comportas e rede crítica | Sensibilidade de saturação, galgamento, operação e interferência |

Não chame HEC-03 de alternativa escolhida. HEC-00–03 são o conjunto mínimo
comparável; HEC-04 é a extensão prioritária; HEC-05 e HEC-06 são sensibilidades
que podem alterar a conclusão.

## Procedimento HEC-RAS 1D

### 1. Auditoria e preparação

- confirmar CRS, datum vertical, unidades, sentido do rio, estaqueamento e
  coerência das geometrias;
- conferir o fechamento de áreas e eliminar dupla contagem entre hidrograma de
  montante e afluências laterais;
- verificar as diferenças apontadas em
  `06_resultados/VALIDACAO/AUDITORIA_CONTORNOS_HECRAS.md`;
- não usar contornos sintéticos como se fossem levantamento topobatimétrico;
- distinguir claramente seção de cálculo, seção observada, confluência,
  ponte, barragem, afluência e condição de contorno.

### 2. Geometria 1D

Use os arquivos preliminares existentes como ponto de partida, mas prepare uma
lista objetiva do que a contratada deverá substituir ou conferir:

- eixo principal e tributários necessários;
- seções transversais com pontos acima e abaixo do nível d’água;
- canal, margens, planície, diques, aterros e estruturas transversais;
- quatro travessias preliminarmente inventariadas e demais pontes relevantes;
- confluências, estruturas existentes, barragens propostas e pontos de entrada
  lateral;
- valores de Manning separados para canal, margem e planície, com calibração;
- condição de jusante por nível observado, curva-chave ou domínio estendido.

O modelo principal deve ser **HEC-RAS 1D**. Não trocar por 2D sem justificativa
formal e compatibilização com o escopo aprovado.

### 3. Hidrologia e hidrogramas

- usar as séries observadas ANA/ONS disponíveis e registrar a estação, período,
  consistência, falhas e transformação aplicada;
- usar Muçum e Encantado como referências de séries longas e Estrela como
  controle de evento, sem superestimar a amostra curta de Estrela;
- usar o posto Forqueta 86745000 como referência lateral;
- usar Santa Lúcia/Guaporé 86580000 para a hipótese GU1;
- manter explícita a lacuna de novembro de 2023 e a incerteza da defasagem;
- separar hidrograma de montante, afluência do Guaporé, afluência do Forqueta e
  contribuições incrementais;
- jamais somar o pico agregado de Estrela como entrada de montante e novamente
  como afluência lateral;
- comparar volumes e picos, não apenas o pico máximo;
- testar pelo menos o evento de maio de 2024 e o evento extremo de novembro de
  2023 quando os dados permitirem.

O banco hidrológico institucional pode ser consultado em modo leitura quando o
ambiente de execução tiver acesso à rede. As credenciais devem ser fornecidas
somente por variáveis de ambiente locais; nunca escrever senha, token, URL com
senha ou arquivo de autenticação no repositório, no prompt ou no relatório.

### 4. CAV, reservatórios e operação

- usar as CAV oficiais do SNIRH/ANA quando existirem;
- para eixos sem reservatório existente, gerar CAV preliminar a partir de curvas
  de nível, área alagada e cotas, ajustando curvas monotônicas e documentando a
  resolução;
- aplicar a metodologia de batimetria sintética adotada no projeto apenas como
  estimativa com faixa de incerteza, nunca como levantamento;
- verificar a inversão CAV para transformar volume em cota em cada reservatório;
- definir NA, volume útil, volume de espera, soleira, comportas, vazão de saída,
  regra de pré-rebaixamento, operação durante a cheia e condição de segurança;
- testar barragem seca, soleira livre, comportas e deplecionamento preventivo
  somente como cenários explicitamente identificados;
- verificar remanso e interferência em Monte Claro, Castro Alves, 14 de Julho e
  demais aproveitamentos antes de aceitar qualquer altura.

### 5. Calibração

Calibre primeiro o HEC-00. Não calibre rugosidade ou condição de jusante usando
uma alternativa com barragem. Compare, no mínimo:

- níveis observados e simulados;
- instante de chegada e instante do pico;
- pico e volume do hidrograma;
- duração acima de patamares de inundação;
- extensão/área inundada observada e estimada;
- sensibilidade a Manning, condição de jusante e discretização das seções.

Entregue tabela de métricas, gráficos observação × simulação e uma nota com os
parâmetros aceitos e rejeitados. Se a calibração não for suficiente, pare de
tratar os resultados como comparação decisória e documente a limitação.

### 6. Saídas de cada cenário

Para HEC-00 a HEC-06, produzir, quando aplicável:

- hidrograma de montante e hidrogramas laterais;
- vazão, nível, profundidade e velocidade por seção;
- cota máxima e duração em Estrela, Lajeado, Encantado e pontos críticos;
- área e profundidade inundada;
- efeitos em pontes, diques, estradas, áreas urbanas e estruturas existentes;
- volume retido, volume descarregado e balanço de massa;
- energia gerada, perdas, custos e operação, quando o cenário incluir uso
  múltiplo;
- indicadores para a curva cota–dano e para a análise custo-benefício;
- incertezas de geometria, hidrologia, rugosidade, operação e batimetria.

## Alternativas híbridas e decisão

Depois da matriz de reservatórios, testar ou deixar especificados para a
contratação:

- diques e muros apenas nos trechos onde a mancha hidráulica justificar;
- proteção de instalações críticas e rotas de evacuação;
- zoneamento, alerta, previsão, reassentamento e medidas de preparação;
- combinações ALT-J + GU1, ALT-J + Forqueta e medidas locais;
- cenário de não implantação para comparação imparcial.

A decisão deve usar uma matriz multicritério com, pelo menos, redução de nível e
dano, segurança, remanso, área afetada, deslocamentos, ambiente, energia,
implantação, O&M, custo total, robustez operacional e incerteza. Se o benefício
depender de um parâmetro ainda não calibrado, mostrar a faixa e não apenas o
valor central.

## Termo de Referência — produto final

Ao fechar a rodada, atualizar ou elaborar a minuta do TR contendo:

1. contexto, problema e justificativa;
2. objetivo geral e objetivos específicos;
3. área de estudo, municípios, rios, reservatórios e população/infraestrutura
   potencialmente afetada;
4. escopo por produtos e etapas;
5. levantamento topográfico, topobatimétrico, cadastral e de estruturas;
6. aquisição, consistência e modelagem hidrológica;
7. modelagem hidráulica **HEC-RAS 1D** e calibração;
8. CAVs, reservatórios, comportas, operação e segurança;
9. avaliação de barragens novas, alteamento, Guaporé, Forqueta, diques,
   medidas não estruturais e não implantação;
10. manchas, danos, curva cota–dano e análise custo-benefício;
11. estudos ambientais, sociais, fundiários, riscos e licenciamento;
12. produtos cartográficos, shapefiles, GeoPackages, KMZs, planilhas, modelos,
    arquivos HEC-RAS e memória de cálculo;
13. governança, reuniões, validação e transferência de conhecimento;
14. equipe mínima, qualificações e responsabilidades;
15. cronograma, medições, critérios de aceite e forma de apresentação;
16. referências técnicas e dados de entrada;
17. limitações, premissas e requisitos de rastreabilidade.

O TR deve exigir que a contratada entregue arquivos abertos e reproduzíveis,
metadados, versões, logs, mapas georreferenciados, arquivos nativos do
HEC-RAS 1D e comparação entre observado e simulado. Deve deixar claro que a
contratada poderá recomendar barragens, diques, combinação ou não implantação,
sem obrigação de confirmar a hipótese inicial.

## Regras de execução e entrega

- trabalhar em branch própria e fazer commits pequenos, descritivos e
  reproduzíveis;
- não apagar histórico nem usar `git reset --hard`;
- não versionar credenciais, `.env`, tokens, `auth.json`, chaves ou dados
  pessoais;
- não afirmar que uma simulação foi executada sem arquivo de entrada, log,
  saída e verificação correspondente;
- atualizar o relatório, `STATUS_ATUAL_PROJETO.md`, `HANDOFF.md` e a seção de
  reprodutibilidade após cada etapa relevante;
- gerar figuras legíveis, com norte, escala, legenda, fonte e indicação clara
  de preliminar ou calibrada;
- manter o mapa interativo e os produtos GIS coerentes com as tabelas;
- registrar toda mudança de hipótese e toda divergência entre fontes;
- ao final, apresentar: arquivos alterados, comandos executados, resultados,
  limitações, pendências e recomendação técnica imparcial.

Comece agora pela leitura dos documentos listados, pelo diagnóstico do estado do
repositório e pela verificação do ambiente instalado. Em seguida, avance até a
primeira entrega útil sem esperar nova autorização para tarefas técnicas
reversíveis.

---

## Fim do prompt de continuidade
