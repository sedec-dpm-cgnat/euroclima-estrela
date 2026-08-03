# -*- coding: utf-8 -*-
"""
Triagem combinatória: eixos do rio das Antas + alternativas laterais no Forqueta.

Este script é uma rodada Codex, separada dos scripts claude_*. Ele usa a mesma
parametrização calibrada da rodada do Forqueta, mas amplia a carteira para todas
as alternativas principais e registra explicitamente:

* pico resultante no posto de Estrela;
* redução em relação ao cenário natural da bacia completa;
* distância ao limiar preliminar de 4.000 m³/s;
* cenários sem Forqueta, com FQ1 e com FQ2;
* regra operativa convencional, seca e comportas.

O limiar de 4.000 m³/s continua provisório. Não é um limite legal de cheia e
deverá ser substituído pela curva cota-dano/HEC-RAS calibrada.
"""
from pathlib import Path
import math
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
D_CAV = ROOT / "01_dados" / "cav"
D_FQ = ROOT / "01_dados" / "cav_forqueta"
D_RES = ROOT / "06_resultados"
D_TAB = D_RES / "tabelas"
D_VAL = D_RES / "VALIDACAO"
D_CLAUDE = D_RES / "CLAUDE"
for p in (D_TAB, D_VAL):
    p.mkdir(parents=True, exist_ok=True)

RD = dict(sep=";", decimal=",", encoding="utf-8-sig")
WR = dict(sep=";", decimal=",", encoding="utf-8-sig", index=False)

A_ANALISE = 19_440.0
A_FORQUETA = 2_845.6
A_ESTRELA = 22_472.0
A_MARGEM = A_ESTRELA - A_ANALISE - A_FORQUETA
Q_PICO_ANTAS = 16_300.0
Q_BASE_TOTAL = 926.0
LAMINA_MM = 227.0
Q_LIMIAR = 4_000.0
Q_EVENTO_2023 = 17_260.9
DT_H = 1.0
FORMA_M = 3.0
Q_PICO_FQ = 1_292.3 * (A_FORQUETA / 791.0) ** 0.85
LAG_H = 0.0
EXCLUIDOS = {"E10"}


def read(path):
    return pd.read_csv(path, **RD)


def gamma_hidro(qp, area_km2, lamina_mm, tp_fator=1.0, n_h=400):
    qb = Q_BASE_TOTAL * area_km2 / A_ESTRELA
    volume = lamina_mm / 1000.0 * area_km2 * 1e6
    fvol = math.gamma(FORMA_M + 1) * math.exp(FORMA_M) / FORMA_M ** (FORMA_M + 1)
    tp = volume / max((qp - qb) * fvol, 1.0) * tp_fator
    t = np.arange(0.0, n_h * 3600.0, DT_H * 3600.0)
    x = t / max(tp, 1.0)
    q = qb + (qp - qb) * x ** FORMA_M * np.exp(FORMA_M * (1.0 - x))
    q[~np.isfinite(q)] = qb
    return t / 3600.0, q


def desloca(q, lag_h):
    k = int(round(lag_h / DT_H))
    if k == 0:
        return q.copy()
    out = np.full_like(q, q[0])
    if k > 0:
        out[k:] = q[:-k]
    else:
        out[:k] = q[-k:]
    return out


def vertedouro(h, h_sol, comprimento, coef=2.1):
    return coef * comprimento * max(h - h_sol, 0.0) ** 1.5


def orificio(h, area, cd=0.62):
    return cd * area * math.sqrt(2.0 * 9.81 * h) if h > 0 else 0.0


def area_para_q(q, carga, cd=0.62):
    return q / (cd * math.sqrt(2.0 * 9.81 * max(carga, 1.0)))


def interp_volume(cv, altura):
    return float(np.interp(altura, cv.altura_m, cv.volume_hm3)) * 1e6


def interp_altura(cv, volume_m3):
    return float(np.interp(volume_m3 / 1e6, cv.volume_hm3, cv.altura_m))


def rota_reservatorio(hin, cv, geo, altura, q_meta, regra):
    """Puls preliminar, com a mesma lógica operativa da rodada calibrada."""
    cv = cv.sort_values("altura_m")
    geo = geo.sort_values("altura_m")
    v_max = interp_volume(cv, altura)
    if regra == "seca":
        h_sol, v_ini = max(altura - 4.0, 0.0), 0.0
        area_fundo = area_para_q(q_meta, altura / 2.0)
    elif regra == "comportas":
        h_norm = 0.70 * altura
        h_sol, v_ini = h_norm, interp_volume(cv, h_norm)
        area_fundo = area_para_q(q_meta, altura * 0.35)
    else:
        h_sol, v_ini, area_fundo = 0.95 * altura, interp_volume(cv, 0.95 * altura), 0.0

    volume = np.zeros(len(hin))
    altura_na = np.zeros(len(hin))
    efluente = np.zeros(len(hin))
    volume[0], altura_na[0] = v_ini, interp_altura(cv, v_ini)
    comprimento_crista = float(np.interp(altura, geo.altura_m, geo.L_crista_m))
    comprimento_soleira = max(comprimento_crista * 0.25, 40.0)
    saturou = False
    dt_s = DT_H * 3600.0

    for i in range(1, len(hin)):
        inflow = (hin[i - 1] + hin[i]) / 2.0
        vp, hp = volume[i - 1], altura_na[i - 1]
        capacidade = vertedouro(hp, h_sol, comprimento_soleira) + orificio(hp, area_fundo)
        cheio = vp >= v_max * 0.995
        if cheio:
            qout = min(capacidade, inflow)
            saturou = True
        else:
            qout = min(q_meta, capacidade)
            ocupacao = vp / max(v_max, 1.0)
            if ocupacao > 0.85:
                qout = min(capacidade, max(q_meta, inflow * (ocupacao - 0.85) / 0.15))
        vn = vp + (inflow - qout) * dt_s
        if vn > v_max:
            qout = max(qout, inflow)
            vn = v_max
            saturou = True
        if vn < v_ini:
            qout = max(qout + (vn - v_ini) / dt_s, 0.0)
            vn = v_ini
        volume[i] = vn
        altura_na[i] = interp_altura(cv, vn)
        efluente[i] = qout
    return efluente, float((volume.max() - v_ini) / 1e6), saturou


def imediato(eixo, conjunto, montantes):
    candidatos = [m for m in conjunto if m != eixo and m in montantes.get(eixo, set())]
    return [m for m in candidatos if not any(o in montantes.get(m, set()) for o in candidatos)]


def jusantes(eixo, conjunto, montantes):
    return [o for o in conjunto if o != eixo and eixo in montantes.get(o, set())]


# Entradas principais.
eix = read(D_CAV / "eixos_todos.csv")
topo = read(D_CAV / "topologia_eixos.csv")
cav = read(D_RES / "tabelas" / "cav_eixos_novos_interpolada_1m.csv")
geo = read(D_CAV / "geometria_todos.csv")
alt_adm = read(D_CLAUDE / "claude_altura_admissivel_revisada.csv")

AREA = dict(zip(eix.codigo, eix.area_km2))
H_ADM = dict(zip(alt_adm.eixo, alt_adm.altura_max_m))
MONT = {e: set(topo.loc[topo.eixo == e, "montante"]) for e in eix.codigo}

# O pipeline isolado do Forqueta renumera os eixos. Reconciliamos por área.
fqe = read(D_FQ / "eixos_todos.csv")
fqc = read(D_FQ / "cav_todos.csv")
fqg = read(D_FQ / "geometria_todos.csv")
fq_map = {}
for _, row in fqe.iterrows():
    dist = (eix.area_km2 - row.area_km2).abs()
    if float(dist.min()) <= 2.0:
        fq_map[row.codigo] = eix.loc[dist.idxmin(), "codigo"]
    else:
        fq_map[row.codigo] = "FQ1" if row.area_km2 > 2300.0 else "FQ2"
fqc["eixo"] = fqc.eixo.map(fq_map)
fqg["eixo"] = fqg.eixo.map(fq_map)
fqe["codigo"] = fqe.codigo.map(fq_map)
AREA_FQ = dict(zip(fqe.codigo, fqe.area_km2))
MONT_FQ = {e: set() for e in AREA_FQ}
topo_fq = read(D_FQ / "topologia_eixos.csv")
for _, row in topo_fq.iterrows():
    e, m = fq_map.get(row.eixo, row.eixo), fq_map.get(row.montante, row.montante)
    MONT_FQ.setdefault(e, set()).add(m)
ALT_FQ = {"FQ1": 30.0, "FQ2": 30.0}

# Hidrogramas próprios das vertentes, com defasagem medida de 0 h.
T_H, Q_ANTAS = gamma_hidro(Q_PICO_ANTAS, A_ANALISE, LAMINA_MM)
_, Q_FQ = gamma_hidro(Q_PICO_FQ, A_FORQUETA, LAMINA_MM, tp_fator=(A_FORQUETA / A_ANALISE) ** 0.3)
qb_antas = Q_BASE_TOTAL * A_ANALISE / A_ESTRELA
qb_fq = Q_BASE_TOTAL * A_FORQUETA / A_ESTRELA
Q_MARGEM = np.full_like(Q_ANTAS, Q_BASE_TOTAL * A_MARGEM / A_ESTRELA)
Q_MARGEM += (Q_ANTAS - qb_antas) * (A_MARGEM / A_ANALISE)
Q_NATURAL = Q_ANTAS + desloca(Q_FQ, LAG_H) + Q_MARGEM
PICO_NATURAL = float(Q_NATURAL.max())


def rota_vertente(conjunto, q_nat, area_ref, regra, area, montantes, cav_data, geo_data, alturas):
    conjunto = [e for e in conjunto if e not in EXCLUIDOS]
    if not conjunto:
        return q_nat.copy(), 0.0, False, 0.0
    efluentes, volume_total, saturou = {}, 0.0, False
    for eixo in sorted(conjunto, key=lambda x: area[x]):
        mont = imediato(eixo, conjunto, montantes)
        inc = area[eixo] - sum(area[m] for m in mont)
        hin = q_nat * (inc / area_ref)
        for m in mont:
            hin += efluentes[m]
        cv = cav_data[cav_data.eixo == eixo]
        if eixo in alturas:
            altura = float(alturas[eixo])
        else:
            efluentes[eixo] = hin
            continue
        geo_e = geo_data[geo_data.eixo == eixo]
        if cv.empty or geo_e.empty or altura <= 0:
            efluentes[eixo] = hin
            continue
        # A meta de descarga é referida ao ponto de análise de 19.440 km²,
        # como na rodada calibrada. Para o Forqueta isso evita conceder ao
        # tributário uma vazão-alvo artificialmente alta apenas porque sua
        # área de referência é menor que a bacia em Estrela.
        q_meta = Q_LIMIAR * area[eixo] / A_ANALISE
        efluentes[eixo], usado, sat = rota_reservatorio(hin, cv, geo_e, altura, q_meta, regra)
        volume_total += usado
        saturou = saturou or sat

    terminais = [e for e in conjunto if not jusantes(e, conjunto, montantes)]
    area_controlada = sum(area[e] for e in terminais)
    q_saida = q_nat * (1.0 - area_controlada / area_ref)
    for e in terminais:
        q_saida += efluentes[e]
    return q_saida, volume_total, saturou, area_controlada


def avalia(eixos_antas, eixos_forqueta, regra):
    qa, va, sa, aa = rota_vertente(eixos_antas, Q_ANTAS, A_ANALISE, regra, AREA, MONT, cav, geo, H_ADM)
    qf, vf, sf, af = rota_vertente(eixos_forqueta, Q_FQ, A_FORQUETA, regra, AREA_FQ, MONT_FQ, fqc, fqg, ALT_FQ)
    q_est = qa + desloca(qf, LAG_H) + Q_MARGEM
    return dict(
        serie=q_est,
        pico=float(q_est.max()),
        vol_antas=va,
        vol_forqueta=vf,
        area_antas=aa,
        area_forqueta=af,
        saturou=sa or sf,
    )


ALTERNATIVAS = {
    "SEM_OBRA": [],
    "ALT-A": ["E02", "E04"],
    "ALT-B": ["E02", "E04", "E01"],
    "ALT-C": ["E02", "E04", "E05"],
    "ALT-D": ["E02", "E04", "E08"],
    "ALT-E": ["E02", "E04", "E12"],
    "ALT-F": ["E02"],
    "ALT-G": ["E04"],
    "ALT-H": ["E12"],
    "ALT-I": ["E02", "E04", "E01", "E05", "E08"],
    "ALT-J": ["E02", "E04", "E01", "E05", "E08", "E12"],
}
FQ_CENARIOS = {
    "SEM_FORQUETA": [],
    "FQ1": ["FQ1"],
    "FQ2": ["FQ2"],
    "FQ1+FQ2_INVIAVEL": ["FQ1", "FQ2"],
}
REGRAS = ("seca", "comportas", "convencional")

rows = []
series = [{"cenario": "SEM_OBRA", "regra": "natural", "tempo_h": t, "pico_m3s": q}
          for t, q in zip(T_H, Q_NATURAL)]
for nome_alt, eixos_a in ALTERNATIVAS.items():
    for nome_fq, eixos_f in FQ_CENARIOS.items():
        inviavel = nome_fq == "FQ1+FQ2_INVIAVEL"
        for regra in REGRAS:
            r = avalia(eixos_a, eixos_f, regra)
            pico = r["pico"]
            rows.append({
                "alternativa_antas": nome_alt,
                "eixos_antas": "+".join(eixos_a) or "-",
                "cenario_forqueta": nome_fq,
                "eixos_forqueta": "+".join(eixos_f) or "-",
                "regra_operativa": regra,
                "fisicamente_admissivel": not inviavel,
                "pico_natural_estrela_m3s": round(PICO_NATURAL, 1),
                "pico_resultante_estrela_m3s": round(pico, 1),
                "reducao_pico_pct": round(100.0 * (1.0 - pico / PICO_NATURAL), 2),
                "acima_limiar_preliminar_m3s": round(max(pico - Q_LIMIAR, 0.0), 1),
                "razao_limiar_preliminar": round(pico / Q_LIMIAR, 3),
                "reducao_em_relacao_evento_2023_pct": round(100.0 * (1.0 - pico / Q_EVENTO_2023), 2),
                "area_controlada_antas_km2": round(r["area_antas"], 1),
                "area_controlada_forqueta_km2": round(r["area_forqueta"], 1),
                "volume_usado_antas_hm3": round(r["vol_antas"], 1),
                "volume_usado_forqueta_hm3": round(r["vol_forqueta"], 1),
                "volume_usado_total_hm3": round(r["vol_antas"] + r["vol_forqueta"], 1),
                "algum_reservatorio_saturou": r["saturou"],
                "observacao": "incluir apenas como limite teórico; FQ1 e FQ2 interferem por cota" if inviavel else "",
            })
            if regra in ("seca", "comportas"):
                cid = f"{nome_alt}+{nome_fq}+{regra}"
                for t, q in zip(T_H, r["serie"]):
                    series.append({"cenario": cid, "regra": regra, "tempo_h": t, "pico_m3s": q})

resultado = pd.DataFrame(rows)
resultado.to_csv(D_TAB / "roteamento_combinado_antas_forqueta.csv", **WR)
pd.DataFrame(series).to_csv(D_TAB / "hidrogramas_combinados_antas_forqueta.csv", **WR)

# Síntese dos cenários fisicamente admissíveis; empate resolvido por menor volume.
validos = resultado[resultado.fisicamente_admissivel].copy()
melhor = validos.sort_values(["pico_resultante_estrela_m3s", "volume_usado_total_hm3"]).iloc[0]
best_seca = validos[validos.regra_operativa == "seca"].sort_values(
    ["pico_resultante_estrela_m3s", "volume_usado_total_hm3"]).iloc[0]
best_comp = validos[validos.regra_operativa == "comportas"].sort_values(
    ["pico_resultante_estrela_m3s", "volume_usado_total_hm3"]).iloc[0]
best_conv = validos[validos.regra_operativa == "convencional"].sort_values(
    ["pico_resultante_estrela_m3s", "volume_usado_total_hm3"]).iloc[0]

md = []
md.append("# Triagem combinada Antas + Forqueta")
md.append("")
md.append("Rodada preliminar com hidrogramas próprios do Antas e do Forqueta, defasagem medida de 0 h e exutório em Estrela (22.472 km²). O ponto de 19.440 km² permanece a montante do Forqueta.")
md.append("")
md.append(f"- Pico natural sintético em Estrela: **{PICO_NATURAL:,.0f} m³/s**; máximo observado em 19/11/2023: **{Q_EVENTO_2023:,.0f} m³/s**.")
md.append(f"- Limiar preliminar de comparação: **{Q_LIMIAR:,.0f} m³/s**; não é limite legal nem substitui a curva cota-dano calibrada.")
md.append(f"- Altura de triagem adotada: **30 m** para FQ1 e FQ2; os dois eixos são mutuamente exclusivos por interferência de cota.")
md.append("")
md.append("## Melhores combinações fisicamente admissíveis")
md.append("")
md.append("| Regra | Alternativa Antas | Forqueta | Pico em Estrela (m³/s) | Redução (%) | Acima de 4.000 (m³/s) | Volume total (hm³) |")
md.append("|---|---|---|---:|---:|---:|---:|")
for r in [best_seca, best_comp, best_conv]:
    md.append(f"| {r.regra_operativa} | {r.alternativa_antas} | {r.cenario_forqueta} | {r.pico_resultante_estrela_m3s:,.0f} | {r.reducao_pico_pct:.1f} | {r.acima_limiar_preliminar_m3s:,.0f} | {r.volume_usado_total_hm3:,.0f} |")
md.append("")
md.append("## Leitura preliminar")
md.append("")
md.append(f"A menor vazão entre as combinações fisicamente admissíveis foi **{melhor.pico_resultante_estrela_m3s:,.0f} m³/s**, em **{melhor.alternativa_antas} + {melhor.cenario_forqueta}**, com regra **{melhor.regra_operativa}**. Esse valor permanece **{melhor.acima_limiar_preliminar_m3s:,.0f} m³/s acima** do limiar preliminar de 4.000 m³/s e corresponde a {melhor.reducao_em_relacao_evento_2023_pct:.1f}% de redução em relação ao pico observado de 2023.")
md.append("")
md.append("Portanto, nesta parametrização não há combinação que leve o pico em Estrela a uma magnitude próxima da não ocorrência de cheia. O Forqueta melhora a proteção de Estrela, mas o ganho marginal é pequeno diante do controle já obtido pela carteira ALT-J. A conclusão é de triagem: deve ser reavaliada no HEC-RAS 1D com remanso, operação e curva cota-dano.")
md.append("")
md.append("Os resultados completos estão em `tabelas/roteamento_combinado_antas_forqueta.csv`; as séries para os gráficos estão em `tabelas/hidrogramas_combinados_antas_forqueta.csv`.")
(D_RES / "ROTEAMENTO_COMBINADO_ANTAS_FORQUETA.md").write_text("\n".join(md) + "\n", encoding="utf-8")

# Figura de comunicação: natural, ALT-J, ALT-J+FQ1 e ALT-J+FQ2 sob regra seca.
try:
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(10.5, 5.8), dpi=180)
    ax.plot(T_H, Q_NATURAL, color="#333333", lw=2.2, label="Natural — Antas + Forqueta")
    for fq, color, label in [("SEM_FORQUETA", "#1f77b4", "ALT-J"), ("FQ1", "#d62728", "ALT-J + FQ1"), ("FQ2", "#2ca02c", "ALT-J + FQ2")]:
        r = avalia(ALTERNATIVAS["ALT-J"], FQ_CENARIOS[fq], "seca")
        ax.plot(T_H, r["serie"], lw=1.8, color=color, label=f"{label} — {r['pico']:,.0f} m³/s")
    ax.axhline(Q_LIMIAR, color="#9467bd", ls="--", lw=1.4, label="Limiar preliminar 4.000 m³/s")
    ax.set_xlabel("Tempo desde o início do hidrograma (h)")
    ax.set_ylabel("Vazão em Estrela (m³/s)")
    ax.set_title("Triagem combinada: barragens do Antas e opções no Forqueta")
    ax.grid(True, alpha=0.25)
    ax.legend(frameon=True, fontsize=8, ncol=2)
    fig.tight_layout()
    fig.savefig(D_VAL / "HIDROGRAMAS_COMBINADOS_ANTAS_FORQUETA.png", bbox_inches="tight")
    plt.close(fig)
except Exception as exc:
    print(f"Aviso: figura não gerada: {exc}")

# Fallback vetorial sem dependência externa: a figura é mantida em SVG para
# que o relatório possa ampliá-la sem perda de resolução.
svg_path = D_VAL / "HIDROGRAMAS_COMBINADOS_ANTAS_FORQUETA.svg"
if not svg_path.exists():
    from xml.sax.saxutils import escape

    curvas = [("Natural — Antas + Forqueta", Q_NATURAL, "#333333", 3.0)]
    for fq, color, label in [
        ("SEM_FORQUETA", "#1f77b4", "ALT-J"),
        ("FQ1", "#d62728", "ALT-J + FQ1"),
        ("FQ2", "#2ca02c", "ALT-J + FQ2"),
    ]:
        rr = avalia(ALTERNATIVAS["ALT-J"], FQ_CENARIOS[fq], "seca")
        curvas.append((f"{label} — {rr['pico']:,.0f} m³/s", rr["serie"], color, 2.0))
    W, H = 1100, 620
    left, top, right, bottom = 78, 58, 1035, 530
    ymax = 18000.0

    def sx(x):
        return left + (x / max(T_H.max(), 1.0)) * (right - left)

    def sy(y):
        return bottom - (max(0.0, min(float(y), ymax)) / ymax) * (bottom - top)

    def points(values):
        return " ".join(f"{sx(x):.1f},{sy(y):.1f}" for x, y in zip(T_H, values))

    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="620" viewBox="0 0 1100 620">',
        '<rect width="1100" height="620" fill="white"/>',
        '<text x="78" y="29" font-family="Arial,sans-serif" font-size="19" font-weight="bold">Triagem combinada: barragens do Antas e opções no Forqueta</text>',
        f'<rect x="{left}" y="{top}" width="{right-left}" height="{bottom-top}" fill="#fafafa" stroke="#444"/>',
    ]
    for tick in range(0, 18001, 3000):
        y = sy(tick)
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{right}" y2="{y:.1f}" stroke="#d9d9d9"/>')
        parts.append(f'<text x="{left-10}" y="{y+5:.1f}" text-anchor="end" font-family="Arial,sans-serif" font-size="12">{tick:,}</text>')
    for tick in range(0, 401, 50):
        x = sx(tick)
        parts.append(f'<text x="{x:.1f}" y="{bottom+24}" text-anchor="middle" font-family="Arial,sans-serif" font-size="12">{tick}</text>')
    y_lim = sy(Q_LIMIAR)
    parts.append(f'<line x1="{left}" y1="{y_lim:.1f}" x2="{right}" y2="{y_lim:.1f}" stroke="#9467bd" stroke-width="2" stroke-dasharray="8,6"/>')
    parts.append(f'<text x="{right-5}" y="{y_lim-7:.1f}" text-anchor="end" font-family="Arial,sans-serif" font-size="12" fill="#6a3d9a">Limiar preliminar: 4.000 m³/s</text>')
    for label, values, color, width in curvas:
        parts.append(f'<polyline points="{points(values)}" fill="none" stroke="{color}" stroke-width="{width}"/>')
    for i, (label, _, color, _) in enumerate(curvas):
        x = left + 18 + (i % 2) * 455
        y = 555 + (i // 2) * 22
        parts.append(f'<line x1="{x}" y1="{y-4}" x2="{x+25}" y2="{y-4}" stroke="{color}" stroke-width="3"/>')
        parts.append(f'<text x="{x+32}" y="{y}" font-family="Arial,sans-serif" font-size="12">{escape(label)}</text>')
    parts += [
        f'<text x="{(left+right)/2:.1f}" y="605" text-anchor="middle" font-family="Arial,sans-serif" font-size="13">Tempo desde o início do hidrograma (h)</text>',
        f'<text x="18" y="{(top+bottom)/2:.1f}" transform="rotate(-90 18 {(top+bottom)/2:.1f})" text-anchor="middle" font-family="Arial,sans-serif" font-size="13">Vazão em Estrela (m³/s)</text>',
        '</svg>',
    ]
    svg_path.write_text("\n".join(parts), encoding="utf-8")

print("Pico natural em Estrela:", round(PICO_NATURAL, 1), "m3/s")
print("Melhor combinação admissível:")
print(melhor[["regra_operativa", "alternativa_antas", "cenario_forqueta", "pico_resultante_estrela_m3s", "reducao_pico_pct", "acima_limiar_preliminar_m3s", "volume_usado_total_hm3"]].to_string())
print("Melhor regra seca:")
print(best_seca[["alternativa_antas", "cenario_forqueta", "pico_resultante_estrela_m3s", "reducao_pico_pct", "acima_limiar_preliminar_m3s"]].to_string())
print("Melhor regra comportas:")
print(best_comp[["alternativa_antas", "cenario_forqueta", "pico_resultante_estrela_m3s", "reducao_pico_pct", "acima_limiar_preliminar_m3s"]].to_string())
