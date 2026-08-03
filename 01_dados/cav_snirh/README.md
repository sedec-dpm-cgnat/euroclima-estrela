# Curvas Cota × Área × Volume — SNIRH/ANA

## Fonte

Registro de metadados da Agência Nacional de Águas e Saneamento Básico (ANA):

<https://metadados.snirh.gov.br/geonetwork/srv/api/records/b8f0487a-df73-4f8d-8b22-bb49cf9f3683>

O registro é intitulado **Cota x Área x Volume dos Reservatórios de Usinas
Hidrelétricas** e informa que os pacotes podem conter a planilha CAV
atualizada, o relatório final de batimetria e um geodatabase com dados
geográficos do reservatório.

Pacotes baixados e preservados nesta pasta:

| Usina | Pacote original |
|---|---|
| 14 de Julho | <https://metadados.snirh.gov.br/files/b8f0487a-df73-4f8d-8b22-bb49cf9f3683/14_de_Julho.zip> |
| Castro Alves | <https://metadados.snirh.gov.br/files/b8f0487a-df73-4f8d-8b22-bb49cf9f3683/Castro_Alves.zip> |
| Monte Claro | <https://metadados.snirh.gov.br/files/b8f0487a-df73-4f8d-8b22-bb49cf9f3683/Monte_Claro.zip> |

As planilhas foram extraídas para `planilhas_cav/`. Os ZIPs não foram
alterados. A importação é reproduzida por
`05_MODELAGEM/07_python/24_importa_cav_snirh.py`.

## Conteúdo produzido

- `curvas/cav_snirh_consolidada.csv`: 3.700 registros, cota a cada 0,10 m,
  com cota no Sistema Local (SL), cota no Sistema Geodésico Brasileiro (SGB),
  área e volume acumulado;
- `curvas/cav_14_de_julho.csv`, `cav_castro_alves.csv` e
  `cav_monte_claro.csv`: recortes por usina;
- `cav_snirh_ficha_tecnica.csv` e `.json`: níveis operacionais, áreas, volumes,
  vazões e datas de atualização extraídos da ficha técnica;
- `05_MODELAGEM/06_resultados/tabelas/comparacao_cav_snirh_projeto.csv`:
  comparação com a cota indicada pelo MDE no projeto;
- `05_MODELAGEM/06_resultados/tabelas/volume_deplecionamento_cav_snirh.csv`:
  volume potencial de espera para 1, 2, 3, 5, 8, 10 e 15 m de depleção;
- `05_MODELAGEM/06_resultados/VALIDACAO/CAV_SNIRH_CURVAS.svg`: figura de
  controle das seis curvas.

## Referencial vertical e cautelas

Os níveis normais da ficha técnica são apresentados em **Sistema Local**.
Por isso, a depleção é calculada na curva SL. A planilha também traz a cota
SGB; o deslocamento no nível normal é de aproximadamente 0,07 m em 14 de
Julho, 0,15 m em Castro Alves e 0,13 m em Monte Claro.

A cota `cota_terreno_m` usada no projeto foi comparada nos dois referenciais,
mas o datum vertical do MDE ainda precisa ser confirmado documentalmente.
Assim, a comparação cota-MDE × CAV é diagnóstica, não uma calibração do MDE.

## Cobertura encontrada

Neste registro do SNIRH foram localizados pacotes para 14 de Julho, Castro
Alves e Monte Claro. Não foram localizados, na busca do registro, pacotes com
os nomes Foz do Prata, Passo do Meio, Serra Cavalinhos, Jararaca ou Cotiporã.
Isso deve ser tratado como **ausência de pacote neste registro**, e não como
prova de inexistência de CAV em outras bases da ANA, ONS ou CERAN.

## Interpretação inicial

As curvas oficiais destravam a análise de deplecionamento para as três UHEs
principais. Elas devem substituir a estimativa sintética do MDE para essa
finalidade. A aplicação operacional ainda requer níveis em tempo real,
regras de rebaixamento e reenchimento, restrições de geração, segurança de
barragem, remanso e simulação hidrológica/hidráulica da cascata.
