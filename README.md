# EUROCLIMA+ / AECID — Estudo integrado de alternativas para redução do risco de inundação em Estrela/RS

Análises técnicas de apoio à elaboração do Termo de Referência do componente técnico do projeto EUROCLIMA+ no Rio Grande do Sul (bacia do Taquari‑Antas).

**Secretaria Nacional de Proteção e Defesa Civil — SEDEC/MIDR**
Departamento de Prevenção e Mitigação de Desastres — DPM

> **Aviso.** Todos os resultados aqui são **preliminares**, de ordem de grandeza, destinados a orientar o escopo e o preço da contratação. Não substituem os estudos a serem contratados. Parâmetros econômicos e o hidrograma de referência ainda não estão calibrados — ver as seções de limitações em cada documento.

---

## O que este repositório contém

| Pasta | Conteúdo |
|---|---|
| `01_dados/cav` | Eixos delineados, curvas cota‑área‑volume, geometria e custos das barragens, topologia das cascatas |
| `01_dados/gis_derivado` | Bacias contribuintes, reservatórios, manchas de inundação (GeoPackage) |
| `02_R` | Análises em R — hidrologia, roteamento, alternativas, custo‑benefício, uso múltiplo |
| `06_resultados` | Relatórios, tabelas e figuras |
| `07_python` | Processamento geoespacial — delineação D8, HAND, geometria de barragens |

## Pipeline

```
07_python/10_eixos_cascata.py       # lê os eixos do KMZ, delineia, CAV, geometria, topologia
07_python/08_manchas_hand.py        # manchas de inundação com e sem barragem (HAND + Manning)
07_python/09_perfil_divisao_quedas.py  # perfil longitudinal do talvegue
07_python/49_cartografia_publica.py # mapas PNG contextualizados e mapa Leaflet

02_R/00_config.R                    # parâmetros do estudo
02_R/01_baixa_dados_ana.R           # séries fluviométricas ANA/HidroWeb
02_R/02_volume_amortecimento.R      # volume de amortecimento necessário
02_R/03_roteamento_puls.R           # roteamento de reservatório
02_R/05_analise_alternativas.R      # universo de alternativas + custo‑benefício
02_R/06_sensibilidade.R             # sensibilidade ao dano de referência
02_R/07_comportas_uso_multiplo.R    # vertedouro com comportas + geração hidrelétrica
```

O pipeline é **genérico**: basta acrescentar eixos ao KMZ e rodar `10_eixos_cascata.py` novamente — a numeração, a topologia e as curvas são refeitas automaticamente.

Os mapas de comunicação são gerados por `49_cartografia_publica.py`. A planta regional, as pranchas de ponto de partida, os mapas de Forqueta, Guaporé e HAND incorporam norte, escala, municípios, rodovias e a rede hidrográfica BHO/ANA. O mesmo script gera o mapa interativo em `06_resultados/GIS/mapa_interativo_alternativas.html`, com base de ruas OpenStreetMap, pop-ups e camadas ativáveis. A base OSM é apenas cartográfica; as geometrias analíticas permanecem nas fontes locais do projeto.

Para retomar a execução pelo outro ambiente Codex, use o [prompt de continuidade do Saulo](PROMPT_CONTINUIDADE_SAULO_CODEX.md). Ele contém o estado técnico, a matriz HEC-RAS 1D, as salvaguardas de dados e o roteiro para o Termo de Referência.

## Eixos avaliados

Doze eixos, numerados de montante para jusante (E01 a E12). Área de drenagem em Estrela: 19.440 km².

| Código | Área controlada | Área incremental | Cota do eixo | Eixos a montante |
|---|---:|---:|---:|---:|
| E01 | 2.549 km² | 2.549 km² | 72,5 m | 0 |
| E02 | 3.591 km² | 3.591 km² | 293,0 m | 0 |
| E03 | 3.772 km² | 181 km² | 149,5 m | 1 |
| E04 | 7.498 km² | 7.498 km² | 239,0 m | 0 |
| E05 | 7.923 km² | 425 km² | 167,0 m | 1 |
| E06 | 8.159 km² | 661 km² | 149,5 m | 2 |
| E07 | 8.174 km² | 676 km² | 149,5 m | 3 |
| E08 | 11.951 km² | 862 km² | 148,0 m | 6 |
| E09 | 12.330 km² | 1.241 km² | 106,0 m | 7 |
| E10 | 12.778 km² | 1.689 km² | 71,5 m | 8 |
| E11 | 15.457 km² | 1.819 km² | 57,5 m | 10 |
| E12 | 15.760 km² | 2.122 km² | 47,0 m | 11 |

Eixos independentes (sem outro eixo a montante): **E01, E02 e E04**.

## Dados de entrada

- Modelo digital de elevação e direções de fluxo D8 (28,6 m) — base do projeto
- Base Hidrográfica Ottocodificada — ANA
- Malha municipal — IBGE
- Série consistida de cotas do rio Taquari em Lajeado (1939–2023) — Moraes, Collischonn, Buffon & Eckhardt (2024)

## Requisitos

- Python com GDAL, geopandas, scipy (ambiente do QGIS 3.44 serve)
- R ≥ 4.4 com `data.table`, `ggplot2`, `sf`, `terra`

## Referências

MORAES, S. R.; COLLISCHONN, W.; BUFFON, F. T.; ECKHARDT, R. R. *Revisão e consolidação da série histórica dos níveis das cheias do rio Taquari em Lajeado de 1939 a 2023.* Porto Alegre, 2024.

NOBRE, A. D. et al. Height Above the Nearest Drainage — a hydrologically relevant new terrain model. *Journal of Hydrology*, v. 404, 2011.
