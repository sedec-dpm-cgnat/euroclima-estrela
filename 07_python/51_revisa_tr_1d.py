"""Gera a versão limpa e coerente com HEC-RAS 1D da minuta do TR.

Uso:
    python 51_revisa_tr_1d.py [entrada.docx] [saida.docx]

A REV. 0A original não é sobrescrita. O script parte da REV. 0B já limpa,
remove notas editoriais internas e corrige a exigência hidráulica para 1D.
"""

from __future__ import annotations

import sys
from pathlib import Path

from docx import Document


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "06_resultados" / "TR_MINUTA_REV0B.docx"
DEFAULT_OUTPUT = ROOT / "06_resultados" / "TR_MINUTA_REV0C_LIMPA_HECRAS1D.docx"


def remove_paragraph(paragraph) -> None:
    element = paragraph._element
    element.getparent().remove(element)
    paragraph._p = paragraph._element = None


def revise_paragraphs(document: Document) -> None:
    remove_editorial = {
        "(mantida da REV. 0A — texto atual está adequado)",
        "(mantida da REV. 0A, com acréscimo do item 2.1)",
        "(mantida da REV. 0A)",
    }

    for paragraph in list(document.paragraphs):
        text = paragraph.text.strip()
        if text in remove_editorial:
            remove_paragraph(paragraph)
            continue

        # A nota de revisão é útil no histórico, mas não pertence ao TR que será
        # encaminhado para análise. A REV. 0A original continua preservada fora
        # desta cópia de trabalho.
        if text.startswith("NOTA DE REVISÃO"):
            remove_paragraph(paragraph)
            continue

        if text == "TERMO DE REFERÊNCIA — REV. 0B (MINUTA)":
            paragraph.text = "TERMO DE REFERÊNCIA — REV. 0C (MINUTA LIMPA — HEC-RAS 1D)"
            continue

        if text.startswith("2.4 — Modelo hidráulico."):
            paragraph.text = (
                "2.4 — Modelo hidráulico. Modelagem hidráulica unidimensional "
                "(1D) obrigatória no trecho de estudo e no subtrecho refinado que "
                "compreende a área urbana de Estrela. O modelo deverá representar "
                "calha, planície, pontes, confluências, diques e estruturas de "
                "controle por seções transversais e estruturas hidráulicas. A "
                "geração de mapas de profundidade, velocidade, perigo "
                "hidrodinâmico (h·v), tempo de propagação e extensão das manchas "
                "deverá ser feita a partir do HEC-RAS 1D e de pós-processamento "
                "geoespacial. Eventual uso de modelo 2D poderá ser proposto apenas "
                "como análise complementar, mediante justificativa e aprovação da "
                "CONTRATANTE; não integra o modelo hidráulico principal deste TR."
            )

        if "modelagem hidrodinâmica bidimensional" in paragraph.text:
            paragraph.text = paragraph.text.replace(
                "modelagem hidrodinâmica bidimensional",
                "modelagem hidráulica unidimensional (1D)",
            )


def revise_tables(document: Document) -> None:
    # T6 é a tabela de qualificação da equipe na REV. 0B.
    if len(document.tables) > 6:
        for row in document.tables[6].rows:
            for cell in row.cells:
                if "projetos 2D comprovados" in cell.text:
                    for paragraph in cell.paragraphs:
                        if "projetos 2D comprovados" in paragraph.text:
                            paragraph.text = paragraph.text.replace(
                                "projetos 2D comprovados",
                                "projetos de modelagem hidráulica 1D comprovados",
                            )


def main() -> int:
    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_INPUT
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUTPUT
    if not input_path.exists():
        raise FileNotFoundError(input_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    document = Document(input_path)
    revise_paragraphs(document)
    revise_tables(document)
    document.save(output_path)
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
