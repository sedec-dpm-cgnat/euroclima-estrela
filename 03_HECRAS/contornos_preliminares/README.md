# Contornos preliminares do HEC-RAS 1D

Este diretório contém o manifesto da preparação dos casos HEC-00 e HEC-01.
Ainda não há arquivos nativos de projeto, geometria ou plano HEC-RAS porque
faltam seções topobatimétricas, cadastro de pontes, dados de jusante e séries
efluentes por nó.

O produto principal é `manifesto_contornos_hecras.csv`. A auditoria completa,
com o fechamento de áreas e as regras contra dupla contagem, está em:

`06_resultados/VALIDACAO/AUDITORIA_CONTORNOS_HECRAS.md`

O caso prioritário continua sendo:

- HEC-00: situação atual, sem novas barragens;
- HEC-01: E02 + E04, após gerar os efluentes nodais calibrados.

Não usar as séries agregadas em Estrela como se fossem simultaneamente entrada
de montante e afluências laterais.
