# Relatório EUROCLIMA — figuras, narrativa e referências obrigatórias

O relatório será documentado de forma didática no site Quarto versionado no
GitHub, seguindo o modelo do [tutorial TRIGRS](https://sedec-dpm-cgnat.github.io/tutorial-trigrs/).
Cada capítulo deve explicar o problema, mostrar o método, apresentar a figura
ou tabela correspondente, registrar limitações e indicar as referências
bibliográficas completas.

## Sequência metodológica que deve aparecer no relatório

1. **Diagnóstico geomorfológico preliminar:** MDE, rede de drenagem, áreas de
   contribuição, HAND e comparação com a mancha observada de 2024.
2. **Hidrologia:** séries ANA/UFRGS, hidrograma do evento, vazões de projeto,
   incertezas e cenários de afluência.
3. **Alternativas de reservatório:** eixos, divisão de quedas, CAVs, remanso,
   alturas admissíveis e SINV.
4. **Hidráulica 1D:** seções, pontes, diques, confluências, condições de
   contorno, calibração e simulação dos cenários no HEC-RAS 1D.
5. **Exposição e danos:** municípios, setores censitários, população,
   domicílios, edificações, profundidade/duração e curva cota–dano.
6. **Seleção:** comparação de redução de danos, energia, custo, risco,
   reassentamento, ambiente, segurança e incerteza.

O HAND não deve ser apresentado como substituto do HEC-RAS. Ele é um produto
preliminar de triagem baseado no relevo e em uma curva-chave sintética de
Manning. O HEC-RAS 1D é o modelo hidráulico de referência para os resultados
finais do estudo.

## Figuras mínimas

| Figura | Conteúdo | Estado/fonte |
|---|---|---|
| 1 | Localização da bacia, corredor e trecho HEC-RAS 1D | GIS a compor |
| 2 | MDE, drenagem, HAND e mancha observada de maio de 2024 | HAND preliminar disponível |
| 3 | Perfil longitudinal e divisão de quedas com todas as alternativas estudadas | `VALIDACAO/DIVISAO_QUEDAS_REVISADA.png` |
| 4 | Zoom E02/E04, Castro Alves e trecho intermediário | `VALIDACAO/DIVISAO_QUEDAS_ZOOM_E02_E04_CASTRO.png` |
| 5 | Zoom da cascata Monte Claro–Castro Alves–14 de Julho | `VALIDACAO/DIVISAO_QUEDAS_ZOOM_CASCATA_ANTAS.png` |
| 6 | Divisão de quedas comparando ALT-A, ALT-D, ALT-E/C02, ALT-I, C04 e pontos exploratórios | `VALIDACAO/DIVISAO_QUEDAS_ALTERNATIVAS.png` |
| 7 | CAV oficial das UHEs existentes | `VALIDACAO/CAV_SNIRH_CURVAS.svg` |
| 8 | CAV dos 12 eixos novos, com classe de confiabilidade | gerar a partir da base única |
| 9 | Hidrogramas sem barragem, C01–C05 e detalhe de C02 | `figuras/14_hidrogramas_natural_vs_cascatas.png`; `figuras/15_hidrograma_natural_vs_C02.png` |
| 10 | Geometria 1D: seções, pontes, diques e condições de contorno | criar com HEC-RAS 1D |
| 11 | Perfil de linha d’água e manchas HEC-RAS 1D por cenário | criar após modelagem |
| 12 | Curva cota–dano e EAD | criar após integração de exposição |
| 13 | Comparação custo × dano evitado × energia × incerteza | criar na síntese |
| 14 | Mapa final da alternativa recomendada/selecionada | somente após HEC-RAS 1D e danos |
| 15 | Perfil e coordenadas de pontos exploratórios CA2, MC2, 14J2 e EST1 | `VALIDACAO/PERFIL_EIXOS_EXPLORATORIOS.png`; `GIS/eixos_exploratorios_propostos.kmz` |
| 16 | Planta didática do conjunto inicial para o TR: E02/E04, E08, E12, GU1 e Forqueta | `VALIDACAO/MAPA_ALTERNATIVAS_PONTO_PARTIDA_TR.png` |
| 17 | Perfil didático da cascata, envelopes de altura admissível e sequência HEC-00–HEC-06 | `VALIDACAO/PERFIL_ALTERNATIVAS_PONTO_PARTIDA_TR.png` |

E02 e E04 são candidatos prioritários na triagem, mas a expressão “alternativa
selecionada” só deve ser usada depois da validação hidráulica, dos danos,
custos e restrições socioambientais.

## Referências

O site terá uma página central `referencias.qmd` e referências também no final
de cada capítulo quando necessário. A lista deverá incluir, no mínimo:

- artigos e manuais da metodologia HAND e da curva-chave/Manning;
- RENNÓ et al. (2008), NOBRE et al. (2011) e GOERL et al., *O modelo HAND
  como ferramenta de mapeamento de áreas propensas a inundar*, XX Simpósio
  Brasileiro de Recursos Hídricos, disponível em
  <https://files.abrhidro.org.br/Eventos/Trabalhos/60/PAP022598.pdf>;
- artigo de referência para a reconstrução/estimativa de CAV e batimetria;
- Manual de Inventário Hidrelétrico da EPE e fórmulas SINV utilizadas;
- dados e metadados ANA/SNIRH, ONS, ANEEL e CERAN;
- séries e revisão histórica da UFRGS/ANA;
- ANADEM e documentação dos MDEs;
- Atlas de Desastres do MDR;
- malhas, setores censitários e bases IBGE;
- SINAPI/CUB-RS e demais fontes de custos;
- documentação oficial do HEC-RAS 1D;
- legislação, normas de segurança de barragens, licenciamento e proteção e
  defesa civil aplicáveis.

Nenhuma figura, número ou afirmação metodológica entra no site sem fonte,
data, unidade, sistema de referência e classificação de incerteza.
