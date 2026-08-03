"""Gera o diagrama topológico das alternativas que irão ao HEC-RAS 1D.

O desenho separa a conectividade física dos eixos da sequência de cenários
hidráulicos. Ele é deliberadamente esquemático: não substitui a confirmação
topográfica, de remanso ou de tempo de trânsito no modelo.
"""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "06_resultados" / "VALIDACAO" / "DIAGRAMA_TOPOLOGICO_ALTERNATIVAS_HECRAS.svg"


def esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def box(x, y, w, h, title, subtitle, fill="#eef4fb", stroke="#3b6ea5", text="#203040", dash=""):
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    return (
        f'<g><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="2"{dash_attr}/>'
        f'<text x="{x + w / 2}" y="{y + 25}" text-anchor="middle" '
        f'font-size="18" font-weight="700" fill="{text}">{esc(title)}</text>'
        f'<text x="{x + w / 2}" y="{y + 47}" text-anchor="middle" '
        f'font-size="12" fill="{text}">{esc(subtitle)}</text></g>'
    )


def line(x1, y1, x2, y2, color="#5b6770", width=3, dash="", arrow=True):
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    marker = ' marker-end="url(#arrow)"' if arrow else ""
    return (
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" '
        f'stroke-width="{width}"{dash_attr}{marker}/>'
    )


def text(x, y, value, size=14, fill="#263238", weight="400", anchor="start"):
    return (
        f'<text x="{x}" y="{y}" font-size="{size}px" fill="{fill}" '
        f'font-weight="{weight}" text-anchor="{anchor}">{esc(value)}</text>'
    )


def build_svg() -> str:
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1800" height="1120" viewBox="0 0 1800 1120">',
        '<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth">'
        '<path d="M0,0 L0,6 L9,3 z" fill="#5b6770"/></marker></defs>',
        '<rect width="1800" height="1120" fill="#ffffff"/>',
        text(60, 48, "Topologia física e matriz de entrada no HEC-RAS 1D", 28, "#17324d", "700"),
        text(60, 75, "Linhas contínuas = conectividade a confirmar; linhas tracejadas = afluências laterais ou sensibilidades.", 15, "#52606d"),
        '<rect x="35" y="100" width="1730" height="510" rx="14" fill="#f7f9fb" stroke="#d7e0e8"/>',
        text(65, 132, "A. Rede física esquemática", 21, "#17324d", "700"),
        text(65, 160, "Os eixos E02/E04 são os ramos prioritários; E08 e E12 entram como extensões condicionadas.", 14, "#52606d"),
    ]

    # Main Antas network: two convergent branches and the downstream cascade.
    nodes = {
        "E02": (150, 205, "prioritário"),
        "E03": (340, 205, "condicionado"),
        "E08": (530, 265, "intermediário"),
        "E09": (720, 265, "condicionado"),
        "E10": (910, 265, "sensibilidade"),
        "E11": (1100, 265, "condicionado"),
        "E12": (1290, 265, "cobertura"),
        "E04": (150, 385, "prioritário"),
        "E05": (340, 385, "condicionado"),
        "E06": (530, 445, "condicionado"),
        "E07": (720, 445, "condicionado"),
        "E01": (910, 445, "condicionado"),
    }
    colors = {
        "prioritário": ("#e6f2ff", "#1d70b8"),
        "intermediário": ("#fff4d6", "#b7791f"),
        "cobertura": ("#fde8e8", "#c53030"),
        "condicionado": ("#f1f3f5", "#6c757d"),
        "sensibilidade": ("#f7eafa", "#7b3f98"),
    }
    # Edges are drawn before the nodes so that nodes cover line ends.
    edges = [
        (205, 230, 340, 230, "#1d70b8", ""),
        (395, 230, 530, 275, "#6c757d", ""),
        (205, 410, 340, 410, "#1d70b8", ""),
        (395, 410, 530, 455, "#6c757d", ""),
        (585, 295, 720, 295, "#6c757d", ""),
        (775, 295, 910, 295, "#7b3f98", ""),
        (965, 295, 1100, 295, "#6c757d", ""),
        (1155, 295, 1290, 295, "#c53030", ""),
        (585, 445, 720, 325, "#6c757d", ""),
        (965, 445, 1100, 325, "#6c757d", ""),
        (1345, 295, 1600, 295, "#17324d", ""),
    ]
    for x1, y1, x2, y2, color, dash in edges:
        parts.append(line(x1, y1, x2, y2, color=color, width=3, dash=dash))

    for name, (x, y, role) in nodes.items():
        fill, stroke = colors[role]
        parts.append(box(x, y, 110, 55, name, role, fill, stroke))

    parts += [
        text(1630, 289, "saída para", 13, "#17324d", "700", "middle"),
        text(1630, 309, "Estrela", 15, "#17324d", "700", "middle"),
        # GU1 lateral branch
        line(850, 170, 850, 250, color="#2f855a", width=3, dash="8 6"),
        box(760, 115, 180, 55, "GU1", "Guaporé · prioridade", "#e7f7ed", "#2f855a"),
        text(950, 146, "entrada lateral a montante", 13, "#2f855a", "700"),
        text(950, 164, "com desagregação do hidrograma", 12, "#2f855a"),
        # Forqueta lateral branch
        line(1215, 475, 1215, 325, color="#805ad5", width=3, dash="8 6"),
        box(1115, 475, 200, 55, "FQ2", "Forqueta · sensibilidade", "#f0eafd", "#805ad5"),
        text(1335, 498, "entrada lateral antes de Estrela", 13, "#805ad5", "700"),
        text(1335, 516, "FQ1 é alternativa exclusiva e condicionada", 12, "#805ad5"),
        # legend
        '<rect x="65" y="540" width="15" height="15" fill="#e6f2ff" stroke="#1d70b8"/>',
        text(88, 553, "prioritário", 12, "#263238"),
        '<rect x="180" y="540" width="15" height="15" fill="#fff4d6" stroke="#b7791f"/>',
        text(203, 553, "extensão intermediária", 12, "#263238"),
        '<rect x="375" y="540" width="15" height="15" fill="#fde8e8" stroke="#c53030"/>',
        text(398, 553, "cobertura terminal", 12, "#263238"),
        line(600, 548, 665, 548, color="#805ad5", width=3, dash="8 6", arrow=False),
        text(678, 553, "ramo lateral / sensibilidade", 12, "#263238"),
        text(65, 585, "A topologia não autoriza, por si só, a combinação de obras: remanso, cota de afogamento, energia e operação ainda precisam ser validados.", 13, "#52606d"),
        '<rect x="35" y="635" width="1730" height="430" rx="14" fill="#f7f9fb" stroke="#d7e0e8"/>',
        text(65, 670, "B. Sequência de simulação no HEC-RAS 1D", 21, "#17324d", "700"),
        text(65, 697, "A primeira rodada identifica o efeito incremental; as extensões só entram depois da calibração do caso sem obra.", 14, "#52606d"),
    ]

    stages = [
        ("HEC-00", "REF", "sem obra", "calibração do evento 2024", "#e9ecef", "#495057"),
        ("HEC-01", "ALT-A / C01", "E02 + E04", "primeiro caso estrutural", "#e6f2ff", "#1d70b8"),
        ("HEC-02", "ALT-D / C03", "E02 + E04 + E08", "cobertura intermediária", "#fff4d6", "#b7791f"),
        ("HEC-03", "ALT-E / C02", "E02 + E04 + E12", "cobertura ampliada", "#fde8e8", "#c53030"),
        ("HEC-04", "ALT-J + GU1", "carteira + Guaporé", "prioridade estrutural", "#e7f7ed", "#2f855a"),
        ("HEC-05", "ALT-J + FQ2", "carteira + Forqueta", "sensibilidade lateral", "#f0eafd", "#805ad5"),
        ("HEC-06", "C04 / C05 / FQ1", "rede crítica", "sensibilidade opcional", "#f1f3f5", "#6c757d"),
    ]
    x = 65
    y = 755
    w = 215
    h = 150
    for i, (code, name, axes, role, fill, stroke) in enumerate(stages):
        parts.append(box(x, y, w, h, code, name, fill, stroke))
        parts.append(text(x + w / 2, y + 82, axes, 14, stroke, "700", "middle"))
        parts.append(text(x + w / 2, y + 106, role, 12, "#52606d", "400", "middle"))
        if i < len(stages) - 1:
            parts.append(line(x + w + 5, y + h / 2, x + w + 35, y + h / 2, color="#8a959e", width=2))
        x += 245
    parts += [
        '<rect x="65" y="950" width="1690" height="80" rx="8" fill="#fff8e1" stroke="#d69e2e"/>',
        text(85, 978, "Regra de decisão", 14, "#8a5a00", "700"),
        text(85, 1003, "HEC-01 é o primeiro caso com obra. HEC-02 e HEC-03 medem o ganho incremental. GU1 entra como extensão prioritária após a calibração; FQ2 e FQ1 são sensibilidades laterais exclusivas. Nenhum cenário é obra selecionada antes da curva cota–dano e da validação hidráulica.", 13, "#5d4700"),
        text(65, 1092, "Fonte: síntese da topologia E01–E12 e da matriz de alternativas do estudo EUROCLIMA+ / AECID. Esquema sem escala.", 12, "#6c757d"),
        "</svg>",
    ]
    return "\n".join(parts)


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build_svg(), encoding="utf-8")
    print(OUT)
