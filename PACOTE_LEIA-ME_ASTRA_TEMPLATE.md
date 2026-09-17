# EUROCLIMA+ / Estrela — pacote de continuidade para Astra

**Data de preparação:** 17 de setembro de 2026

**Finalidade:** permitir que outro GPT Codex/Astra reproduza, audite e avance
nas simulações preliminares e, em seguida, complete o relatório técnico e o
Termo de Referência.

## Ordem de leitura

1. `01_PROMPT_CONTINUIDADE_ASTRA.md` — instruções de continuidade.
2. `02_ESTADO_E_PLANO/HANDOFF.md` — números confiáveis, limitações e bugs já
   corrigidos.
3. `02_ESTADO_E_PLANO/STATUS_ATUAL_PROJETO.md` e `PLANO_DE_ACAO.md`.
4. `03_MODELO_05_MODELAGEM/README.md` e os relatórios em
   `03_MODELO_05_MODELAGEM/06_resultados`.
5. `04_TR_E_CONTEXTO/01_trabalho_limpo/TR_MINUTA_REV0C_LIMPA_HECRAS1D.docx`.

## Organização

- `03_MODELO_05_MODELAGEM`: cópia de trabalho do repositório, com scripts,
  dados derivados, resultados, figuras e site Quarto. Os diretórios temporários
  de QA do DOCX foram excluídos.
- `04_TR_E_CONTEXTO`: minuta limpa REV. 0C, versão histórica 0A e documentos
  do componente Espanha usados para contextualização.
- `05_GIS_E_KMZ`: camadas vetoriais/GPKG/SHP e KMZ selecionadas, além dos KMZ
  originais. As fontes brutas de grande porte estão documentadas, mas não foram
  duplicadas neste pacote.
- `06_INVENTARIO`: inventário de arquivos com tamanho, hash SHA-256, origem,
  finalidade e observações.

## Estado técnico essencial

A seleção de referência em triagem é HEC-01 (E02+E04); HEC-02, HEC-03, HEC-04,
HEC-05 e HEC-06 são alternativas/sensibilidades que precisam ser comparadas.
A vazão de referência e o benefício devem ser definidos no ponto de controle de
Estrela, com conservação explícita das contribuições laterais, inclusive
Forqueta e Guaporé. O HEC-RAS contratado deve ser 1D; 2D só pode aparecer como
complementação aprovada.

Ainda não existe projeto, geometria ou plano nativo HEC-RAS executado. As
manchas HAND são triagem, não substituem a modelagem hidráulica calibrada.

## Segurança e rastreabilidade

Este pacote não contém senhas, tokens, `auth.json`, `.env` ou credenciais de
PostGIS. Os hashes do inventário permitem verificar se uma cópia foi alterada.
Não sobrescreva a minuta original: qualquer revisão deve receber novo sufixo e
ser acompanhada de registro no relatório.
