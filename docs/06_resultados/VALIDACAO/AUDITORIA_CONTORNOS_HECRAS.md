# Auditoria dos contornos do HEC-RAS 1D

**Data da auditoria:** 07/09/2026  
**Status:** preparação — nenhum plano HEC-RAS foi executado.

## Resultado principal

Os insumos geométricos do trecho estão organizados, mas os hidrogramas ainda não
formam uma entrada hidráulica final. O arquivo calibrado de C4 contém o
hidrograma natural associado à seção de análise de **19.440 km²**, com pico de
**16.299 m³/s** e passo temporal de **1,0 h**. Ele pode
ser candidato à condição de montante do HEC-00 somente se o limite montante do
modelo coincidir exatamente com essa seção.

O C01 disponível para E02+E04 pertence à rodada de triagem antiga. Seu pico
resultante em Estrela é **9.217 m³/s**, mas o próprio relatório
classifica essa série como baseada em hidrograma sintético, tempo de viagem fixo
e parâmetros de comportas não calibrados. Ela deve ser usada apenas para conferir
ordem de grandeza, não como condição final do HEC-01.

## Fechamento espacial das áreas

| Componente | Área (km²) |
|---|---:|
| Limite de montante informado | 19.440,0 |
| Soma das seis laterais localizadas | 4.002,3 |
| Montante + laterais | 23.442,3 |
| Limite de jusante informado | 23.699,0 |
| Diferença a explicar | 256,7 |

A diferença de **256,7 km²** precisa ser explicada antes da
calibração: pode representar áreas não cadastradas, diferença entre seções de
controle ou inconsistência de áreas. Somar todas as laterais ao hidrograma de
19.440 km² sem fechar esse balanço pode duplicar contribuição.

## Decisão de modelagem registrada

1. **HEC-00:** usar o hidrograma calibrado como entrada de montante apenas após
   confirmar a seção de 19.440 km²; inserir as laterais com séries próprias ou
   transpostas e testar a condição de jusante.
2. **HEC-01:** não usar `Q_resultante_Estrela` do C01 como entrada de montante.
   É necessário gerar os efluentes de E02 e E04 no ponto de cada nó, depois
   propagá-los até o limite do HEC-RAS sem dupla contagem.
3. **Forqueta:** entra como afluência lateral a montante de Estrela, não como
   parcela já contida no hidrograma de montante, salvo se a desagregação da
   bacia demonstrar o contrário.
4. **Guaporé:** sua contribuição está a montante do ponto de análise e precisa
   ser retirada da parcela residual antes de qualquer cenário GU1.

## Insumos que destravam a execução

- séries efluentes nodais calibradas para E02 e E04;
- série de vazão lateral do Forqueta com defasagem e tratamento da lacuna de
  novembro de 2023;
- confirmação da área correspondente ao limite de 19.440 km²;
- seções topobatimétricas, pontes, diques e curva-chave/nível de jusante;
- definição da representação do Guaporé na decomposição do hidrograma.

O manifesto auditável está em
`03_HECRAS/contornos_preliminares/manifesto_contornos_hecras.csv`.
