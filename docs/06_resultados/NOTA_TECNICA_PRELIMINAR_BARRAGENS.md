# Nota Técnica Preliminar — Potencial de barragens de montante na redução dos danos de cheias em Estrela/RS

**Projeto EUROCLIMA+ / AECID — Componente técnico (SEDEC/MIDR)**
**Autores:** Cássio Guilherme Rampinelli — DPM/SEDEC/MIDR; [Saulo Aires de Souza, PhD](http://lattes.cnpq.br/6021309864695571) — DPM/SEDEC/MIDR · Julho–Agosto de 2026
**Status:** análise exploratória de ordem de grandeza, destinada a subsidiar a redação do Termo de Referência. **Não substitui** os estudos a serem contratados.

---

## 1. Objetivo

Responder, em nível de triagem, à pergunta que estrutura o Eixo 3 do estudo:

> *Quantas barragens, de que porte e com que volume de amortecimento seriam necessárias a montante para evitar — ou reduzir significativamente — os danos de uma cheia equivalente à de maio de 2024 em Estrela/RS?*

A resposta condiciona diretamente o escopo, o esforço de modelagem e o preço do contrato.

## 2. Base de dados utilizada

| Insumo | Origem | Resolução / porte |
|---|---|---|
| Modelo digital de elevação (`mdr.tif`) | base do projeto | 28,6 m, EPSG:32722 |
| Direções de fluxo D8 (`Fdr.tif`) | base do projeto | 28,6 m, EPSG:31982 |
| Base hidrográfica ottocodificada | BHO/ANA (`Drenagem_Bacia_Taquari.shp`) | 30.459 trechos |
| Eixos de barragem candidatos | `Barragem_A`, `Barragem_A2`, `Barragem_B` | 3 pontos |
| Série consistida de cotas do Taquari | Moraes, Collischonn, Buffon & Eckhardt (2024) | 1939–2023 |

Área de drenagem: **19.440 km²** no ponto de análise a montante; **22.472 km²** na seção
observada de Estrela; e **23.618 km²** na bacia Taquari-Antas completa. Essa distinção é
essencial: o Forqueta deságua a jusante do ponto de 19.440 km² e só entra no hidrograma
da seção de Estrela.

## 3. Delineação das bacias contribuintes

Delineação por *upstream BFS* sobre o grafo D8, com *snap* dos eixos à célula de drenagem cuja área acumulada mais se aproxima da área ottocodificada da BHO. A aderência entre as duas fontes foi excelente (erro < 1%), o que valida a grade de direções de fluxo.

| Eixo | Latitude | Longitude | Cota do eixo | Área controlada | % da bacia em Estrela | Aderência à BHO |
|---|---|---|---|---|---|---|
| **BAR-A** | −29,16163 | −51,83560 | 47 m | **15.760 km²** | **81,1 %** | 15.852 km² (−0,6%) |
| **BAR-A2** | −29,08147 | −51,65664 | 72 m | 12.777 km² | 65,7 % | 12.877 km² (−0,8%) |
| **BAR-B** | −29,05970 | −51,71858 | 72 m | 2.549 km² | 13,1 % | 2.547 km² (+0,1%) |

> **Atenção — os eixos são aninhados.** BAR-A situa-se a jusante da confluência dos ramos controlados por BAR-A2 e BAR-B. Os volumes **não são aditivos**: BAR-A já engloba as outras duas. A área incremental entre elas é de apenas 433 km².
>
> Portanto, as alternativas mutuamente exclusivas reais são:
> - **(i)** uma barragem única em BAR-A (81,1% da bacia); **ou**
> - **(ii)** o par BAR-A2 + BAR-B (78,8% da bacia), evitando uma estrutura única de grande porte.

## 4. Curvas cota-área-volume

Obtidas por *flood-fill* hidraulicamente conectado a montante de cada eixo, sobre o MDE de 28,6 m.

**Volume armazenado (hm³) por altura de barragem:**

| Altura | BAR-A | BAR-A2 | BAR-B | A2+B |
|---:|---:|---:|---:|---:|
| 20 m | 92 | 33 | 11 | 44 |
| 30 m | 255 | 63 | 28 | 91 |
| 40 m | 493 | 156 | 56 | 212 |
| 50 m | 788 | 311 | 96 | 407 |
| 60 m | 1.150 | 502 | 149 | 651 |
| 70 m | 1.648 | 732 | 216 | 948 |
| 80 m | **2.231** | 1.004 | 301 | 1.304 |

Área alagada correspondente em BAR-A: 26,7 km² a 40 m; 45,2 km² a 60 m; 62,5 km² a 80 m.

## 5. Alternativas estudadas e justificativa

Esta seção registra a lógica de seleção das alternativas, para que o estudo não seja interpretado como uma busca por uma barragem única já definida. A comparação foi organizada em camadas: (i) referência sem novas barragens e arranjos híbridos; (ii) alteamento das UHEs existentes; (iii) alternativas de um ou mais eixos novos; e (iv) diferentes regras de operação. O objetivo foi identificar quais hipóteses merecem modelagem hidráulica detalhada, e não aprovar obras.

### 5.1 Referência sem nova barragem e arranjos híbridos

A referência sem novo reservatório é indispensável porque mede o risco que continuará existindo mesmo se nenhum eixo for implantado. Ela também evita atribuir às barragens benefícios que podem ser obtidos por medidas de menor prazo, como alerta e previsão hidrometeorológica, ordenamento territorial, proteção localizada, realocação seletiva, retenção distribuída e operação coordenada dos reservatórios existentes.

Por isso, a alternativa estrutural não deve ser comparada apenas com o cenário "nada fazer". O Termo de Referência deve exigir pelo menos um arranjo híbrido, combinando medidas estruturais e não estruturais, com o mesmo hidrograma, horizonte de análise, curva cota–dano e critérios de segurança usados para as barragens.

### 5.2 Alteamento das UHEs existentes — alternativa de sensibilidade

O alteamento foi estudado porque poderia mobilizar volume sem abrir um novo eixo e, em princípio, reduzir desapropriações e licenciamento. As curvas oficiais do SNIRH, entretanto, indicam que o ganho conjunto das UHEs 14 de Julho, Castro Alves e Monte Claro é de aproximadamente **105 hm³ para 10 m de deplecionamento** e **139 hm³ para 15 m**, contra cerca de **3.230 hm³** estimados como necessários no evento de referência.

Assim, o alteamento permanece documentado como alternativa de sensibilidade, incluindo custos, segurança, estabilidade, vertedouro, remanso, regras de operação e impactos a montante. Os indícios disponíveis apontam para valores expressivos de obra e para ganho relativamente pequeno de volume de espera; portanto, ele não será o eixo principal da investigação antes da confirmação por projeto básico, topografia, geotecnia e avaliação econômica.

### 5.3 Primeira rodada: um reservatório grande versus dois reservatórios distribuídos

A primeira rodada usou os eixos BAR-A, BAR-A2 e BAR-B (e os pontos equivalentes B1, B3 e B2 em KMZ) para responder a duas perguntas: se a concentração de volume em um vale principal seria mais eficiente que a distribuição em dois ramos; e se uma barragem convencional teria desempenho suficiente para uma cheia de grande magnitude.

| Alternativa de triagem | Por que foi estudada | Resultado que orienta a próxima fase |
|---|---|---|
| BAR-A/B1 isolada | Maximizar área controlada e volume em uma única estrutura | Maior efeito hidrológico potencial, mas concentra risco, impacto territorial e custo em uma obra de grande porte. |
| BAR-A2/B3 + BAR-B/B2 | Distribuir o controle em dois ramos e evitar uma única barragem muito alta | Área controlada semelhante, mas volume menor; a combinação não reproduz o desempenho do eixo principal. |
| Barragem convencional | Representar a solução com reservatório permanentemente operado e vertedouro de soleira livre | A maior parte dos cenários satura; a redução de pico é insuficiente para o evento de referência. |
| Barragem seca (*dry dam*) | Reservar volume vazio para a cheia, com descarga de fundo e vertedouro próximo da crista | Foi a única configuração capaz de produzir redução relevante de pico na triagem; requer verificação de segurança, operação e manutenção. |

Essa rodada não define a alternativa final. Ela mostrou que a função de controle de cheias — especialmente o volume vazio disponível antes do evento — é tão importante quanto a altura da barragem. Os resultados de BAR-A/B1, BAR-A2/B3 e BAR-B/B2 permanecem como referência histórica da triagem inicial; a carteira atual foi revisada com os 12 eixos E01–E12 e com a posição longitudinal das usinas em operação.

O arquivo `EUROCLIMA-rev.kmz` contém as 12 geometrias de eixo que formam essa carteira. A rede derivada da topologia D8/BHO indica três caminhos geomorfológicos principais: `E01 → E11 → E12`; `E02 → E03 → E08 → E09 → E10 → E11 → E12`; e `E04 → E05 → E06 → E07 → E08 → E09 → E10 → E11 → E12`. Esses caminhos não significam que todos os eixos devam ser construídos; eles definem onde é tecnicamente possível testar barragens em série ou em ramos convergentes.

### 5.4 Carteira revisada de eixos novos

Na rodada revisada, cada eixo foi filtrado por posição longitudinal, interferência com usinas em operação, altura admissível, curva cota–área–volume, volume de espera e desempenho energético. A cascata Monte Claro–Castro Alves–14 de Julho foi tratada como restrição dominante. A expressão "baixa interferência" abaixo significa prioridade de verificação, e não ausência de remanso comprovada.

A interferência não deve ser apresentada apenas como veto binário. O remanso pode começar a reduzir a queda e a energia da usina de montante antes de atingir sua cota mínima operacional. Por isso, a ficha de cada eixo deverá separar: **(a)** altura de veto, quando o remanso atinge a cota mínima operacional; e **(b)** altura de início da perda energética. Na triagem do Claude, por exemplo, a perda em E12 começa aproximadamente entre 15 e 20 m de altura, enquanto o veto operacional ocorre próximo de 55–60 m; a precisão desse intervalo depende da discretização e do datum. Já E10 apresenta balanço energético líquido negativo em toda a faixa viável e deve permanecer fora da carteira principal por esse motivo.

| Grupo / alternativa | Por que foi estudada | Situação na triagem |
|---|---|---|
| **E02 isolado** | Testar o maior eixo prioritário fora da cascata principal e medir sua contribuição individual | Prioritário para confirmar remanso, geologia e licenciamento; cerca de 1.377 hm³ no teto geométrico de 120 m. |
| **E04 isolado** | Testar o maior volume individual da carteira, também sem interferência direta da cascata principal | Prioritário para investigação; cerca de 2.211 hm³ no teto geométrico de 120 m. O teto é técnico, não uma altura de engenharia aprovada. |
| **E02 + E04** | Arranjo-base com os dois eixos prioritários e sem conflito direto comprovado com Monte Claro–Castro Alves–14 de Julho | Primeira alternativa composta para HEC-RAS 1D; cerca de 1.794 hm³ de espera e 57,0% da bacia controlada, antes do roteamento definitivo. |
| **E02 + E04 + E12** | Testar se a inclusão de um eixo com maior cobertura supera a limitação espacial do arranjo-base | Cenário de cobertura; cerca de 2.282 hm³ de espera e 81,1% da bacia, mas E12 é condicionado pelo remanso da 14 de Julho. |
| **E02 + E04 + E08** | Representar um arranjo intermediário, adicionando cobertura sem incluir todos os eixos condicionados | Cenário intermediário; E08 é condicionado por Castro Alves. |
| **E02 + E04 + E01 + E05 + E08** | Testar diversificação espacial, cobertura e contribuição de tributário | Cenário ampliado; pode elevar cobertura e volume, mas agrega complexidade, áreas inundadas e conflitos operacionais. E01, E05 e E08 exigem confirmação específica. |
| **E01** | Avaliar um tributário com menor área inundável e possível independência hidráulica | Alternativa complementar; volume menor, com restrição operacional de Cotiporã a confirmar. |
| **E05** | Verificar se a revisão longitudinal elimina a inviabilidade artificial apontada na primeira análise | Alternativa condicional a Castro Alves; não deve ser descartada sem confirmar remanso e cota operacional. |
| **E03, E06, E07 e E08** | Representar diferentes posições na faixa de influência de Castro Alves | Alternativas condicionadas; servem para testar a relação entre cobertura, volume e perda de queda. |
| **E09, E10, E11 e E12** | Quantificar a contribuição dos eixos da cascata inferior | Cenários condicionados por Monte Claro e/ou 14 de Julho. E10 fica fora da carteira principal até revisão, pois o balanço energético líquido preliminar foi negativo. |

### 5.4.1 Resultado dos eixos exploratórios no Forqueta

O Forqueta foi testado como contribuição lateral na seção de Estrela, não como vazão
adicional no ponto de análise de 19.440 km². A série observada do posto Passo do Coimbra
(86745000) tem 68,7 anos e 97,8% de dados consistidos. Em 13 eventos pareados, a
defasagem central Forqueta–Estrela foi 0 dia; o pico observado de 1.292,3 m³/s foi
transposto para 3.837 m³/s na área total do tributário.

| Cenário em Estrela | Pico (m³/s) | Redução | Leitura |
|---|---:|---:|---|
| ALT-J sem Forqueta | 7.005 | 58,6% | referência da carteira do Antas |
| ALT-J + FQ1 | 6.880 | 59,3% | ganho marginal de 0,7 ponto percentual |
| ALT-J + FQ2 | 6.816 | 59,7% | ganho marginal de 1,1 ponto percentual |
| ALT-J + FQ1 + FQ2 | 6.880 | 59,3% | arranjo inviável por interferência de cota |

FQ1 e FQ2 não entram na alternativa de referência. **Isso não é descarte do Forqueta.**
Como o tributário conflui a montante de Estrela, FQ1/FQ2 permanecem alternativas
condicionadas para avaliar a afluência lateral e o controle de cheias em Lajeado, Estrela
e Bom Retiro do Sul no HEC-RAS 1D. O eixo FQ1 fica condicionado à
confirmação de uma defasagem positiva no evento de novembro de 2023, que coincide com
uma lacuna no Passo do Coimbra. O eixo FQ1 a 30 m tem aproximadamente 212 hm³ e FQ2
148 hm³; o NA de FQ1 fica 12,5 m acima da cota do eixo FQ2. A ação de dados prioritária
é reativar a curva-chave e obter observações subdiárias em Barra do Fão (86780000).

### 5.4.1.1 Matriz combinada com a carteira do rio das Antas

Para testar se a inclusão do Forqueta muda a capacidade de controle, foi executada uma
matriz com ALT-A a ALT-J, sem Forqueta, com FQ1 e com FQ2, sob as regras de barragem seca,
comportas e convencional. O exutório é o posto de Estrela (22.472 km²), com hidrogramas
próprios do Antas e do Forqueta e defasagem central medida de 0 h. O pico natural sintético
em Estrela é 16.903 m³/s, próximo do máximo observado de 17.261 m³/s em 19/11/2023.

| Regra | Melhor combinação admissível | Pico em Estrela | Redução | Excesso sobre 4.000 m³/s |
|---|---|---:|---:|---:|
| Barragem seca | ALT-J + FQ2 | 6.802 m³/s | 59,8% | 2.802 m³/s |
| Comportas | ALT-J + FQ1 | 7.887 m³/s | 53,3% | 3.887 m³/s |
| Convencional | ALT-D sem Forqueta | 15.799 m³/s | 6,5% | 11.799 m³/s |

O melhor resultado fisicamente admissível foi ALT-J + FQ2, mas ele ainda permanece
2.802 m³/s acima do limiar preliminar de 4.000 m³/s; equivale a uma redução de 60,6%
em relação ao pico observado de 2023. Nesta rodada, nenhuma combinação alcançou uma
magnitude compatível com a não ocorrência de cheia. O limiar de 4.000 m³/s não é limite
legal e deverá ser substituído pela curva cota–dano calibrada e pela simulação de cota,
profundidade e duração no HEC-RAS 1D.

Os resultados completos estão em `tabelas/roteamento_combinado_antas_forqueta.csv`,
com síntese em `ROTEAMENTO_COMBINADO_ANTAS_FORQUETA.md` e hidrogramas em
`tabelas/hidrogramas_combinados_antas_forqueta.csv`.

### 5.4.1.2 Busca ampliada de carteiras — outras barragens no Antas

Como a pergunta de projeto é se a inclusão de outras barragens poderia levar a vazão
em Estrela a uma magnitude compatível com a não ocorrência de cheia, foi executada uma
busca exaustiva das adições à ALT-J. A busca principal percorreu as 32 combinações
formadas por E03, E06, E07, E09 e E11, mantendo E10 excluído por seu balanço energético
negativo. Em seguida, foi calculado um envelope teórico de 64 combinações incluindo E10
e uma matriz de 192 combinações com SEM_FORQUETA, FQ1 ou FQ2 e as regras seca e
comportas.

| Escopo | Melhor composição | Pico em Estrela | Excesso sobre 4.000 m³/s | Abaixo de 4.000 m³/s |
|---|---|---:|---:|---:|
| Adições à ALT-J, E10 excluído | ALT-J | 7.005 m³/s | 3.005 m³/s | 0 de 32 |
| Envelope incluindo E10 | ALT-J | 7.005 m³/s | 3.005 m³/s | 0 de 64 |
| Adições à ALT-J com Forqueta | ALT-J + FQ2, seca | 6.802 m³/s | 2.802 m³/s | 0 de 192 |

O resultado não deve ser interpretado como prova de que a construção de qualquer eixo
adicional seja inútil. Ele mostra que, no roteamento de triagem, E03/E06/E07/E09/E11
estão aninhados ou subordinados ao mesmo terminal E12, que controla 81,1% da área de
19.440 km². Acrescentá-los não aumenta a área terminal controlada nem modifica o pico
no exutório. Esses eixos continuam podendo alterar remanso, níveis de montante,
distribuição do armazenamento e segurança em pontos intermediários; para capturar isso,
é necessário HEC-RAS 1D com operação coordenada, tempos de viagem e estruturas reais.

Assim, **a carteira atual de eixos do Antas, mesmo ampliada pelo envelope teórico e
combinada ao Forqueta, não alcança o limiar preliminar de 4.000 m³/s**. O limiar ainda
é apenas uma referência de triagem, e a decisão deve ser refeita com a curva cota–dano
e a hidráulica calibrada. Os arquivos reproduzíveis são `tabelas/carteiras_ampliadas_antas_principal.csv`,
`tabelas/carteiras_ampliadas_antas_envelope_E10.csv`, `tabelas/carteiras_ampliadas_antas_forqueta.csv`
e `BUSCA_CARTEIRAS_AMPLIADAS_ANTAS_FORQUETA.md`.

O próximo candidato estrutural é o **GU1 no rio Guaporé**, porque não é apenas uma
adição redundante da carteira E01–E12. Para avaliá-lo, a sub-bacia do Guaporé precisa
ser desagregada do hidrograma sintético do Antas, roteada pelo GU1 e recombinada na
seção de análise. A soma direta de uma série do Guaporé ao hidrograma atual produziria
dupla contagem. Essa era a razão para o GU1 ter ficado inicialmente fora do roteamento
numérico da carteira de referência; a desagregação foi executada na rodada seguinte.

Essa desagregação foi executada em uma primeira triagem. A seção de 19.440 km² foi
particionada em 2.486,7 km² do Guaporé e 16.953,3 km² de vertente residual. O GU1
controla 1.993,7 km², ou 80,2% do tributário. Com o máximo histórico do posto Santa
Lúcia, ALT-J + GU1 a 100 m produziu **4.532 m³/s** em Estrela, contra 7.038 m³/s
na mesma decomposição sem GU1; com o pico de novembro de 2023 e defasagem zero, o
resultado a 120 m (envelope geométrico) foi **4.763 m³/s**, contra 4.902 m³/s sem
GU1. A combinação ALT-J + GU1 + FQ2 não melhorou o máximo histórico nesta rodada
(6.166 m³/s a 100 m e defasagem zero).

Foram avaliadas 384 combinações com duas magnitudes de evento, quatro defasagens,
seis alturas de 0 a 120 m, ALT-J/sem obra, FQ2/sem Forqueta e regras seca/comportas.
Nenhuma ficou abaixo de 4.000 m³/s. A altura de 120 m é somente envelope geométrico
da CAV; não é altura admissível, e os hidrogramas ainda são sintéticos Gamma, com pico
diário transposto. Os resultados completos estão em `tabelas/roteamento_guapore_antas.csv`,
`ROTEAMENTO_GUAPORE_ANTAS.md` e `VALIDACAO/HIDROGRAMAS_GUAPORE_ALTJ.svg`.

### 5.4.2 Nova hipótese a montante — Guaporé

O posto Santa Lúcia (86580000) e a BHO indicam cerca de 2.470–2.487 km² no Guaporé,
contribuição de ordem semelhante à do Forqueta, mas situada a montante do ponto de análise.
O banco hidrológico DPM confirma 31.047 registros diários entre 1940 e 2024, área ANA de
2.470 km² e máximo observado de 5.077,1 m³/s; a estatística consistida disponível cobre
1940–2022. A série é, portanto, suficientemente longa para uma investigação preliminar,
mas ainda precisa ser transposta para a seção do eixo e pareada com os eventos de Estrela.
Foi criado o eixo exploratório GU1-PROPOSTO no trecho BHO 2681952, com área a montante
de 1.993,7 km² (80,2% da bacia), ponto médio aproximado em **−28,902566; −51,981445**
e cota MDE de 227,5 m.

| Altura geométrica | Área alagada | Volume preliminar |
|---:|---:|---:|
| 30 m | 1,97 km² | 21,7 hm³ |
| 50 m | 4,82 km² | 87,2 hm³ |
| 70 m | 9,24 km² | 223,9 hm³ |
| 100 m | 20,85 km² | 667,4 hm³ |

Esses volumes são classe de triagem e não representam altura admissível. O GU1 está
próximo de aproveitamentos existentes do próprio Guaporé, incluindo Guaporé e Monte Cuco;
remanso, interferência energética e regras operativas precisam ser calculados antes de
qualquer comparação com E02/E04. O eixo foi criado como hipótese exploratória, não como
alternativa selecionada. Produtos: `GIS/eixo_guapore_proposto.kmz`,
`tabelas/eixo_guapore_proposto.csv`, `GIS/eixo_guapore_proposto.gpkg` e a rodada isolada
`01_dados/cav_guapore/`.

### 5.5 Critério de priorização e alternativa a levar ao HEC-RAS 1D

As alternativas devem ser comparadas nesta ordem: **(1)** redução de vazão e nível no trecho protegido; **(2)** interferência e remanso nas usinas existentes; **(3)** volume de espera efetivamente disponível e risco de saturação; **(4)** área inundada, população e patrimônio expostos; **(5)** custo de implantação, operação e manutenção; **(6)** energia gerada e energia perdida; e **(7)** segurança, licenciamento, geotecnia e resiliência operacional.

Com os dados atuais, **E02 + E04 é a alternativa-base para a primeira rodada do HEC-RAS 1D**, porque concentra o teste nos dois eixos prioritários e evita, nesta etapa, a interferência direta comprovada na cascata principal. **E02 + E04 + E08** será o cenário intermediário e **E02 + E04 + E12** o cenário de cobertura ampliada. O Guaporé (GU1) será a extensão estrutural prioritária após a calibração; o Forqueta (FQ1/FQ2) entra como sensibilidade lateral. E01, E05 e os demais eixos condicionados entram em sensibilidades, não como obras selecionadas.

Ainda não há alternativa final selecionada. A escolha somente poderá ser feita depois de: (i) calibrar hidrologia e HAND contra maio de 2024; (ii) simular remanso e operação no HEC-RAS 1D; (iii) obter a curva cota–dano com Atlas de Desastres, exposição territorial e custos unitários; e (iv) comparar custo, benefício, energia, impactos e incertezas. A figura de divisão de quedas deve apresentar todas essas alternativas e destacar a recomendação apenas após essa validação.

### 5.5.1 Matriz explícita de simulação no HEC-RAS 1D

Para evitar que a nomenclatura de alternativas seja confundida com a de cascatas com
comportas, a matriz contratada fica definida em planos HEC. A regra é executar o caso
sem obra antes de comparar qualquer obra e acrescentar um eixo por vez na primeira
rodada.

| Plano | Correspondência | Composição | Função | Prioridade |
|---|---|---|---|---|
| **HEC-00 / REF** | situação atual | sem novos reservatórios | calibração de maio de 2024, nível de jusante e curva cota–dano | obrigatório |
| **HEC-01 / ALT-A / C01** | carteira-base | **E02 + E04** | primeiro caso com obra e referência de ganho incremental | obrigatório |
| **HEC-02 / ALT-D / C03** | carteira intermediária | **E02 + E04 + E08** | acrescentar E08, condicionado à verificação de Castro Alves | obrigatório |
| **HEC-03 / ALT-E / C02** | carteira ampliada | **E02 + E04 + E12** | acrescentar E12, condicionado à verificação de 14 de Julho | obrigatório |
| **HEC-04** | extensão estrutural | **ALT-J + GU1** | investigar controle independente do Guaporé a montante do ponto de análise | prioridade após HEC-00–03 |
| **HEC-05** | extensão lateral | **ALT-J + FQ2** | avaliar o Forqueta no trecho de Estrela, sem dupla contagem no montante | sensibilidade prioritária |
| **HEC-06** | rede crítica | C04, C05, FQ1 e combinações selecionadas | avaliar comportas, saturação, galgamento e incertezas de operação | opcional |

Assim, o **primeiro caso com obra é HEC-01 (E02 + E04)**. HEC-02 e HEC-03 não
representam decisões finais: são controles incrementais para medir o valor de E08 e
E12. O HEC-04 só deve receber o hidrograma do Guaporé depois de desagregar essa
sub-bacia da parcela residual do Antas; o HEC-05 deve inserir o Forqueta como
hidrograma lateral na confluência, não somá-lo à entrada de 19.440 km². FQ1 e FQ2
são mutuamente exclusivas. A topologia e a ordem de simulação estão na figura
`VALIDACAO/DIAGRAMA_TOPOLOGICO_ALTERNATIVAS_HECRAS.svg`.

### 5.6 Cascatas de barragens com comportas

Além dos arranjos isolados, devem ser analisadas barragens com comportas operadas em cascata. A hipótese é que o controle distribuído possa sincronizar a descarga dos reservatórios, reduzir a saturação de uma única estrutura e usar a previsão de cheia para abrir volume de espera em diferentes pontos. O efeito não pode ser estimado somando volumes: cada reservatório altera o hidrograma recebido pelo seguinte e pode também elevar o nível de jusante de uma usina ou de outro eixo.

Os cenários mínimos são: **C01 — E02 + E04**, como rede de dois ramos prioritários; **C02 — E02 + E04 + E12**, como arranjo de cobertura; **C03 — E02 + E04 + E08**, como arranjo intermediário; **C04 — E09 + E10 + E11 + E12**, como série crítica no canal principal; e **C05 — E01 + E02 + E04 + E08 + E09 + E10 + E11 + E12**, como sensibilidade de rede ramificada. E10 deve permanecer fora da carteira principal até a revisão do balanço energético, mas pode ser mantido no cenário hidráulico de sensibilidade para medir seu efeito sobre a propagação da cheia.

O roteamento conjunto deverá conservar massa a cada passo de tempo: a afluência de cada reservatório será a soma da contribuição incremental de sua sub-bacia, dos efluentes dos reservatórios imediatamente a montante e do deslocamento temporal no trecho. A regra de comportas deverá limitar a vazão durante o enchimento, prever deplecionamento preventivo, respeitar a capacidade máxima de descarga e transferir a afluência quando o reservatório saturar. Devem ser reportados abertura das comportas, níveis máximos, volumes armazenados, saturação, galgamento, pico a jusante, energia e perda de queda.

Como primeira sensibilidade, com hidrograma sintético, tempo de viagem fixo de 6 h e parâmetros de comporta ainda não calibrados, o roteamento produziu:

| Cenário | Eixos com comportas | Pico resultante (m³/s) | Redução do pico | Saturados / galgamentos |
|---|---|---:|---:|---:|
| C01 | E02 + E04 | 9.217 | 48,8% | 0 / 0 |
| C02 | E02 + E04 + E12 | 6.650 | 63,1% | 0 / 0 |
| C03 | E02 + E04 + E08 | 8.713 | 51,6% | 0 / 0 |
| C04 | E09 + E10 + E11 + E12 | 14.753 | 18,0% | 4 / 4 |
| C05 | E01 + E02 + E04 + E08 + E09 + E10 + E11 + E12 | 5.965 | 66,9% | 1 / 1 |

O resultado sugere que **C01, C03 e C02 devem ser lidos como uma sequência de comparação**, e não como uma escolha isolada: C01 mede a carteira-base, C03 o ganho incremental de E08 e C02 o ganho de E12. C04 evidencia que a cascata crítica, isoladamente, satura e oferece pouco amortecimento. C05 apresentou a maior redução nesta hipótese, mas não pode ser tratado como recomendação porque inclui um galgamento e o eixo E10, cujo balanço energético preliminar é negativo. Esses números são apenas triagem e estão detalhados em `CASCATAS_COMPORTAS_TRIAGEM.md`.

O inventário reproduzível está em `CASCATAS_COMPORTAS_METODOLOGIA.md`, com a rede imediata em `tabelas/rede_imediata_cascatas_comportas.csv` e os cenários em `tabelas/cascatas_candidatas_comportas.csv`. Esses resultados são preparação para o roteamento; a validação final depende do HEC-RAS 1D, de tempos de viagem e de regras operativas reais.

## 6. Volume de amortecimento necessário

Evento de referência adotado (a recalibrar com a série consistida): pico de **18.000 m³/s** em Estrela (0,93 m³/s/km²), lâmina escoada de 260 mm, **volume escoado total de ≈ 5.050 hm³**, permanência acima de 4.000 m³/s por 116 h.

O volume que precisaria ser retirado do hidrograma, `V = ∫ max(0, Q − Q_alvo) dt`:

| Vazão-alvo em Estrela | Redução do pico | Volume necessário |
|---:|---:|---:|
| 4.000 m³/s *(sem dano relevante)* | 78 % | **3.230 hm³** |
| 6.000 m³/s | 67 % | 2.462 hm³ |
| 8.000 m³/s | 56 % | 1.811 hm³ |
| 9.000 m³/s *(metade do pico)* | 50 % | 1.524 hm³ |
| 12.000 m³/s | 33 % | 798 hm³ |

### 6.1 Existe um piso físico de redução

BAR-A controla 81,1% da bacia. Os **3.680 km² restantes (18,9%)** continuam produzindo escoamento mesmo com a barragem totalmente fechada — da ordem de **3.400 m³/s** de pico residual em Estrela. Nenhum arranjo de barragens nesses eixos reduz o pico abaixo desse valor.

## 7. Amortecimento efetivo — roteamento de Puls

Simulação de piscina nivelada com vertedouro de soleira livre (`Q = 2,1·L·H^1,5`) e descarga de fundo (`Q = 0,62·A·√(2gh)`). Testados dois arranjos: **convencional** (soleira a ¾ da altura, reservatório com volume morto) e **seca / *dry dam*** (reservatório normalmente vazio, descarga de fundo dimensionada para liberar ≈ 4.000 m³/s, vertedouro apenas junto à crista).

| Cenário | Vol. utilizado | Pico em Estrela | Redução | Saturou? |
|---|---:|---:|---:|:---:|
| A1 — BAR-A 40 m convencional | 493 hm³ | 18.000 m³/s | 0 % | **sim** |
| A2 — BAR-A 60 m convencional | 1.118 hm³ | 17.016 m³/s | 5,5 % | não |
| A3 — BAR-A 80 m convencional | 1.712 hm³ | 15.106 m³/s | 16,1 % | não |
| B1 — BAR-A2 60 m convencional | 489 hm³ | 17.804 m³/s | 1,1 % | não |
| B2 — BAR-B 60 m convencional | 105 hm³ | 17.976 m³/s | 0,1 % | não |
| **S1 — BAR-A 60 m seca** | 1.150 hm³ | 17.518 m³/s | 2,7 % | **sim** |
| **S2 — BAR-A 80 m seca** | **2.067 hm³** | **8.303 m³/s** | **53,9 %** | não |
| S3 — BAR-A2 80 m seca | 1.004 hm³ | 15.627 m³/s | 13,2 % | **sim** |
| S4 — A2 80 m + B 60 m secas | 1.152 hm³ | 17.113 m³/s | 4,9 % | **sim** |

*"Saturou" = o reservatório encheu durante o evento e passou a transferir a cheia integralmente para jusante, perdendo a função de amortecimento.*

### 7.1 Preparação do HEC-RAS 1D

O Claude organizou os insumos preliminares do trecho detalhado: aproximadamente **39,4 km de eixo**, **102 seções transversais** (37 no trecho detalhado), **4 travessias**, **6 confluências** e condições de contorno consolidadas. A geometria está em `CLAUDE/claude_hecras_eixo.gpkg`, com tabelas auxiliares de eixo, seções, travessias, confluências e contornos.

Esses arquivos são uma base de montagem, não um modelo calibrado. Ainda faltam seções topobatimétricas, cota de tabuleiro e vãos das pontes, diques e aterros, curva–chave em Estrela e regras operativas verificadas. O Rio Forqueta, com cerca de 14,6% da bacia na seção de Estrela, deve entrar como contribuição lateral concentrada; ele não altera o hidrograma no ponto de análise de 19.440 km². A rodada do Claude reproduziu o pico observado em Estrela com erro de −2,1% usando a série do Passo do Coimbra, mas a lacuna de novembro de 2023 exige dados subdiários em Barra do Fão. O Guaporé, a montante do ponto de análise, deve ser incluído como hipótese lateral adicional no estudo de alternativas. A condição de jusante é especialmente sensível: a declividade estimada nos últimos 10 km é de apenas `6,3 × 10⁻⁵ m/m`, de modo que o nível em Estrela pode ser governado pelo remanso de jusante. Deve-se testar uma ordem de grandeza de sensibilidade, estender o modelo até a foz ou usar nível variável observado antes de interpretar a lâmina calculada.

### 7.2 Cadeia hidrológica e HAND

O cálculo hidrológico preliminar foi organizado em cinco camadas: (i) delimitação D8 e
conferência com a BHO; (ii) conversão da vazão específica calibrada de 0,0269 m³/s/km² em
afluências; (iii) hidrograma do evento; (iv) continuidade de massa em cada reservatório,
`S(t+Δt) = S(t) + [I(t) − O(t)]Δt`; e (v) transferência do hidrograma resultante para
Estrela. O volume requerido foi calculado por `V_req = ∫ max(0, Q − Q_alvo)dt`.

A rodada C3/C4 calibrada adotou, para o Antas no ponto de análise, pico de 16.300 m³/s,
lâmina de 227 mm e vazão-base de 926 m³/s. Para Estrela, o roteamento natural com o
Forqueta produziu 16.903 m³/s, contra 17.261 m³/s observados; a diferença de −2,1% é
adequada para uma triagem, mas não substitui a calibração hidráulica. A frequência continua
ancorada em Muçum, cuja série é longa; Estrela é controle de evento, não amostra principal.

O HAND foi usado como triagem altimétrica e orientação das áreas potencialmente conectadas
à drenagem. Ele não substitui o HEC-RAS 1D, pois não representa pontes, remanso, duração,
armazenamento lateral nem operação de comportas.

As figuras comparativas históricas estão em `figuras/14_hidrogramas_natural_vs_cascatas.png`
e `figuras/15_hidrograma_natural_vs_C02.png`; a figura calibrada de ALT-J está em
`figuras/16_hidrograma_calibrado_ALTJ.png`. Os cenários sintéticos C01–C05 não devem ser
misturados aos resultados calibrados C1–C4 sem identificar a origem, o ponto de controle e
a regra operativa. A nota completa de integração está em
`CLAUDE/CLAUDE_NOTA_FORQUETA.md`.

#### Volume requerido versus volume de espera por reservatório

O volume requerido `V_req = ∫ max(0, Q_Estrela − Q_alvo)dt` é calculado no hidrograma da
seção de controle de Estrela. Ele representa uma ordem de grandeza do volume que deveria ser
retirado do hidrograma para manter a vazão abaixo da meta, sob uma hipótese ideal de controle.
Não é uma distribuição automática de volume entre as barragens.

Na rodada SINV, cada eixo recebe uma altura admissível e uma fração de espera de 50% do volume
máximo correspondente à sua própria CAV. Assim, `V_espera,i = 0,50 × V_max,i(H_i)` e a cota
de espera é obtida pela inversão da CAV: `NA_mxn,i = cota_eixo,i + CAV_i⁻¹(V_max,i − V_espera,i)`.
As alternativas somam os volumes nominais dos seus eixos, mas somente o roteamento pode
determinar quanto será usado, quando e com qual pico residual.

Na formulação atual, `Q_alvo = 4.000 m³/s` é uma meta preliminar em Estrela, associada à
hipótese de vazão abaixo da qual não haveria dano relevante. O roteamento simplificado converte
essa meta em uma meta local proporcional à área, `Q_alvo,i = 4.000 × A_i/19.440`; essa é uma
regra de triagem e não uma vazão observada a montante. O valor deve ser recalibrado com dados
de nível, danos e HEC-RAS 1D.

| Alternativa | Eixos | Volume de espera nominal | Observação |
|---|---|---:|---|
| ALT-A | E02 + E04 | 1.794 hm³ | soma de 688,7 hm³ em E02 e 1.105,3 hm³ em E04 |
| ALT-D | E02 + E04 + E08 | 2.104 hm³ | inclui 310,2 hm³ em E08 |
| ALT-E/C02 | E02 + E04 + E12 | 2.282 hm³ | inclui 488,2 hm³ em E12; eixo condicionado à 14 de Julho |
| ALT-I | E02 + E04 + E01 + E05 + E08 | 2.235 hm³ | mais estruturas e restrições condicionais |

### 7.3 Pontos exploratórios de queda concentrada

O perfil longitudinal foi suavizado e avaliado por queda média em janelas de 10 km. O
resultado não define novos eixos de engenharia, mas fornece pontos de reconhecimento:

| Código | Latitude | Longitude | Queda média em 10 km | Uso preliminar |
|---|---:|---:|---:|---|
| CA2-PROPOSTO | −29,0457167 | −51,3622784 | 32,8 m | queda a jusante de Castro Alves |
| MC2-PROPOSTO | −29,0455307 | −51,5562985 | 6,3 m | geometria fornecida pelo usuário, entre Monte Claro e 14 de Julho |
| 14J2-PROPOSTO | −29,0658852 | −51,6384943 | 33,0 m | queda a jusante de 14 de Julho |
| EST1-PROPOSTO | −29,1656775 | −51,7456402 | 8,9 m | controle de cheias próximo de Estrela |

O arquivo separado `EIXO-MONTECLARO2.kmz` foi conferido e contém uma `LineString` sobre o
canal principal. Seu ponto médio cai na estaca aproximada 294,48 km do perfil e a cerca de
12 m do talvegue amostrado. A geometria original foi incorporada ao
`GIS/eixos_exploratorios_propostos.kmz`; a cota de triagem de 107,1 m vem do perfil suavizado
do MDE, enquanto as altitudes originalmente gravadas no KML permanecem pendentes de
verificação de datum. O `EUROCLIMA-rev.kmz` continua contendo 12 linhas com rótulo genérico
`EIXO`; portanto, MC2 deve entrar no pipeline como candidato adicional, não como eixo
selecionado ou como E13 definitivo antes da validação de CAV, remanso, energia e interferência.

### 7.4 Energia e custo–benefício

A potência preliminar foi calculada por `P = ηρgQ_turbH_liq/10⁶`, com integração temporal
para energia e limitação pela potência instalada. A interferência com usinas existentes foi
tratada como perda de queda/energia, distinguindo o início de perda energética do veto
físico ou operacional. O valor a reportar é `ΔE_liq = E_novo − E_perdida_nas_usinas_existentes`.

Para a análise econômica, o benefício deve ser obtido pela diferença entre dano esperado
anual sem e com medida, a partir de curvas cota–dano e frequência. Com taxa `i` e horizonte
`n`, `FVP = [1 − (1+i)^−n]/i`, `VPL = VP_B − VP_C` e `B/C = VP_B/VP_C`. Os parâmetros
de triagem de 50 anos, 6% a.a. e O&M de 0,8% devem ser confirmados na contratação. O dano
placeholder de R$ 2.500 milhões não deve governar a decisão.

## 8. Conclusões preliminares

As conclusões abaixo mantêm os resultados de roteamento da primeira rodada BAR-A/BAR-A2/BAR-B para rastreabilidade. Para a carteira revisada E01–E12, a leitura atualizada é a da seção 5: E02 + E04 é o arranjo-base, E02 + E04 + E12 é o cenário de cobertura e as cascatas com comportas devem ser validadas antes da seleção final.

**(1) Barragens convencionais são praticamente inócuas para um evento desta magnitude.** Com vertedouro de soleira livre, a redução de pico fica entre 0% e 16%, mesmo com 80 m de altura. O volume da cheia (≈ 5.050 hm³) é 2 a 10 vezes maior que o volume disponível nos reservatórios.

**(2) Só o arranjo de barragem seca de grande porte produz efeito relevante.** BAR-A com 80 m de altura, operada como *dry dam* (≈ 2.070 hm³ de volume dedicado, 62 km² de área inundável), reduz o pico em ≈ 54% — de 18.000 para 8.300 m³/s.

**(3) Ainda assim, isso não evita os danos da cheia de 2024.** Os 8.300 m³/s residuais continuam muito acima da vazão sem dano relevante (ordem de 4.000 m³/s). Para chegar lá seriam necessários ≈ 3.230 hm³ de amortecimento — **acima da capacidade física do melhor eixo, mesmo com 80 m de altura**.

**(4) O par BAR-A2 + BAR-B é claramente inferior a BAR-A isolada.** Controla área semelhante (78,8% vs. 81,1%), mas dispõe de apenas 1.304 hm³ contra 2.231 hm³ a 80 m, por causa da geometria dos vales. Ambos saturam no evento de referência.

**(5) Consequência para o Termo de Referência.** A hipótese "construir barragens a montante resolve o problema de Estrela" **não se sustenta isoladamente**. O TR deve, portanto:

- enquadrar o Eixo 3 como **análise comparativa de alternativas híbridas** (barragens + diques + realocação + controle de uso do solo + alerta precoce), e **não** como projeto de barragens;
- exigir explicitamente o cálculo do **volume de amortecimento necessário** e a **verificação de saturação do reservatório** para o evento de referência, com curvas cota-área-volume derivadas de MDE;
- exigir a **decomposição controlado / não-controlado** da bacia, de modo a explicitar o piso físico de redução;
- tratar a **operação do reservatório** (barragem seca, comportas, pré-deplecionamento) como variável de projeto, não como detalhe;
- incorporar a **análise custo-benefício** com curvas cota-dano, único critério capaz de arbitrar entre uma estrutura de 80 m de altura e um conjunto de medidas distribuídas.

### Atualização após a rodada do Forqueta

Os eixos FQ1 e FQ2 não devem ser apresentados como solução de referência. Com a série
observada do Passo do Coimbra, o ganho marginal sobre ALT-J foi de 0,7 ponto percentual
para FQ1 e 1,1 ponto percentual para FQ2 na seção de Estrela, e os dois eixos são
mutuamente exclusivos por interferência de cota. FQ1 só deve ser reaberto se dados
subdiários de Barra do Fão confirmarem defasagem positiva no evento de novembro de 2023.

O Guaporé passa a ser a nova hipótese exploratória prioritária entre os tributários: sua
contribuição é de ordem semelhante à do Forqueta e está a montante do ponto de análise.
Foi gerado o GU1-PROPOSTO para triagem geométrica, mas ainda faltam remanso, interferência
com as usinas Guaporé/Monte Cuco, energia, operação e roteamento. Nenhum eixo novo foi
selecionado como obra.

## 9. Limitações desta análise

Esta é uma triagem de ordem de grandeza. Especificamente:

- o hidrograma de referência combina uma rodada sintética histórica com a calibração C3/C4; a rodada calibrada ainda é de triagem e deve ser substituída/validada por séries subdiárias e HEC-RAS 1D;
- a decomposição controlado/não-controlado ainda é proporcional à área em parte da triagem; o Forqueta foi tratado como afluência lateral na seção de Estrela, enquanto o Guaporé ainda não foi roteado;
- a defasagem medida do Forqueta foi 0 dia em 13 eventos, mas há lacuna justamente no evento de novembro de 2023; esse parâmetro não deve ser considerado resolvido;
- as curvas cota-área-volume vêm de MDE de **28,6 m**, adequado para triagem mas não para projeto;
- não há verificação **geotécnica, ambiental, fundiária ou de segurança de barragens** dos eixos; a área alagada de 62 km² em BAR-A implica desapropriações e possível remoção de população;
- o limiar de "vazão sem dano relevante" (4.000 m³/s) é **estimado** e deve ser determinado pelo HEC-RAS 1D, integrado ao cadastro de edificações e à curva cota–dano.
- o ponto de análise de 19.440 km² e a seção de Estrela de 22.472 km² não são intercambiáveis; alternativas em tributários devem ser avaliadas no controle correto;

## 10. Reprodutibilidade

| Arquivo | Função |
|---|---|
| `07_python/02_bacias_barragens.py` | delineação D8, acumulação de fluxo, curvas CAV |
| `02_R/00_config.R` | parâmetros da bacia, eixos, limiares |
| `02_R/01_baixa_dados_ana.R` | download das séries ANA/HidroWeb |
| `02_R/02_volume_amortecimento.R` | volume necessário, piso físico, altura requerida |
| `02_R/03_roteamento_puls.R` | roteamento de reservatório, cenários |
| `01_dados/gis_derivado/bacias_barragens.gpkg` | bacias delineadas |
| `01_dados/gis_derivado/reservatorios_barragens.gpkg` | manchas dos reservatórios (20/30/40 m) |
| `01_dados/cav/cav_barragens.csv` | curvas cota-área-volume |
| `07_python/37_propoe_eixo_guapore.py` | eixo exploratório GU1, KMZ, GPKG e CSV |
| `06_resultados/GIS/eixo_guapore_proposto.kmz` | conferência espacial do GU1 |
| `01_dados/cav_guapore/` | rodada isolada de CAV e ancoragem BHO/D8 |
| `06_resultados/CLAUDE/CLAUDE_NOTA_FORQUETA.md` | resultados observados e roteamento do Forqueta |

### Referência

MORAES, S. R.; COLLISCHONN, W.; BUFFON, F. T.; ECKHARDT, R. R. *Revisão e consolidação da série histórica dos níveis das cheias do rio Taquari em Lajeado de 1939 a 2023.* Porto Alegre, 2024. Nota técnica.
