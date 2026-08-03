# Inventário de cascatas para comportas

**Fonte geométrica:** `Documentos EUROCLIMA+/Espanha/kmz/EUROCLIMA-rev.kmz`.
O KMZ contém 12 geometrias lineares de eixos; o pipeline `10_eixos_cascata.py` as converteu em E01–E12 e gerou a relação de bacias aninhadas.

## Como ler

A rede abaixo é uma aproximação de conexão imediata: cada eixo de montante é ligado ao menor eixo jusante que contém sua bacia. Ela serve para ordenar o roteamento e evitar somar hidrogramas de forma independente. Não substitui a confirmação do talvegue, do trecho de rio, do tempo de viagem e do remanso.

## Conexões imediatas

| Montante | Jusante imediato | Área montante (km²) | Área jusante (km²) | Incremental entre eixos (km²) |
|---|---|---:|---:|---:|
| E01 | E11 | 2.548,8 | 15.456,9 | 12.908,1 |
| E02 | E03 | 3.591,2 | 3.771,8 | 180,6 |
| E03 | E08 | 3.771,8 | 11.950,5 | 8.178,7 |
| E04 | E05 | 7.497,5 | 7.922,8 | 425,3 |
| E05 | E06 | 7.922,8 | 8.158,8 | 236,0 |
| E06 | E07 | 8.158,8 | 8.173,5 | 14,7 |
| E07 | E08 | 8.173,5 | 11.950,5 | 3.777,0 |
| E08 | E09 | 11.950,5 | 12.330,0 | 379,5 |
| E09 | E10 | 12.330,0 | 12.778,1 | 448,1 |
| E10 | E11 | 12.778,1 | 15.456,9 | 2.678,8 |
| E11 | E12 | 15.456,9 | 15.759,8 | 302,9 |

## Caminhos geomorfológicos

- E01 → E11 → E12
- E02 → E03 → E08 → E09 → E10 → E11 → E12
- E04 → E05 → E06 → E07 → E08 → E09 → E10 → E11 → E12

## Arranjos a simular

| ID | Arranjo | Tipo | Finalidade | Situação |
|---|---|---|---|---|
| C01 | E02+E04 | ramos_convergentes | testar a operação coordenada dos dois eixos prioritários | primeiro cenário conjunto |
| C02 | E02+E04+E12 | ramos_convergentes_com_eixo_jusante | testar o ganho de cobertura com E12, condicionado à 14 de Julho | cenário de cobertura |
| C03 | E02+E04+E08 | ramos_convergentes_com_eixo_intermediario | testar cobertura intermediária sem incluir toda a cascata inferior | cenário intermediário; E08 condicionado a Castro Alves |
| C04 | E09+E10+E11+E12 | serie_principal | testar barragens com comportas em série e a interação com a cascata existente | cenário crítico; E09/E10/E11/E12 condicionados |
| C05 | E01+E02+E04+E08+E09+E10+E11+E12 | rede_ramificada | avaliar a coordenação de ramos e reservatórios em série | sensibilidade; depende de validar todos os eixos |

## Correspondência com os planos do HEC-RAS 1D

C01 não será executado isoladamente como um estudo desconectado: ele é o plano
**HEC-01**, depois do **HEC-00/REF** sem obra. C03 é o **HEC-02** e C02 é o
**HEC-03**, nessa ordem, para que o ganho incremental de E08 e E12 seja mensurado.
C04 e C05 formam o **HEC-06**, uma sensibilidade posterior. GU1 e FQ1/FQ2 não
pertencem à rede E01–E12: entram nos planos laterais HEC-04 e HEC-05, com
hidrogramas próprios e sem dupla contagem.

O primeiro cenário com obra, portanto, é **E02 + E04 (HEC-01/C01)**. A sequência
completa e o diagrama de conectividade estão em
`06_resultados/VALIDACAO/DIAGRAMA_TOPOLOGICO_ALTERNATIVAS_HECRAS.svg`.

## Regra de roteamento a implementar

A cada passo de tempo, o reservatório recebe a vazão incremental de sua sub-bacia e as vazões efluentes dos reservatórios imediatamente a montante, após o tempo de viagem do trecho. A comporta deve ser modulada por uma regra coordenada, com limites de abertura, capacidade máxima de descarga, volume mínimo de segurança, nível máximo e condição de saturação. Quando um reservatório atingir o nível máximo, ele deixa de amortecer e a vazão de saída deve se aproximar da afluência, sem criar artificialmente vazão maior que a entrada.

O resultado deve reportar, para cada reservatório e para Estrela: pico afluente, pico efluente, volume armazenado, nível máximo, abertura de comportas, saturação, galgamento, energia e perdas de queda. Os cenários devem incluir operação independente, operação coordenada, previsão com 24/48/72 h e falha ou atraso de acionamento.

## Limitação

A topologia foi derivada da grade D8/BHO e as CAVs dos eixos novos são de classe B, derivadas do MDE natural. O HEC-RAS 1D continua sendo necessário para confirmar remanso, níveis, seção de controle, pontes, confluências e tempos de propagação.
