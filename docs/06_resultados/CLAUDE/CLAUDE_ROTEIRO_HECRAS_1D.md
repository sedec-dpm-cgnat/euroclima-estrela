# Roteiro técnico — modelo HEC‑RAS 1D do trecho detalhado

**Projeto EUROCLIMA+ / AECID — componente técnico SEDEC/MIDR**
**Trilha:** modelagem hidráulica · elaborado por Claude · julho de 2026
**Escopo:** trecho detalhado do rio Taquari na área urbana de Estrela/RS

> Roteiro de preparação. Nenhum modelo foi construído — este documento lista o que existe, o que falta e como montar.

---

## 1. Por que 1D neste trecho

Decisão do gestor. É adequada para o objetivo desta etapa — obter perfis de linha d'água e cotas de inundação por cenário de vazão, com e sem barramentos a montante — e é substancialmente mais rápida de calibrar que um modelo 2D.

Limitação a registrar no TR: o 1D não representa explicitamente a velocidade transversal na planície nem o perigo hidrodinâmico (h·v). Nesta linha metodológica, o HEC-RAS será mantido exclusivamente em 1D; a limitação deve ser tratada com indicadores compatíveis com o 1D, dados de exposição, HAND como triagem e, se o contrato exigir uma análise complementar, ferramentas separadas como FloodAdapt/SFINCS — sem transformar HEC-RAS 2D em requisito.

> **Atualização de 30/07/2026.** Os insumos foram levantados da base geoespacial e estão nas tabelas `claude_hecras_*.csv` e no `claude_hecras_eixo.gpkg`. Ver §11.

## 2. Extensão proposta

| Elemento | Valor | Fonte |
|---|---:|---|
| Trecho de modelagem (KMZ) | **39,4 km** | `Trecho_Modelagem` em `EUROCLIMA-rev.kmz` |
| Área do voo LiDAR previsto | 16,3 km² | `AreaLIDAR_DRONE` |
| Batimetria prevista | 1,35 km² | `ECOBATIMETRO_01` + `ECOBATIMETRO2` |
| Área de drenagem no limite de montante | 19.440 km² | delineação D8 |
| Área de drenagem no limite de jusante | 23.699 km² | delineação D8 |

**Sugestão de trecho detalhado para esta etapa preliminar:** os ~12 km centrais que compreendem a área urbana de Estrela e Lajeado, entre a foz do Arroio Boa Vista e a jusante da ponte da BR‑386. É o trecho onde estão as edificações que determinam a curva cota‑dano.

## 3. Dados disponíveis

| Insumo | Arquivo | Situação |
|---|---|---|
| Modelo digital de elevação | `GIS/raster/mdr.tif` | 28,6 m — **insuficiente para o canal**, serve para a planície |
| Direções de fluxo D8 | `GIS/raster/Fdr.tif` | ok |
| Perfil longitudinal do talvegue | `CLAUDE/claude_perfil_principal.csv` | cotas, áreas e coordenadas por estaca |
| Traçado do trecho | `Trecho_Modelagem` (KMZ) | 39,4 km |
| Hidrografia ottocodificada | `Drenagem_Bacia_Taquari.shp` | BHO/ANA, com área acumulada |
| Sub-bacias dos afluentes | `baciadrenagem*.shp` | Forqueta 2.845 km², Boa Vista 576 km², Estrela 241 km², Sampaio 255 km² |
| Mancha observada de 2024 | `mancha_v3_1.shp` | 24.459 polígonos, RS inteiro |
| Mapa de perigo HAND/MGB | `05_MAPA_DE_PERIGO_A_INUNDACAO_PARA_O_RS/` | raster unificado |
| Manchas HAND geradas | `01_dados/gis_derivado/mancha_*.tif` | com e sem barragem |
| Municípios | `Municipios_RS.shp` | IBGE |
| Série consistida de cotas | `Referencias/revisao_consolidacao...pdf` | 1939–2023, **a digitalizar** |

## 4. Dados faltantes — bloqueantes

| Dado | Por que é necessário | Como obter |
|---|---|---|
| **Batimetria do canal** | O MDE registra a lâmina d'água; sem o fundo, a capacidade do canal fica indefinida e o modelo superestima extravasamento | Levantamento do Eixo 1; provisoriamente, seção sintética por inversão de Manning (ver §6) |
| **Seções transversais topobatimétricas** | Geometria do 1D | Eixo 1 — 20 seções previstas |
| **Curva‑chave em Estrela** | Converter as cotas históricas em vazão e definir a condição de jusante | Eixo 1 — 10 medições de vazão previstas |
| **Séries de vazão ANA** | Hidrogramas de entrada e calibração | `02_R/01_baixa_dados_ana.R` — **nunca executado** |
| **Cota de tabuleiro das pontes** | Estruturas no 1D; BR‑386 é crítica | Eixo 1 — cadastro de infraestrutura |
| **Cotas de soleira das edificações** | Curva cota‑dano | Eixo 1 — cadastro técnico |

## 5. Condições de contorno

### Montante
Hidrograma no limite de montante do trecho (área 19.440 km²). Fontes possíveis, em ordem de preferência:

1. Série observada da ANA no posto de Muçum ou Encantado, propagada;
2. Hidrograma sintético já parametrizado em `02_R/02_volume_amortecimento.R`;
3. Para os cenários **com barramento**, o hidrograma efluente calculado pelo roteamento — disponível em `06_resultados/tabelas/hidrogramas_operacao_comportas.csv`.

### Laterais
Hidrogramas dos afluentes, escalados por área de drenagem:

| Afluente | Área | Fração da bacia em Estrela |
|---|---:|---:|
| Rio Forqueta | 2.845 km² | 14,6 % |
| Arroio Boa Vista | 576 km² | 3,0 % |
| Arroio Sampaio | 255 km² | 1,3 % |
| Arroio Estrela | 241 km² | 1,2 % |

### Jusante
*Normal depth* com a declividade média do trecho. Do perfil longitudinal, a declividade em Estrela é de **0,18 m/km** e em Bom Retiro do Sul de **0,17 m/km** — valores muito baixos, típicos de planície.

> **Atenção:** com declividade dessa ordem, o remanso do Guaíba pode governar o nível em eventos extremos. Recomenda-se estender o modelo até a foz ou impor uma condição de nível variável no tempo, e testar a sensibilidade do resultado em Estrela à condição de jusante.

## 6. Seção sintética provisória, enquanto não há batimetria

Enquanto o levantamento do Eixo 1 não ocorre, a geometria do canal pode ser aproximada por inversão da equação de Manning — o mesmo princípio adotado por Domeneghetti (2016) para modelagem em regiões sem dados:

```
h = [ (Q · n) / (B · √S) ] ^ (3/5)
```

com `B` medido no MDE (largura do espelho), `S` do perfil longitudinal e `n` = 0,030 a 0,035. A seção submersa é então representada como trapezoidal ou parabólica com essa profundidade.

**Isso é triagem, não projeto.** Serve para ordenar alternativas, não para dimensionar obra. O erro esperado na cota de inundação é da ordem de 1 a 2 m.

## 7. Sequência de montagem

| # | Passo | Produto |
|---|---|---|
| 1 | Preparar o terreno: reprojetar `mdr.tif` para EPSG:31982 e recortar o trecho | `terrain.tif` |
| 2 | Traçar o eixo do rio a partir de `claude_perfil_principal.csv` | *river centerline* |
| 3 | Gerar seções a cada 200 m no trecho detalhado, 500 m no restante | *cross sections* |
| 4 | Rebaixar o canal nas seções pela profundidade sintética do §6 | seções corrigidas |
| 5 | Inserir as pontes (BR‑386, ferrovia, travessias urbanas) | estruturas |
| 6 | Atribuir Manning: 0,030 canal, 0,060 planície vegetada, 0,12 urbano | rugosidade |
| 7 | Montar os planos de simulação (§8) | planos |
| 8 | Calibrar contra a mancha de 2024 e as marcas históricas | modelo calibrado |

## 8. Planos de simulação propostos

Os planos foram reorganizados para que a primeira rodada compare o caso sem obra com
alternativas que acrescentam um eixo por vez. A nomenclatura C01–C05 permanece para
os cenários de comportas; HEC-00–HEC-06 é a nomenclatura dos planos hidráulicos.

| Plano HEC | Cenário | Obras/entradas | Vazão de montante / laterais | Ordem |
|---|---|---|---|---|
| **HEC-00 / REF** | situação atual e calibração de maio/2024 | sem novos reservatórios | observada / reconstituída; laterais calibradas | 1 |
| **HEC-01 / ALT-A / C01** | primeiro caso com obra | E02 + E04 | efluente roteado | 2 |
| **HEC-02 / ALT-D / C03** | cobertura intermediária | E02 + E04 + E08 | efluente roteado | 3 |
| **HEC-03 / ALT-E / C02** | cobertura ampliada | E02 + E04 + E12 | efluente roteado | 4 |
| **HEC-04** | extensão estrutural | ALT-J + GU1 | efluente roteado + lateral do Guaporé, sem dupla contagem | 5 |
| **HEC-05** | extensão lateral | ALT-J + FQ2 | efluente roteado + lateral do Forqueta | 6 |
| **HEC-06** | sensibilidades de rede | C04, C05, FQ1 e combinações selecionadas | entradas próprias, com saturação/galgamento | 7 |

Os eixos E02 e E04 são os indicados porque, conforme `claude_altura_admissivel_revisada.csv`,
são os únicos **sem interferência da cascata existente** até o teto técnico de 120 m na
triagem atual. E08 e E12 continuam condicionados às usinas Castro Alves e 14 de Julho.
O GU1 deve ser desagregado da parcela residual do Antas antes de receber uma afluência
própria; o Forqueta entra apenas como lateral no trecho de Estrela. O primeiro cenário
com obra é HEC-01, não HEC-03 nem a carteira ALT-J.

## 9. Calibração

**Alvo:** reproduzir a cota máxima observada em Estrela e a extensão da mancha de 2024.

**Referências disponíveis:**
- `mancha_v3_1.shp` — mancha observada do evento;
- raster HAND/MGB do mapa de perigo do RS;
- marcas históricas da nota técnica da UFRGS (Moraes *et al.*, 2024), que traz a série consistida 1939–2023 e resolve a inconsistência entre marcas físicas e observações sistemáticas.

**Métricas:** erro na cota de pico (alvo ≤ 0,3 m), *Critical Success Index* da mancha (alvo ≥ 0,7), Nash‑Sutcliffe se houver hidrograma observado.

**Parâmetro de ajuste principal:** o Manning da planície e a profundidade sintética do canal. Recomenda‑se calibrar a profundidade primeiro, contra a cota, e só depois o Manning, contra a extensão da mancha.

## 10. O que este modelo entrega para o restante do estudo

1. **Curva‑chave em Estrela** — converte as cotas históricas em vazão, o que hoje falta e trava a análise de frequência.
2. **Vazão sem dano relevante** — hoje estimada em 4.000 m³/s sem base; o modelo define o valor real.
3. **Perfis de linha d'água por cenário** — insumo direto da figura de divisão de quedas e da comunicação com o município.
4. **Cotas de inundação por edificação** — base da curva cota‑dano do Eixo 3, quando cruzada com o cadastro.

---

### Referência

DOMENEGHETTI, A. On the use of SRTM and altimetry data for flood modeling in data‑sparse regions. *Water Resources Research*, v. 52, n. 4, p. 2901–2918, 2016.

---

# 11. INSUMOS LEVANTADOS — tabelas prontas

Gerados por `07_python/claude_07_insumos_hecras1d.py`. Geometrias em `claude_hecras_eixo.gpkg` (camadas `eixo_rio`, `secoes`, `travessias`, `confluencias`), prontas para o QGIS e o RAS Mapper.

## 11.1 Eixo e estaqueamento

| Item | Valor |
|---|---:|
| Extensão do trecho contratado | **39,40 km** |
| Cota do talvegue — montante | 22,0 m |
| Cota do talvegue — jusante | 13,5 m |
| Desnível total | 8,5 m |
| Declividade média | **0,216 m/km** (2,16 × 10⁻⁴ m/m) |
| Sub-trecho detalhado (área LiDAR) | 16,33 km² |

Estaqueamento a cada 50 m em `claude_hecras_eixo_rio.csv`, com as duas convenções: `dist_montante_m` cresce para jusante e `estaca_ras_m` cresce para montante, como o HEC‑RAS espera.

> O traçado do KMZ vinha de jusante para montante e foi invertido automaticamente, com verificação pela cota das extremidades.

## 11.2 Seções transversais

**102 seções propostas**, sendo 37 no sub-trecho detalhado.

| Sub-trecho | Espaçamento | Largura da seção |
|---|---:|---:|
| Detalhado (área LiDAR + 500 m) | 200 m | 3.000 m |
| Estendido | 500 m | 4.000 m |

Locação, orientação e extremidades em `claude_hecras_secoes.csv`. As seções são traçadas perpendicularmente ao eixo local; **devem ser conferidas e ajustadas manualmente** nas curvas acentuadas e nas confluências, onde a perpendicular ao eixo não é a direção correta do escoamento.

## 11.3 Travessias

| Tipo | Identificação | Estaca RAS | Dist. montante | Cota amostrada | Talvegue local | Conferir |
|---|---|---:|---:|---:|---:|:--:|
| Rodovia estadual | S/I | 18.762 m | 20,64 km | 14,0 m | 14,0 m | não |
| Rodovia estadual | S/I | 16.933 m | 22,47 km | 24,5 m | 14,0 m | **sim** |
| **Rodovia federal** | **BR‑386** | 13.099 m | 26,30 km | 14,0 m | 14,0 m | não |
| Rodovia estadual | RS‑130 | 8.367 m | 31,04 km | 14,0 m | 14,0 m | não |

Três das quatro travessias caem no sub-trecho detalhado. A **BR‑386** é a travessia crítica — é o eixo de transporte cujo bloqueio isola a região.

Duas observações:

- A cota amostrada de 14,0 m repete‑se porque o MDE registra a **superfície da água**, não o leito nem o tabuleiro. Serve apenas para localizar; **a cota de tabuleiro, o vão e a geometria dos encontros precisam vir do cadastro do Eixo 1**.
- A travessia em 22,47 km tem cota 10,5 m acima do talvegue local e está sinalizada para conferência — o ponto de interseção pode estar fora do leito, ou tratar‑se de greide de aterro sobre a planície.

## 11.4 Confluências e contribuições laterais

| Tributário | Área de drenagem | % da bacia em Estrela | Estaca RAS | Dist. montante |
|---|---:|---:|---:|---:|
| **Rio Forqueta** | 2.844,8 km² | **14,63 %** | 23.675 m | 15,73 km |
| Arroio Boa Vista | 576,5 km² | 2,97 % | 36.604 m | 2,80 km |
| Arroio Sampaio | 254,8 km² | 1,31 % | 9.975 m | 29,43 km |
| Arroio Estrela | 241,0 km² | 1,24 % | 17.899 m | 21,50 km |
| Arroio Grande | 60,9 km² | 0,31 % | 26.823 m | 12,58 km |
| Arroio do Meio | 24,3 km² | 0,13 % | 24.823 m | 14,58 km |

O Rio Forqueta responde por quase 15% da bacia e deve entrar como **contribuição lateral concentrada**, não diluída. Os demais somam 5,96%.

## 11.5 Condições de contorno

| Posição | Tipo | Estaca RAS | Área de drenagem | Fonte |
|---|---|---:|---:|---|
| Montante | *flow hydrograph* | 39.402 m | 19.440 km² | Hidrograma do evento; nos cenários com barragem, o efluente roteado |
| Jusante | *normal depth* | 0 m | 23.699 km² | S = 6,3 × 10⁻⁵ m/m |
| Laterais | *lateral inflow* | 6 pontos | — | Hidrogramas escalados por área |

### Alerta sobre a condição de jusante

A declividade dos últimos 10 km é de **6,3 × 10⁻⁵ m/m** — obtida por regressão sobre a cota bruta, porque o talvegue forçado a monotônico ficou **exatamente plano** e produziria `normal depth` com S = 0, o que o HEC‑RAS não aceita.

Uma declividade dessa ordem significa que **o nível em Estrela pode ser governado pelo remanso de jusante**, não pela capacidade local do canal. Três providências:

1. testar a sensibilidade do nível em Estrela à condição de jusante, variando S em uma ordem de grandeza;
2. considerar estender o modelo até a foz, ou impor nível variável no tempo;
3. tratar o resultado como **não confiável** até que haja curva‑chave medida ou seção topobatimétrica no limite de jusante.

## 11.6 Arquivos gerados

| Arquivo | Conteúdo |
|---|---|
| `claude_hecras_eixo_rio.csv` | Estaqueamento a cada 50 m, com cota bruta e talvegue |
| `claude_hecras_secoes.csv` | 102 seções com locação, orientação e extremidades |
| `claude_hecras_travessias.csv` | 4 travessias, com verificação de coerência de cota |
| `claude_hecras_confluencias.csv` | 6 tributários com área de drenagem |
| `claude_hecras_contornos.csv` | Condições de contorno consolidadas |
| `claude_hecras_eixo.gpkg` | Geometrias para QGIS / RAS Mapper |

## 11.7 O que ainda falta para montar o modelo

| Insumo | Situação | Origem |
|---|---|---|
| Cota de tabuleiro e vão das pontes | **ausente** | Eixo 1 — cadastro de infraestrutura |
| Seções topobatimétricas | **ausente** | Eixo 1 — 20 seções previstas |
| Batimetria do canal | **ausente** | Eixo 1; provisoriamente, seção sintética por Manning (§6) |
| Curva‑chave em Estrela | **ausente** | Eixo 1 — 10 medições de vazão |
| Séries de vazão ANA | **não baixadas** | `02_R/01_baixa_dados_ana.R` |
| Diques e aterros existentes | não levantado | cadastro municipal / LiDAR |
| Rugosidade por uso do solo | a definir | MapBiomas ou levantamento |

Sem os quatro primeiros, o modelo roda mas **não calibra**.
