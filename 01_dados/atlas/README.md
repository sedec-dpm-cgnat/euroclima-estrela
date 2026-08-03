# Atlas Digital de Desastres — extração do corredor

- Fonte oficial: https://atlasdigital.mdr.gov.br/paginas/downloads.xhtml
- Arquivo processado: `BD_Atlas_1991_2025_v1.0_2026.04.23_Consolidado.csv`
- Data da extração: 2026-07-30
- Municípios: corredor usado no modelo preliminar HAND/perfil, incluindo o trecho até Bom Retiro do Sul e municípios de jusante já modelados.
- Recortes: `maio_2024_hidrologico`, `2024_hidrologico` e `historico_hidrologico`.
- O Atlas registra perdas declaradas/levantadas em formulários municipais. Elas calibram ordem de grandeza e priorização, mas não são automaticamente o dano evitável por uma barragem.
- `danos_economicos_atlas` = dano material + prejuízo total declarado; danos humanos permanecem em campos separados.
- Campos econômicos vazios/zero permanecem zero na soma; os totais monetários são, portanto, um piso de registros preenchidos, não uma estimativa completa do evento.
- A data de recorte é `Data_Evento`; datas de registro podem ser posteriores ao evento. O recorte de maio/2024 é estrito e fica separado de todo 2024.
- O arquivo bruto não foi copiado para o repositório.
