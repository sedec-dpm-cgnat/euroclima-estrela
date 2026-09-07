# Avaliação do gerador estocástico Kirsch–Nowak no EUROCLIMA+

**Data:** 07/09/2026  
**Status:** recomendação de uso como módulo probabilístico complementar; não substitui a calibração do evento de referência nem a modelagem HEC-RAS 1D.

## 1. O que foi localizado

O material indicado pelo usuário está disponível localmente em:

`C:\Users\cassi\OneDrive\Documents\Ajumar\Kirsch-Nowak_Streamflow_Generator-master`

O nome correto da pasta contém um sublinhado entre `Nowak` e `Streamflow`. A cópia local está em regime de arquivos sob demanda do OneDrive; por isso, parte dos arquivos não foi aberta diretamente nesta máquina. A estrutura e os arquivos-fonte foram conferidos na versão pública dos autores:

<https://github.com/julianneq/Kirsch-Nowak_Streamflow_Generator>

O repositório contém código MATLAB para gerar séries diárias sintéticas correlacionadas em vários postos, assumindo hidrologia estacionária. A geração é feita em duas escalas:

1. geração de totais mensais correlacionados por transformação logarítmica, normalização e decomposição de Cholesky;
2. desagregação mensal para diária por seleção probabilística de vizinhos históricos (k-NN), usando padrões diários de meses históricos próximos no calendário e reescalonamento proporcional.

## 2. Por que ele pode ajudar neste estudo

O EUROCLIMA hoje possui uma rodada paramétrica por evento: um hidrograma tipo gama é ancorado em pico, base, área e volume e depois decomposto/roteado entre os eixos. Essa rodada é adequada para a triagem do evento de referência e para testar rapidamente alternativas, mas não fornece uma distribuição de muitos eventos independentes.

O Kirsch–Nowak pode acrescentar uma camada probabilística para:

- gerar centenas ou milhares de anos equivalentes de vazões diárias;
- estimar a frequência de excedência do limiar provisório em Estrela;
- comparar redução de pico, volume e duração entre ALT-J, GU1, FQ2 e as demais carteiras;
- estimar confiabilidade do volume de espera e risco de reenchimento;
- produzir distribuições de energia gerada, energia sacrificada e danos evitados;
- preservar, em uma mesma realização, a dependência entre Antas, Forqueta e Guaporé.

O último ponto é importante: uma realização conjunta é preferível a somar hidrogramas independentes. Ela permite testar se a coincidência de picos entre os tributários é rara, típica ou dominante no risco de Estrela.

## 3. Compatibilidade com as séries já disponíveis

Há base suficiente para uma primeira aplicação, mas é preciso montar a entrada com critério topológico. As séries disponíveis incluem, entre outras:

| Posto | Uso preliminar | Período local observado |
|---|---|---:|
| 86510000 | Muçum / Antas | 1940–2026 |
| 86720000 | Encantado / controle intermediário | 1941–2026 |
| 86745000 | Forqueta / Passo do Coimbra | 1957–2026 |
| 86580000 | Guaporé / Santa Lúcia, base DPM | 1940–2024 |
| 86879300 | Estrela, validação de exutório | 2020–2023 |

As datas acima são intervalos brutos dos arquivos locais, não uma declaração de consistência hidrológica. Antes da geração, cada série deve passar por auditoria de lacunas, consistência, unidades, duplicidades, valores negativos e cobertura comum. O posto de Estrela é curto e deve ser usado principalmente para validação e ajuste final; para uma série longa, a geração deve partir dos postos de montante e a vazão em Estrela ser obtida por composição/roteamento.

A primeira auditoria reproduzível está em [AUDITORIA_ENTRADA_KIRSCH_NOWAK.md](VALIDACAO/AUDITORIA_ENTRADA_KIRSCH_NOWAK.md). Ela encontrou uma janela bruta comum de 1957-07-10 a 2024-04-30 entre os quatro candidatos de montante, mas também mostrou que o posto 86720000 tem 6.260 dias ausentes no período total observado (completude bruta de 79,67%). Portanto, ainda não é correto chamar a janela comum de 66,9 anos utilizáveis: a harmonização e o tratamento das lacunas são uma pendência real antes da geração.

### Cuidado com postos aninhados

O gerador não conhece a rede de drenagem. Se forem fornecidos simultaneamente postos aninhados, não se pode somar suas vazões como se fossem contribuições independentes. A entrada deve representar nós ou incrementos hidrológicos compatíveis com a topologia: componente do Antas acima do domínio de Estrela; componente do Guaporé; componente do Forqueta; contribuições laterais ou residuais entre postos; e seção de validação em Estrela, sem somá-la novamente às suas próprias nascentes.

Para o Guaporé, isso é especialmente importante: a sub-bacia foi explicitamente separada do hidrograma do Antas na rodada GU1. O mesmo critério deve ser mantido no ensemble estocástico para evitar dupla contagem.

## 4. O que ele não resolve

Há quatro limitações que precisam aparecer na nota técnica:

1. **Estacionariedade.** A versão principal assume que a estatística histórica seguirá válida no futuro. Não incorpora, sozinha, tendência climática ou mudança de regime.
2. **Escala temporal.** O produto é diário. O HEC-RAS 1D e a análise de onda de cheia precisam de condições subdiárias, portanto será necessária uma etapa posterior de desagregação temporal ou um gerador de eventos horários calibrado.
3. **Extremos fora da amostra.** O k-NN reutiliza padrões diários históricos e o gerador mensal trabalha na estrutura estatística das observações. Ele não deve ser tratado como prova de que reproduz automaticamente o evento de novembro de 2023 ou a cheia de maio de 2024.
4. **Operação hidráulica.** As vazões geradas não incluem, por si, comportas, regras de operação, CAV, remanso, pontes ou restrições de segurança. Cada realização deve ser roteada pelo mesmo modelo de reservatórios e, para os casos selecionados, pelo HEC-RAS 1D.

## 5. Como incorporar ao fluxo do EUROCLIMA+

O gerador deve entrar como **C7 — ensemble estocástico de vazões**, depois da auditoria das séries e antes da seleção dos hidrogramas a serem executados no HEC-RAS:

```text
séries ANA/DPM
      ↓
auditoria e harmonização diária
      ↓
componentes hidrológicos não aninhados
      ↓
Kirsch–Nowak: ensemble multissítio
      ↓
roteamento CAV + comportas + defasagens
      ↓
seleção de eventos representativos
      ↓
HEC-RAS 1D e curva cota–dano
```

### Rodada recomendada

**Fase 1 — diagnóstico.** Preparar 3–4 componentes, sem rodar HEC-RAS: Antas, Forqueta, Guaporé e uma seção de validação. Comparar histórico e sintético quanto a médias e desvios mensais, autocorrelação diária/mensal, curvas de permanência, correlações espaciais, máximas anuais, volume de eventos e coincidência dos picos.

**Fase 2 — ensemble de roteamento.** Gerar inicialmente 1.000 realizações de 30 anos, ou quantidade equivalente de anos sintéticos. Roteá-las pelo roteador Python já existente, mantendo a decomposição incremental de áreas e proibindo a soma de hidrogramas gama independentes.

**Fase 3 — HEC-RAS 1D.** Selecionar eventos representativos por quantis de pico, volume, duração e coincidência Antas–Forqueta–Guaporé. Não é necessário executar milhares de simulações hidráulicas; o ensemble serve para selecionar e quantificar a incerteza, e o HEC-RAS detalha os casos críticos e medianos.

## 6. Recomendação técnica

**Sim, vale incorporar o gerador**, mas como uma camada probabilística complementar.

| Produto | Finalidade | Método principal |
|---|---|---|
| Evento de referência | reproduzir as cheias históricas de interesse | séries observadas + calibração C3/C4 |
| Triagem de alternativas | comparar rapidamente carteiras | hidrogramas paramétricos e roteamento atual |
| Risco e robustez | frequência, incerteza e desempenho esperado | ensemble Kirsch–Nowak + roteamento |

Assim, não se substitui um método pelo outro. O Kirsch–Nowak deve responder **com que frequência e sob quais combinações de tributários** uma alternativa deixa de atender ao limiar; o evento calibrado e o HEC-RAS devem responder **como a cheia se propaga, onde transborda e quais danos permanecem**.

O primeiro passo executável é construir o arquivo de entrada multissítio, sem alterar os resultados oficiais da nota. A validação deve ser aprovada antes de usar o ensemble para atualizar custo-benefício ou selecionar a alternativa final.

## Referências da metodologia

- Giuliani, M.; Herman, J.; Quinn, J. [Kirsch–Nowak Streamflow Generator — repositório e documentação](https://github.com/julianneq/Kirsch-Nowak_Streamflow_Generator).
- Kirsch, B. R.; Characklis, G. W.; Zeff, H. B. (2013). *Evaluating the impact of alternative hydro-climate scenarios on transfer agreements: Practical improvement for generating synthetic streamflows*. Journal of Water Resources Planning and Management, 139(4), 396–406. DOI: [10.1061/(ASCE)WR.1943-5452.0000287](https://doi.org/10.1061/(ASCE)WR.1943-5452.0000287).
- Nowak, K.; Prairie, J.; Rajagopalan, B.; Lall, U. (2010). *A nonparametric stochastic approach for multisite disaggregation of annual to daily streamflow*. Water Resources Research, 46(8). DOI: [10.1029/2009WR008530](https://doi.org/10.1029/2009WR008530).
