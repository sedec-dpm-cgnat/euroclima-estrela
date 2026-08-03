# -*- coding: utf-8 -*-
"""Extrai perdas do Atlas Digital de Desastres para o corredor do projeto.

O arquivo bruto do Atlas não é versionado no projeto. Informe ATLAS_CSV ou use o
download temporário padrão. A extração mantém o registro de evento e produz uma
agregação municipal para a curva preliminar cota–dano.
"""
from pathlib import Path
from datetime import date
import os
import pandas as pd

RAIZ = Path(r"C:\Users\cassi\OneDrive\Documents\SEDEC\PROJETO_EUROCLIMA")
DEST = RAIZ / "05_MODELAGEM"
ATLAS_DIR = DEST / "01_dados" / "atlas"
TAB = DEST / "06_resultados" / "tabelas"
ATLAS_DIR.mkdir(parents=True, exist_ok=True)
TAB.mkdir(parents=True, exist_ok=True)

DEFAULT = Path(os.environ.get(
    "TEMP", r"C:\Users\cassi\AppData\Local\Temp"
)) / "BD_Atlas_1991_2025_v1.0_2026.04.23_Consolidado.csv"
SRC = Path(os.environ.get("ATLAS_CSV", str(DEFAULT)))
if not SRC.exists():
    raise FileNotFoundError(
        f"Atlas não encontrado em {SRC}. Baixe o CSV oficial e defina ATLAS_CSV."
    )

CORREDOR = [
    "Muçum", "Roca Sales", "Encantado", "Colinas", "Arroio do Meio",
    "Cruzeiro do Sul", "Lajeado", "Estrela", "Bom Retiro do Sul",
    "Fazenda Vilanova", "Taquari", "Venâncio Aires", "Mato Leitão",
    "Santa Clara do Sul", "Marques de Souza", "Travesseiro", "Capitão",
    "Bom Princípio", "Sério",
]

USE = [
    "Protocolo_S2iD", "Nome_Municipio", "Sigla_UF", "Data_Registro",
    "Data_Evento", "Cod_Cobrade", "tipologia", "descricao_tipologia",
    "grupo_de_desastre", "Cod_IBGE_Mun", "Status", "DH_MORTOS",
    "DH_FERIDOS", "DH_ENFERMOS", "DH_DESABRIGADOS", "DH_DESALOJADOS",
    "DH_DESAPARECIDOS", "DH_total_danos_humanos_diretos",
    "DH_OUTROS AFETADOS", "DM_total_danos_materiais", "PEPL_total_publico",
    "PEPR_total_privado", "PE_PLePR",
]

# O engine Python respeita descrições textuais com quebras de linha, presentes
# em campos do Atlas; o engine C pode ficar preso em registros legados assim.
df = pd.read_csv(
    SRC, sep=";", encoding="latin1", dtype=str, usecols=USE,
    engine="python", on_bad_lines="skip",
)
df = df[(df["Sigla_UF"] == "RS") & df["Nome_Municipio"].isin(CORREDOR)].copy()
df["data_evento"] = pd.to_datetime(
    df["Data_Evento"], format="%d/%m/%Y", errors="coerce"
)
df["data_registro"] = pd.to_datetime(
    df["Data_Registro"], format="%d/%m/%Y", errors="coerce"
)

NUM = [
    c for c in USE
    if c.startswith("DH_") or c.startswith("DM_") or c.startswith("PE")
]
for c in NUM:
    df[c] = pd.to_numeric(
        df[c].astype(str).str.replace(",", ".", regex=False),
        errors="coerce",
    ).fillna(0.0)

hid = df["grupo_de_desastre"].eq("Hidrológico")
df["recorte"] = ""
df.loc[hid, "recorte"] = "historico_hidrologico"
df.loc[hid & df["data_evento"].dt.year.eq(2024), "recorte"] = "2024_hidrologico"
df.loc[
    hid & df["data_evento"].dt.year.eq(2024)
    & df["data_evento"].dt.month.eq(5),
    "recorte",
] = "maio_2024_hidrologico"

# A tabela de eventos inclui somente hidrológicos para não misturar estiagem,
# vendaval e granizo com o dano potencial de cheia.
eventos = df[hid].copy()
eventos["data_evento"] = eventos["data_evento"].dt.strftime("%Y-%m-%d")
eventos["data_registro"] = eventos["data_registro"].dt.strftime("%Y-%m-%d")
eventos = eventos.drop(columns=["Data_Evento", "Data_Registro"])
eventos.to_csv(
    ATLAS_DIR / "atlas_eventos_hidrologicos_corredor.csv",
    index=False, sep=";", decimal=",",
)

recortes = ["maio_2024_hidrologico", "2024_hidrologico", "historico_hidrologico"]
ag = eventos.groupby(["recorte", "Nome_Municipio"], as_index=False).agg(
    eventos_atlas=("Protocolo_S2iD", "count"),
    mortos=("DH_MORTOS", "sum"),
    feridos=("DH_FERIDOS", "sum"),
    enfermos=("DH_ENFERMOS", "sum"),
    desabrigados=("DH_DESABRIGADOS", "sum"),
    desalojados=("DH_DESALOJADOS", "sum"),
    desaparecidos=("DH_DESAPARECIDOS", "sum"),
    afetados_diretos=("DH_total_danos_humanos_diretos", "sum"),
    outros_afetados=("DH_OUTROS AFETADOS", "sum"),
    danos_materiais=("DM_total_danos_materiais", "sum"),
    prejuizo_publico=("PEPL_total_publico", "sum"),
    prejuizo_privado=("PEPR_total_privado", "sum"),
    prejuizo_total=("PE_PLePR", "sum"),
)
ag["danos_economicos_atlas"] = ag["danos_materiais"] + ag["prejuizo_total"]

idx = pd.MultiIndex.from_product(
    [recortes, CORREDOR], names=["recorte", "Nome_Municipio"]
)
agg = ag.set_index(["recorte", "Nome_Municipio"]).reindex(idx).reset_index()
num_out = [c for c in agg.columns if c not in ("recorte", "Nome_Municipio")]
agg[num_out] = agg[num_out].fillna(0.0)
agg["eventos_atlas"] = agg["eventos_atlas"].astype(int)
agg.to_csv(TAB / "atlas_danos_municipios.csv", index=False, sep=";", decimal=",")

readme = f"""# Atlas Digital de Desastres — extração do corredor

- Fonte oficial: https://atlasdigital.mdr.gov.br/paginas/downloads.xhtml
- Arquivo processado: `{SRC.name}`
- Data da extração: {date.today().isoformat()}
- Municípios: corredor usado no modelo preliminar HAND/perfil, incluindo o trecho até Bom Retiro do Sul e municípios de jusante já modelados.
- Recortes: `maio_2024_hidrologico`, `2024_hidrologico` e `historico_hidrologico`.
- O Atlas registra perdas declaradas/levantadas em formulários municipais. Elas calibram ordem de grandeza e priorização, mas não são automaticamente o dano evitável por uma barragem.
- `danos_economicos_atlas` = dano material + prejuízo total declarado; danos humanos permanecem em campos separados.
- O arquivo bruto não foi copiado para o repositório.
"""
(ATLAS_DIR / "README.md").write_text(readme, encoding="utf-8")
print(agg.to_string(index=False))
print("\nEventos:", len(eventos), "| municípios:", eventos["Nome_Municipio"].nunique())
print("Saídas gravadas em", ATLAS_DIR, "e", TAB)
