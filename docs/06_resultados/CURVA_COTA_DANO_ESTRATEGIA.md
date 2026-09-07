# Estratégia para a curva cota–dano e base territorial única

**Estado:** metodologia preliminar, pronta para receber a malha do IBGE e dados locais de custo.

## Decisão metodológica

Não há uma base pública nacional única que entregue, simultaneamente, valor de mercado de cada imóvel, geometria do imóvel e série histórica de perdas por setor censitário. A curva será construída em camadas, com cada fonte respondendo por uma pergunta diferente:

1. **Exposição espacial — IBGE:** malha definitiva de setores censitários 2022, população, domicílios, situação urbana/rural, área e agregados do universo.
2. **Estoque físico — IBGE + cadastro local:** número de domicílios e classes construtivas; área construída, padrão e cadastro imobiliário devem ser solicitados às prefeituras quando disponíveis.
3. **Custo de reposição — SINAPI/mercado local:** custo por tipologia e área, corrigido para a data-base do estudo. Não deve ser confundido com preço de venda do terreno ou do imóvel.
4. **Atividade econômica e contexto — IpeaGEO/IBGE:** renda, estrutura socioeconômica, uso do território e indicadores municipais para estratificar a exposição e preencher lacunas.
5. **Perda observada — Atlas Digital de Desastres:** danos materiais e prejuízos declarados para calibrar a ordem de grandeza e a distribuição espacial. O Atlas não é tratado como dano evitável automaticamente.

O estudo do Ipea sobre índices de preços para imóveis é útil como orientação: preço de habitação é heterogêneo, depende de atributos estruturais e de vizinhança e, para escala fina, exige cadastro municipal, base cartorial ou transações. Por isso, a primeira curva será de **dano esperado/reposição**, não de valor de mercado puro.

## Como a curva será calculada

Para cada cenário de cota ou profundidade:

1. gerar a mancha hidráulica ou o raster de profundidade;
2. cruzar a mancha com os setores censitários e, quando possível, com edificações/CNEFE/cadastro municipal;
3. estimar domicílios, população e classes de uso atingidos;
4. aplicar custo de reposição por classe e função de dano profundidade–uso;
5. separar dano direto, prejuízo público, prejuízo privado, interrupção e perdas humanas;
6. calibrar a ordem de grandeza com o Atlas, informando cobertura e subdeclaração;
7. produzir curva cota–dano com intervalo baixo/base/alto, nunca uma cifra única sem incerteza.

Uma forma inicial é:

`D(z) = Σ setor, classe [exposição × custo_reposição × função_dano(profundidade)] + prejuízos públicos + prejuízos privados`

O benefício de cada barragem será `D_sem_medida(z) – D_com_medida(z)`, obtido por simulação hidráulica/operativa. Não será calculado por proporção simples entre hm³ armazenados e R$ 2.500 milhões.

## O que já está consolidado

- `tabelas/atlas_danos_municipios.csv`: três recortes — maio/2024 hidrológico, 2024 hidrológico e histórico hidrológico — para os 19 municípios do corredor.
- No recorte `2024_hidrologico`, a extração soma R$ 234,4 milhões em `danos_economicos_atlas`; no recorte estrito de maio/2024, R$ 29,0 milhões. Esses valores são pisos dos campos econômicos preenchidos: vários registros têm danos humanos, mas campos monetários vazios.
- `GIS/02_GPKG_MESTRE/euroclima_master.gpkg`: camadas de eixos, bacias, usinas, reservatórios, manchas, perfil e danos municipais.
- `GIS/03_SHP_ENTREGA`: exportações SHP em EPSG:31982.
- `GIS/04_KMZ_ENTREGA`: três temas KMZ para inspeção visual.

## Campos mínimos para a próxima versão

`cod_setor`, `municipio`, `area_setor_km2`, `populacao`, `domicilios`, `situacao`, `area_domiciliada_km2`, `profundidade_max_m`, `domicilios_expostos`, `custo_reposicao_base`, `dano_direto_base`, `prejuizo_publico`, `prejuizo_privado`, `fonte`, `data_base`, `qualidade`.

## Fontes a baixar/solicitar

- IBGE — [Malhas de setores censitários e divisões intramunicipais](https://www.ibge.gov.br/geociencias/organizacao-do-territorio/malhas-territoriais/26565-malhas-de-setores-censitarios-divisoes-intramunicipais.html) e [agregados por setores do Censo 2022](https://www.ibge.gov.br/estatisticas/sociais/trabalho/22827-censo-demografico-2022.html).
- Ipea — [IpeaGEO: bases](https://portalantigo.ipea.gov.br/ipeageo/bases.html) e [revisão sobre índices de preços para imóveis](https://portalantigo.ipea.gov.br/agencia/images/stories/PDFs/boletim_regional/111125_boletimregional6_cap3.pdf).
- Atlas — [downloads oficiais](https://atlasdigital.mdr.gov.br/paginas/downloads.xhtml).

## Limites

O setor censitário é uma unidade de agregação, não o lote ou o imóvel. A interseção espacial distribui exposição dentro do setor e precisa ser refinada por edificações, cadastro municipal ou vistoria. Valores declarados no Atlas também podem ter campos vazios, diferenças de cobertura e datas de registro distintas; por isso cada soma deve permanecer acompanhada do recorte e da fonte.
