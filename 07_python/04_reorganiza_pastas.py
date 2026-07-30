# -*- coding: utf-8 -*-
"""
Reorganiza a arvore de diretorios do PROJETO_EUROCLIMA.

Uso:
    python 04_reorganiza_pastas.py           # DRY-RUN: so mostra o que faria
    python 04_reorganiza_pastas.py --aplicar # executa de fato

Estrutura proposta:
    00_GESTAO/            documentos formais, oficios, notas tecnicas, fichas
    01_LOGFRAME/          logframe, POA, presupuesto, ficha de formulacao (finais)
    02_TR/                termo de referencia e anexos
    03_GIS/               base geoespacial (shapefiles, raster, projetos, figuras)
    04_REFERENCIAS/       bibliografia
    05_MODELAGEM/         analises, scripts, HEC-RAS, FloodAdapt  [ja criada]
    06_FRENTES_PARCEIRAS/ Haskoning (governanca) e Eco (financiamento)
    07_APRESENTACOES/     pptx e pdf de apresentacao
    08_DADOS_EXTERNOS/    entregas de terceiros (manchas RS, mapa de perigo)
    _ARQUIVO/             versoes antigas e temporarios
"""
import os, sys, shutil, re
from pathlib import Path

RAIZ = Path(r"C:\Users\cassi\OneDrive\Documents\SEDEC\PROJETO_EUROCLIMA")
ESP  = RAIZ / "Documentos EUROCLIMA+" / "Espanha"
APLICAR = "--aplicar" in sys.argv

NOVAS = ["00_GESTAO", "01_LOGFRAME", "02_TR", "03_GIS", "04_REFERENCIAS",
         "06_FRENTES_PARCEIRAS/Haskoning_Governanca",
         "06_FRENTES_PARCEIRAS/Eco_Financiamento",
         "07_APRESENTACOES", "08_DADOS_EXTERNOS", "_ARQUIVO/versoes_logframe",
         "_ARQUIVO/temporarios"]

# (origem relativa a RAIZ, destino relativo a RAIZ)
MOVIMENTOS = [
    # ---------------------------------------------------------------- gestao
    (ESP / "Oficio ABC EUROCLIMA+.pdf",                       "00_GESTAO"),
    (ESP / "Nota Técnica análise FINATEC.pdf",                "00_GESTAO"),
    (ESP / "Nota Técnica análise Programa EUROCLIMA+ AECID.pdf", "00_GESTAO"),
    (ESP / "Ficha de Ação de Resiliência Climática.pdf",      "00_GESTAO"),
    (ESP / "Estructura de seguimiento_Brasil.docx",           "00_GESTAO"),
    (ESP / "REFLECTION_PAPER_Draft_2024.docx",                "00_GESTAO"),
    (ESP / "Final" / "Carta de Delegação (espanhol).pdf",     "00_GESTAO"),
    (ESP / "Final" / "Carta de Delegação (português).pdf",    "00_GESTAO"),
    (ESP / "PASSOS_FORMAIS.png",                              "00_GESTAO"),
    (ESP / "PASSOS_FORMAIS2.png",                             "00_GESTAO"),

    # -------------------------------------------------------------- logframe
    (ESP / "Final" / "Macro Logframe SEDEC_final_20270720.xlsx",        "01_LOGFRAME"),
    (ESP / "Final" / "Anexo II - Presupuesto 20270720.xlsx",            "01_LOGFRAME"),
    (ESP / "Final" / "Ficha formulación (português) - 20270720.docx",   "01_LOGFRAME"),
    (ESP / "Final" / "Ficha formulación (português) - 20270720.pdf",    "01_LOGFRAME"),
    (ESP / "Final" / "Ficha formulación (español) - 20270720.docx",     "01_LOGFRAME"),
    (ESP / "Final" / "Ficha formulación (español) - 20270720.pdf",      "01_LOGFRAME"),
    (ESP / "ANEXO- Plan Operativo Anual.xlsx",                          "01_LOGFRAME"),
    (ESP / "DESCRITIVO DAS ATIVIDADES.docx",                            "01_LOGFRAME"),
    (ESP / "LOGFRAME_INSTRUCOES.png",                                   "01_LOGFRAME"),

    # versoes antigas do logframe -> arquivo
    (ESP / "Action Logframe design tool_draft_16-12-2025 (1).xlsx", "_ARQUIVO/versoes_logframe"),
    (ESP / "Action Logframe design tool_draft_21-03-2026.xlsx",     "_ARQUIVO/versoes_logframe"),
    (ESP / "Action Logframe design tool_draft_30_04_2026.xlsx",     "_ARQUIVO/versoes_logframe"),
    (ESP / "FICHA FORMULACIÓN_26_01_2026.docx",                     "_ARQUIVO/versoes_logframe"),

    # -------------------------------------------------------------------- TR
    (ESP / "Termo de Referência" / "PROJETO_EUROCLIMA_ESTRELA_TERMO_DE_REFERENCIA_REV_0A.docx", "02_TR"),

    # ------------------------------------------------------------------- GIS
    (ESP / "GIS",      "03_GIS"),
    (ESP / "Figuras",  "03_GIS/figuras_capa"),
    (ESP / "logos",    "03_GIS/logos"),

    # ---------------------------------------------------------- apresentacoes
    (ESP / "Apresentacao",                              "07_APRESENTACOES"),
    (ESP / "Apresentação EUROCLIMA+.pdf",               "07_APRESENTACOES"),
    (ESP / "Actualizacion Euroclima - BR- AECID Abril26.pptx", "07_APRESENTACOES"),

    # ------------------------------------------------------- frentes parceiras
    (RAIZ / "Documentos EUROCLIMA+" / "Holanda_Haskoning", "06_FRENTES_PARCEIRAS/Haskoning_Governanca"),
    (RAIZ / "Documentos EUROCLIMA+" / "Inglaterra_Eco",    "06_FRENTES_PARCEIRAS/Eco_Financiamento"),

    # --------------------------------------------------------- dados externos
    (ESP / "03_MANCHAS_INUNDACAO_PRE_EXISTENTES.zip",        "08_DADOS_EXTERNOS"),
    (ESP / "05_MAPA_DE_PERIGO_A_INUNDACAO_PARA_O_RS",        "08_DADOS_EXTERNOS"),
    (ESP / "05_MAPA_DE_PERIGO_A_INUNDACAO_PARA_O_RS.zip",    "08_DADOS_EXTERNOS"),
    (ESP / "4.2_ARQUIVOS_SIG_v2",                            "08_DADOS_EXTERNOS"),
    (ESP / "4.2_ARQUIVOS_SIG_v2.zip",                        "08_DADOS_EXTERNOS"),

    # ------------------------------------------------------------ referencias
    (RAIZ / "Referencias", "04_REFERENCIAS"),
]

# arquivos temporarios do Word — candidatos a descarte
PADROES_TEMP = [r"^~\$", r"^~WRL\d+\.tmp$"]


def temp(nome):
    return any(re.match(p, nome) for p in PADROES_TEMP)


def main():
    modo = "APLICANDO" if APLICAR else "DRY-RUN (nada sera alterado)"
    print("=" * 78)
    print(f"REORGANIZACAO DO PROJETO_EUROCLIMA — {modo}")
    print("=" * 78)

    print("\n--- 1. diretorios a criar ---")
    for d in NOVAS:
        alvo = RAIZ / d
        marca = "existe" if alvo.exists() else "CRIAR"
        print(f"  [{marca:>6}] {d}")
        if APLICAR:
            alvo.mkdir(parents=True, exist_ok=True)

    print("\n--- 2. movimentacoes ---")
    n_ok = n_falta = 0
    for origem, dest_rel in MOVIMENTOS:
        origem = Path(origem)
        destino = RAIZ / dest_rel
        if not origem.exists():
            print(f"  [ AUSENTE] {origem.name}")
            n_falta += 1
            continue
        alvo = destino / origem.name if destino.is_dir() or not destino.suffix else destino
        tipo = "DIR " if origem.is_dir() else "FILE"
        print(f"  [{tipo}] {origem.relative_to(RAIZ)}\n         -> {dest_rel}/")
        n_ok += 1
        if APLICAR:
            destino.mkdir(parents=True, exist_ok=True)
            final = destino / origem.name
            if final.exists():
                print(f"         ! destino ja existe, pulando")
                continue
            shutil.move(str(origem), str(final))

    print("\n--- 3. temporarios do Word (nao serao removidos automaticamente) ---")
    achados = []
    for p in RAIZ.rglob("*"):
        if p.is_file() and temp(p.name):
            achados.append(p)
    for p in achados:
        print(f"  [TEMP] {p.relative_to(RAIZ)}  ({p.stat().st_size/1024:.0f} KB)")
    if not achados:
        print("  nenhum encontrado")
    else:
        print(f"\n  {len(achados)} arquivo(s) temporario(s). Feche o Word e apague manualmente,")
        print("  ou rode:  python 04_reorganiza_pastas.py --aplicar --limpar-temp")

    if APLICAR and "--limpar-temp" in sys.argv:
        for p in achados:
            try:
                p.unlink(); print(f"  removido: {p.name}")
            except Exception as e:
                print(f"  falha ao remover {p.name}: {e}")

    print("\n" + "=" * 78)
    print(f"resumo: {n_ok} movimentacoes previstas, {n_falta} origens ausentes")
    if not APLICAR:
        print("Para executar de fato:  python 04_reorganiza_pastas.py --aplicar")
    print("=" * 78)


if __name__ == "__main__":
    main()
