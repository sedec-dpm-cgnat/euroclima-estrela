# CAVs dos eixos novos — metodologia e controle

## Por que a aproximação é aceitável nesta etapa

Os 12 eixos analisados são pré-estabelecidos e não possuem reservatório
existente no local. Portanto, o MDE representa o relevo natural que seria
submerso, ao contrário do caso de uma UHE existente, em que o MDE normalmente
representa a superfície da água e não informa a batimetria abaixo dela.

A CAV preliminar foi calculada pelo pipeline `10_eixos_cascata.py` a partir da
área conectada inundada e do volume acumulado para níveis de 10 a 120 m, em
passos de 5 m. Os 276 pontos originais foram preservados.

## Densificação e interpolação

O script `27_ajusta_cav_eixos_novos.py` gera 1.332 pontos em passos de 1 m,
sem extrapolar o intervalo original. O método principal é uma interpolação
PCHIP monotônica, que preserva a ordem crescente de área e volume e evita
oscilações artificiais.

Os polinômios de graus 2, 3 e 4 são calculados somente como representação
compacta e teste de sensibilidade. Eles não são automaticamente adotados como
curva operacional quando deixam de ser monotônicos. No diagnóstico cúbico,
por exemplo, a área do E05 e o volume do E10 não permaneceram monotônicos em
todo o intervalo; nesses casos, a PCHIP é obrigatória.

## Saídas

- `06_resultados/tabelas/cav_eixos_novos_interpolada_1m.csv` — curva
  recomendada para interpolação preliminar;
- `06_resultados/tabelas/cav_eixos_novos_ajustes_polinomiais.csv` — erros e
  monotonicidade dos ajustes;
- `06_resultados/tabelas/cav_eixos_novos_modelos.json` — coeficientes e escala
  dos polinômios;
- `06_resultados/tabelas/cav_base_unica.csv` — base única com as três CAVs
  oficiais do SNIRH e os 12 eixos novos;
- `06_resultados/tabelas/catalogo_cavs.csv` — catálogo de fontes e classes de
  confiabilidade.
- `06_resultados/tabelas/validacao_cavs.csv` e `VALIDACAO_CAVS.md` — controle
  de monotonicidade e verificação de ordem de grandeza `dV/dc ≈ área`.

## Classificação de confiabilidade

- **A — CAV oficial SNIRH/ANA:** 14 de Julho, Castro Alves e Monte Claro;
- **B — derivada do MDE natural:** 12 eixos novos, adequada para triagem de
  alternativas, SINV preliminar e comparação de ordem de grandeza;
- **C — sintética sobre reservatório existente:** não deve substituir CAV
  oficial e permanece apenas como sensibilidade onde não houver levantamento.

Mesmo para os eixos novos, a CAV deve ser recalculada na fase de engenharia
com topografia de maior resolução, geologia, remanso, controle de sedimentos,
batimetria do reservatório formado e verificação hidráulica do eixo.
