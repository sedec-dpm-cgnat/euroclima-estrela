# Plano de Ação — Fechamento do TR e Simulações Preliminares

**Projeto EUROCLIMA+ / AECID — Estudo técnico Estrela/RS**
Atualizado em 07/09/2026

---

## Situação atual

| Item | Estado |
|---|:--:|
| Macro Logframe (plano de trabalho) | ✅ fechado em 20/07/2027 |
| Ficha de Formulação (PT/ES) | ✅ fechada |
| Anexo II — Presupuesto | ✅ fechado (€ 300.000) |
| Descritivo das Atividades (5 eixos) | ✅ redigido |
| Base GIS | ⚠️ existe, mas com CRS heterogêneos e nomenclatura duplicada |
| TR REV. 0A | ⚠️ seções 1–4.1 boas; 3.2 em diante era resíduo de outro projeto |
| **TR REV. 0B (minuta)** | ✅ **redigida — `06_resultados/TR_MINUTA_REV0B.md`** |
| Delineação das barragens + CAV sintética de triagem | ✅ concluída |
| CAV oficial SNIRH/ANA | ✅ 3 UHEs; completar demais reservatórios |
| CAV dos 12 eixos novos | ✅ MDE natural, interpolação monotônica a 1 m |
| Simulação preliminar de amortecimento | ✅ concluída (Puls) |
| Modelo HEC-RAS 1D | ⚠️ insumos preliminares e auditoria de contornos prontos; projeto/calibração pendentes |
| FloodAdapt | ⏳ a montar |
| Site Quarto documentando a análise no GitHub | ✅ publicado em `sedec-dpm-cgnat.github.io/euroclima-estrela-site` |

---

## FASE 1 — Fechar o TR (esforço: 3 a 5 dias)

### 1.1 Decidir os 10 pontos abertos
Estão listados no apêndice da minuta. **Os três primeiros são os críticos** — determinam o preço do Eixo 1, que é 49% do contrato:

| # | Divergência | Descritivo | Base GIS |
|---|---|---:|---:|
| 1 | Trecho de modelagem | 40 km | **51,7 km** |
| 2 | Sub-trecho refinado | 10 km | **35,9 km** |
| 3 | Área do voo LiDAR | 16 km² | **24,2 / 48,2 / 139,4 km²** |

**Recomendação:** medir a extensão real do trecho urbano crítico em Estrela e fixar. Um voo LiDAR de 139 km² a 20 pts/m² custa da ordem de 4 a 8× um voo de 16 km² — a diferença sozinha pode inviabilizar o orçamento de € 133.875.

**Ação:** abrir `Trecho Modelagem.shp`, `Refinamento.shp` e os polígonos de levantamento no QGIS, decidir o recorte definitivo, salvar como `AREA_ESTUDO_DEFINITIVA.gpkg` e anexar ao TR como vinculante.

### 1.2 Sanear a divergência orçamentária de € 1.375
Presupuesto: € 273.875 · Logframe (aba *Actividades-Español*): € 272.500. Fixar um valor.

### 1.3 Consolidar a base GIS
Harmonizar tudo em **EPSG:31982**. Hoje convivem EPSG:31983 (os três eixos de barragem), 32722, 20822 (Aratu — datum obsoleto) e arquivos sem CRS. Script pronto em `07_python/`.

### 1.4 Revisar e converter a minuta
Ler `TR_MINUTA_REV0B.md`, ajustar, e gerar o DOCX final com a identidade visual do EUROCLIMA+ (logos já disponíveis em `Espanha/logos/`).

### 1.5 Anexar a Nota Técnica Preliminar
`06_resultados/NOTA_TECNICA_PRELIMINAR_BARRAGENS.md` como ANEXO VII. É o que justifica tecnicamente o enquadramento do Eixo 3 como análise de alternativas híbridas.

---

## FASE 2 — Consolidar a hidrologia (esforço: 2 a 4 dias)

### 2.1 Baixar as séries da ANA
```bash
Rscript 02_R/01_baixa_dados_ana.R
```
Postos configurados: 86870000 (Lajeado antigo), 86879300 (Estrela/Lajeado atual), 86510000 (Muçum), 86720000 (Encantado), 86560000, 86440000.

### 2.2 Digitalizar a série consistida da UFRGS
A nota técnica de Moraes, Collischonn, Buffon & Eckhardt (2024) — em `Referencias/revisao_consolidacao_serie_historica_rio_taquari_lajeado.pdf` — traz a série consistida de cotas máximas anuais de 1939 a 2023 (seções 8 e 9). **É a melhor base disponível** e resolve a inconsistência entre marcas físicas e observações sistemáticas. Digitalizar as tabelas e salvar em `01_dados/serie_consistida_lajeado.csv`.

### 2.3 Recalibrar o hidrograma de referência
Substituir os parâmetros em `02_R/02_volume_amortecimento.R`:
```r
PAR_EVENTO <- list(q_pico = ..., lamina_mm = ..., q_base = ...)
```
pelos valores derivados do evento real de maio/2024. Rodar novamente 02 e 03 — todas as conclusões se atualizam automaticamente.

### 2.4 Curva-chave em Estrela
Estabelecer a relação cota × vazão no posto 86879300 para converter as cotas históricas (incluindo 29,92 m de 1941 e as marcas de 2023/2024) em vazões. Sem isso, o `Q_SEGURA = 4.000 m³/s` permanece uma estimativa.

---

## FASE 3 — Modelo HEC-RAS 1D preliminar (esforço: 5 a 8 dias)

Versões instaladas: **HEC-RAS 6.3.1 e 7.0.1**; **HEC-HMS 4.11 e 4.13**.

O HAND já foi executado como etapa preliminar de triagem geomorfológica e
controle de coerência. Ele orienta o corredor, as primeiras manchas e a
comparação com 2024, mas não substitui o HEC-RAS 1D.

### 3.1 Preparar o terreno
```
Entrada:  GIS/raster/mdr.tif (28,6 m, EPSG:32722)
Saída:    03_HECRAS/Terrain/estrela_terrain.tif  (EPSG:31982)
```
Para a etapa preliminar o MDE de 28,6 m basta para o trecho estendido. O projeto informa que o `mdr.tif` veio do ANADEM, mas essa origem não está registrada nos metadados do arquivo. O recorte público `anadem_taquari_31982.tif` deve ser usado como controle de sensibilidade e contexto, não como segunda fonte independente. Para o trecho urbano/detalhado, usar MDE local de maior resolução e levantamento topográfico-topobatimétrico integrado.

### 3.2 Geometria
- **Trecho prioritário**: aproximadamente 12 km na área urbana de Estrela/Lajeado, dentro do trecho contratado de 39,4 km.
- **Seções 1D**: a cada 200 m no trecho detalhado e 500 m no restante, refinando em pontes, confluências, diques e mudanças de seção.
- **Estruturas**: cadastrar BR-386, ferrovia e travessias urbanas; representar diques e aterros como elementos de seção.
- **Manning**: 0,030 no canal; 0,060 em planície vegetada; 0,12 em área urbana, calibrando contra cotas e mancha de maio/2024.

### 3.3 Condições de contorno
- **Montante**: hidrograma no limite montante (`LimiteMontante.shp`, −29,3764 / −51,8790).
- **Laterais**: hidrogramas dos afluentes já delineados — Rio Forqueta (2.845 km²), Arroio Boa Vista (576 km²), Arroio Estrela (241 km²), Arroio Sampaio (255 km²). O Forqueta entra somente entre o ponto de análise de 19.440 km² e Estrela; o Guaporé (aprox. 2.487 km²) deve ser incluído após a triagem do eixo GU1.
- **Jusante**: *normal depth* com declividade do trecho, ou curva-chave se disponível. Atenção ao remanso do Guaíba/Lago em eventos extremos.

### 3.4 Plano de simulação
| Plano | Cenário |
|---|---|
| P00 | Calibração — evento de maio/2024, situação atual |
| P01 | TR 100 anos, situação atual |
| P02 | TR 100 anos + E02 |
| P03 | TR 100 anos + E04 |
| P04 | TR 100 anos + E02 + E04 |
| P05 | Evento 2024 + E02 + E04 |
| P06 | Evento 2024 + diques na área urbana |

Nos planos com barragem, aplicar como condição de contorno de montante o **hidrograma efluente** já calculado por `03_roteamento_puls.R` (saída em `06_resultados/tabelas/`), evitando modelar a estrutura no HEC-RAS nesta etapa preliminar. O roteiro detalhado está em `06_resultados/CLAUDE/CLAUDE_ROTEIRO_HECRAS_1D.md`.

### 3.5 Calibração
Alvo: reproduzir a mancha de maio/2024. Referências disponíveis:
- `GIS/shapefiles/mancha_v3_1.shp` (24.459 polígonos, mancha RS 2024);
- `Documentos EUROCLIMA+/Espanha/05_MAPA_DE_PERIGO_A_INUNDACAO_PARA_O_RS/` (raster HAND/MGB unificado);
- marcas de cheia da nota técnica da UFRGS.

Métrica: *Critical Success Index* entre mancha simulada e observada.

---

## FASE 4 — FloodAdapt (esforço: 4 a 6 dias)

O FloodAdapt (Deltares) é a ferramenta adequada para a **análise de alternativas e custo-benefício** do Eixo 3 — que é exatamente o que o TR precisa dimensionar. Ele consome resultados de modelo hidrodinâmico e cruza com exposição e funções de dano.

### 4.1 O que o FloodAdapt exige
| Insumo | Situação |
|---|---|
| Modelo hidrodinâmico (SFINCS) | ⏳ a construir — o FloodAdapt usa SFINCS, não HEC-RAS |
| Exposição de edificações (FIAT) | ⏳ derivar do cadastro; provisoriamente OpenStreetMap + CNEFE/IBGE |
| Funções de dano por tipologia | ⏳ adaptar — as *default* são dos EUA (USACE/HAZUS) |
| Valor de reposição das edificações | ⏳ usar SINAPI/CUB-RS por tipologia |
| Modelo digital de elevação | ✅ `mdr.tif` (preliminar) |

### 4.2 Estratégia recomendada
**Não tente rodar FloodAdapt completo nesta etapa preliminar.** O caminho eficiente é:

1. **Agora (preliminar):** HEC-RAS 1D no trecho detalhado para perfis de linha d'água, curva-chave, remanso e cenários de operação + planilha de curvas cota-dano. Esta é a configuração hidrodinâmica adotada neste trabalho.
2. **No contrato:** exigir da CONTRATADA a entrega de um *setup* FloodAdapt operacional, com SFINCS calibrado e/ou confrontado contra os resultados do HEC-RAS 1D. Uma modelagem HEC-RAS 2D não faz parte da linha metodológica atual.

> **Sugestão para o TR:** incluir no Eixo 3, como entregável opcional pontuado na avaliação técnica, a implantação de uma instância FloodAdapt para Estrela. Deltares e o programa EUROCLIMA+ têm histórico de cooperação, o que favorece a aceitação.

### 4.3 Se quiser testar agora
O FloodAdapt tem uma versão *Database Builder*. O caminho mínimo:
```
1. SFINCS model  <- terreno + rugosidade + contornos
2. FIAT exposure <- OSM buildings + tipologia + valor
3. Damage curves <- adaptar JRC Global Flood Depth-Damage (América do Sul)
4. FloodAdapt DB <- Database Builder
```
As funções de dano do **JRC (Huizinga et al., 2017)** têm curva específica para a América do Sul e são a melhor referência pública disponível para o Brasil.

---

## FASE 5 — Curvas cota-dano preliminares (esforço: 3 a 4 dias)

Esta é a peça que falta para fechar o argumento econômico do TR, e pode ser feita **sem** o cadastro de campo:

1. Extrair edificações do **OpenStreetMap** + **CNEFE 2022 (IBGE)** para Estrela.
2. Amostrar a cota do terreno de cada edificação no MDE; assumir soleira 0,3 m acima.
3. Aplicar funções de dano do JRC para a América do Sul, por tipologia.
4. Valorar por **CUB-RS** (residencial/comercial) e SINAPI.
5. Cruzar com as manchas do HEC-RAS por cenário → **dano esperado anual (EAD)**.
6. Comparar EAD entre alternativas → razão benefício-custo preliminar.

Isso permite responder no TR: *"o dano evitado por uma barragem de 80 m justifica seu custo?"* — que é a pergunta que a AECID vai fazer.

---

## Sequência recomendada

```
Semana 1   FASE 1 (fechar TR)          ← desbloqueia a publicação
Semana 2   FASE 2 (hidrologia ANA)     ← consolida os números
Semana 3-4 FASE 3 (HEC-RAS 1D)         ← perfis, curva-chave e cenários
Semana 5   FASE 5 (curvas cota-dano)   ← argumento econômico
Semana 6   Revisão final do TR com os resultados
FASE 4     transferir para o contrato (recomendado)
```

**Caminho crítico:** a FASE 1 não depende das demais. **O TR pode ser publicado ao final da semana 1**, e as simulações servirão para refinar a avaliação das propostas e a fiscalização.

---

## Riscos

| Risco | Prob. | Impacto | Mitigação |
|---|:--:|:--:|---|
| Divergência de escopo (40 vs 51,7 km; 16 vs 139 km²) chega ao mercado | Alta | **Alto** | Fixar no TR com shapefile vinculante (Fase 1.1) |
| Orçamento insuficiente para o LiDAR especificado | Média | Alto | Consulta prévia de mercado antes da publicação |
| Expectativa de que "barragens resolvem" persistir | Média | Alto | Anexar a Nota Técnica Preliminar ao TR (Fase 1.5) |
| Ausência de curva-chave em Estrela | Alta | Médio | Exigir no Eixo 1 as 10 medições de vazão |
| MDE de 28,6 m insuficiente para o trecho urbano | Certa | Médio | Usar `mdr.tif`/ANADEM apenas como contexto; o Eixo 1 deve entregar MDE e topobatimetria de maior resolução |
| Sobreposição com as frentes Haskoning e Eco | Média | Médio | Seção 1.1 do TR delimita; reuniões de articulação |
