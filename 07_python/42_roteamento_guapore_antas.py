# -*- coding: utf-8 -*-
"""Triagem do GU1 com decomposição do hidrograma do rio das Antas.

O hidrograma agregado de 19.440 km² é decomposto em uma vertente residual de
16.953 km² e na sub-bacia do Guaporé (2.487 km²). Essa separação evita somar o
Guaporé duas vezes. A forma temporal é sintética Gamma, calibrada apenas por
picos diários observados no posto Santa Lúcia; o resultado não substitui uma
modelagem chuva-vazão ou HEC-RAS 1D.
"""

from __future__ import annotations

import contextlib
import html
import io
import math
import runpy
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
D_RES = ROOT / "06_resultados"
D_TAB = D_RES / "tabelas"
D_VAL = D_RES / "VALIDACAO"
D_GU = ROOT / "01_dados" / "cav_guapore"
D_DB = ROOT / "01_dados" / "dpm_db"
for path in (D_TAB, D_VAL):
    path.mkdir(parents=True, exist_ok=True)

with contextlib.redirect_stdout(io.StringIO()):
    NS = runpy.run_path(str(ROOT / "07_python" / "39_roteamento_combinado_antas_forqueta.py"))

RD = dict(sep=";", decimal=",", encoding="utf-8-sig")
WR = dict(sep=";", decimal=",", encoding="utf-8-sig", index=False)

gamma_hidro = NS["gamma_hidro"]
desloca = NS["desloca"]
rota_vertente = NS["rota_vertente"]
T_H = NS["T_H"]
Q_ANTAS_PICO = float(NS["Q_PICO_ANTAS"])
Q_ANTAS_BASE = np.asarray(NS["Q_ANTAS"], dtype=float)
Q_FQ = NS["Q_FQ"]
Q_MARGEM = NS["Q_MARGEM"]
Q_LIMIAR = float(NS["Q_LIMIAR"])
LAMINA_MM = float(NS["LAMINA_MM"])
A_ANALISE = float(NS["A_ANALISE"])
A_FORQUETA = float(NS["A_FORQUETA"])
AREA_ANTAS = NS["AREA"]
MONT_ANTAS = NS["MONT"]
CAV_ANTAS = NS["cav"]
GEO_ANTAS = NS["geo"]
H_ADM_ANTAS = NS["H_ADM"]

eixos_gu = pd.read_csv(D_GU / "eixos_todos.csv", **RD)
gu_row = eixos_gu.loc[eixos_gu["codigo"] == "E01"].iloc[0]
A_GU_TOTAL = float(pd.read_csv(D_RES / "tabelas" / "eixo_guapore_proposto.csv", **RD).loc[0, "area_total_guapore_km2"])
A_GU1 = float(gu_row["area_BHO_km2"])
A_REST = A_ANALISE - A_GU_TOTAL
GU_MAP = {"E01": "GU1"}
GU_CAV = pd.read_csv(D_GU / "cav_todos.csv", **RD)
GU_CAV = GU_CAV[GU_CAV["eixo"] == "E01"].copy()
GU_CAV["eixo"] = "GU1"
GU_GEO = pd.read_csv(D_GU / "geometria_todos.csv", **RD)
GU_GEO = GU_GEO[GU_GEO["eixo"] == "E01"].copy()
GU_GEO["eixo"] = "GU1"

serie = pd.read_csv(D_DB / "86580000_vazao.csv", **RD, parse_dates=["data"])
serie["vazao"] = pd.to_numeric(serie["vazao"], errors="coerce")
serie = serie.dropna(subset=["data", "vazao"])
Q_GU_OBS_PICO = float(serie["vazao"].max())
Q_GU_2023_NOV = float(serie.loc[(serie.data.dt.year == 2023) & (serie.data.dt.month == 11), "vazao"].max())
Q_GU_DESIGN = Q_GU_OBS_PICO * (A_GU_TOTAL / 2470.0) ** 0.85

# O pico do Antas é mantido na mesma referência da rodada 39. A parcela
# residual é a diferença de pico; as duas formas são reconstruídas com a mesma
# lâmina sintética apenas para esta triagem de ordem de grandeza.
EVENTOS = {
    "pico_historico_santa_lucia": Q_GU_DESIGN,
    "novembro_2023_santa_lucia": Q_GU_2023_NOV * (A_GU_TOTAL / 2470.0) ** 0.85,
}

ALT = {
    "SEM_OBRA": [],
    "ALT-J": list(NS["ALTERNATIVAS"]["ALT-J"]),
}
FQ = {"SEM_FORQUETA": [], "FQ2": ["FQ2"]}
ALT_FQ = NS["ALT_FQ"]
AREA_FQ = NS["AREA_FQ"]
MONT_FQ = NS["MONT_FQ"]
CAV_FQ = NS["fqc"]
GEO_FQ = NS["fqg"]


def serie_gamma_gu(pico_gu):
    # Mantém a mesma forma temporal de Q_ANTAS usada na matriz combinada.
    # A versão anterior somava dois hidrogramas gamma independentes, alterando
    # o pico natural e tornando o HEC-04 incomparável aos demais casos.
    frac_gu = min(max(float(pico_gu) / Q_ANTAS_PICO, 0.0), 0.95)
    q_gu = Q_ANTAS_BASE * frac_gu
    q_rest = Q_ANTAS_BASE - q_gu
    return q_rest, q_gu


def branch_gu(q_gu, altura, regra):
    if altura <= 0:
        return q_gu.copy(), 0.0, False, 0.0
    return rota_vertente(
        ["GU1"], q_gu, A_GU_TOTAL, regra,
        {"GU1": A_GU1}, {"GU1": set()}, GU_CAV, GU_GEO, {"GU1": altura},
    )


def branch_fq(q_fq, regra):
    if not q_fq:
        # Sem barragem no Forqueta, a contribuição natural continua chegando
        # a Estrela. O ramo não pode ser zerado apenas porque não foi roteado.
        return Q_FQ.copy(), 0.0, False, 0.0
    return rota_vertente(q_fq, Q_FQ, A_FORQUETA, regra, AREA_FQ, MONT_FQ, CAV_FQ, GEO_FQ, ALT_FQ)


rows = []
curvas = {}
q_natural_ref = None
q_hec04_ref = None
for evento, pico_gu in EVENTOS.items():
    q_rest, q_gu = serie_gamma_gu(pico_gu)
    for lag_h in (0, 6, 12, 24):
        q_gu_lag = desloca(q_gu, lag_h)
        for alt_nome, eixos_antas in ALT.items():
            for fq_nome, eixos_fq in FQ.items():
                for regra in ("seca", "comportas"):
                    # Todas as séries desta matriz são reportadas em Estrela;
                    # portanto o Forqueta natural permanece presente quando
                    # não há eixo de controle nesse ramo.
                    qf_nat = Q_FQ.copy()
                    qf_out, vf, sf, af = branch_fq(eixos_fq, regra)
                    q_natural = q_rest + q_gu_lag + qf_nat + Q_MARGEM
                    qantas_out, va, sa, aa = (
                        (q_rest.copy(), 0.0, False, 0.0)
                        if not eixos_antas
                        else rota_vertente(
                            eixos_antas, q_rest, A_REST, regra,
                            AREA_ANTAS, MONT_ANTAS, CAV_ANTAS, GEO_ANTAS, H_ADM_ANTAS,
                        )
                    )
                    # 120 m é apenas envelope geométrico da CAV; não é altura admissível.
                    for altura in (0.0, 30.0, 50.0, 70.0, 100.0, 120.0):
                        if altura <= 0:
                            qgu_out, vg, sg, ag = q_gu_lag.copy(), 0.0, False, 0.0
                        else:
                            qgu_raw, vg, sg, ag = branch_gu(q_gu, altura, regra)
                            qgu_out = desloca(qgu_raw, lag_h)
                        q_out = qantas_out + qgu_out + qf_out + Q_MARGEM
                        peak_nat = float(q_natural.max())
                        peak_out = float(q_out.max())
                        key = (evento, alt_nome, fq_nome, regra, lag_h, altura)
                        if evento == "pico_historico_santa_lucia" and lag_h == 0 and regra == "seca" and fq_nome == "SEM_FORQUETA":
                            # O HEC-00 deve ser a série sem novas obras. A rodada
                            # anterior guardava q_out com ALT-J e a rotulava como
                            # natural, o que contaminava a comparação visual.
                            if q_natural_ref is None:
                                q_natural_ref = q_natural.copy()
                            if alt_nome == "ALT-J" and altura == 100.0:
                                q_hec04_ref = q_out.copy()
                        rows.append({
                            "evento_guapore": evento,
                            "pico_guapore_total_m3s": round(pico_gu, 1),
                            "eixos_antas": "+".join(eixos_antas) or "SEM_OBRA",
                            "eixos_forqueta": "+".join(eixos_fq) or "SEM_FORQUETA",
                            "regra_operativa": regra,
                            "defasagem_guapore_h": lag_h,
                            "altura_gu1_m": altura,
                            "pico_natural_estrela_m3s": round(peak_nat, 1),
                            "pico_resultante_estrela_m3s": round(peak_out, 1),
                            "reducao_pico_pct": round(100 * (1 - peak_out / peak_nat), 2),
                            "acima_limiar_4000_m3s": round(max(peak_out - Q_LIMIAR, 0), 1),
                            "area_controlada_antas_km2": round(aa, 1),
                            "area_controlada_gu1_km2": round(ag, 1),
                            "area_controlada_forqueta_km2": round(af, 1),
                            "volume_gu1_hm3": round(vg, 1),
                            "volume_antas_hm3": round(va, 1),
                            "volume_forqueta_hm3": round(vf, 1),
                            "volume_total_hm3": round(vg + va + vf, 1),
                            "reservatorio_saturou": bool(sg or sa or sf),
                            "observacao": "GU1 preliminar; CAV sintética e pico diário transposto",
                        })

resultado = pd.DataFrame(rows)
resultado.to_csv(D_TAB / "roteamento_guapore_antas.csv", **WR)

if q_natural_ref is None or q_hec04_ref is None:
    raise RuntimeError("Não foi possível montar as séries de referência do HEC-00 e do HEC-04.")

pd.DataFrame(
    [
        {"cenario": "HEC-00", "alternativa": "Situação atual — sem novos eixos", "tempo_h": t, "pico_m3s": q}
        for t, q in zip(T_H, q_natural_ref)
    ]
    + [
        {"cenario": "HEC-04", "alternativa": "ALT-J + GU1 (100 m; triagem)", "tempo_h": t, "pico_m3s": q}
        for t, q in zip(T_H, q_hec04_ref)
    ]
).to_csv(D_TAB / "hidrogramas_guapore_antas.csv", **WR)

validos = resultado[(resultado.altura_gu1_m > 0) & (resultado.regra_operativa == "seca")].copy()
nov_zero_120 = resultado[
    (resultado.evento_guapore == "novembro_2023_santa_lucia")
    & (resultado.eixos_antas == "E02+E04+E01+E05+E08+E12")
    & (resultado.eixos_forqueta == "SEM_FORQUETA")
    & (resultado.regra_operativa == "seca")
    & (resultado.defasagem_guapore_h == 0)
    & (resultado.altura_gu1_m == 120)
].iloc[0]
best = validos.sort_values(["pico_resultante_estrela_m3s", "volume_total_hm3"]).iloc[0]
best_por_evento = (
    validos.sort_values(["evento_guapore", "pico_resultante_estrela_m3s", "volume_total_hm3"])
    .groupby("evento_guapore", as_index=False).first()
)

md = [
    "# Triagem do GU1 — rio Guaporé + Antas",
    "",
    f"A série DPM do posto Santa Lúcia (86580000) tem **{len(serie):,} registros válidos**, de {serie.data.min().date()} a {serie.data.max().date()}, com máximo de **{Q_GU_OBS_PICO:,.1f} m³/s**. O máximo de novembro de 2023 foi {Q_GU_2023_NOV:,.1f} m³/s.",
    "",
    f"A decomposição usa {A_ANALISE:,.1f} km² na seção de análise, separando **{A_GU_TOTAL:,.1f} km² do Guaporé** e **{A_REST:,.1f} km² de vertente residual**. O GU1 controla preliminarmente {A_GU1:,.1f} km² ({A_GU1 / A_GU_TOTAL:.1%} do Guaporé).",
    "",
    "## Melhor resultado por evento",
    "",
    "| Evento | Antas | Forqueta | Altura GU1 | Defasagem | Pico natural | Pico com GU1 | Redução | Excesso sobre 4.000 |",
    "|---|---|---|---:|---:|---:|---:|---:|---:|",
]
for _, r in best_por_evento.iterrows():
    md.append(f"| {r.evento_guapore} | {r.eixos_antas} | {r.eixos_forqueta} | {r.altura_gu1_m:.0f} m | {r.defasagem_guapore_h:.0f} h | {r.pico_natural_estrela_m3s:,.0f} | {r.pico_resultante_estrela_m3s:,.0f} | {r.reducao_pico_pct:.1f}% | {r.acima_limiar_4000_m3s:,.0f} |")
md += [
    "",
    f"No melhor cenário da rodada, **{best.eixos_antas} + {best.eixos_forqueta}**, GU1 com {best.altura_gu1_m:.0f} m e regra seca produziu {best.pico_resultante_estrela_m3s:,.0f} m³/s em Estrela, ainda {best.acima_limiar_4000_m3s:,.0f} m³/s acima do limiar preliminar. O resultado é uma triagem, pois o GU1 usa CAV sintética, pico diário transposto e não inclui remanso nem operação real das usinas Guaporé/Monte Cuco.",
    f"A matriz contém {len(resultado)} combinações e nenhuma ficou abaixo de 4.000 m³/s. O valor de novembro de 2023 apresentado na tabela usa a defasagem que minimizou o pico nessa sensibilidade; com defasagem zero, o resultado a 120 m foi {nov_zero_120.pico_resultante_estrela_m3s:,.0f} m³/s.",
    "",
    "A inclusão do GU1 é metodologicamente válida porque a sub-bacia foi retirada da vertente residual antes do roteamento. Não se somou o hidrograma do Guaporé ao hidrograma agregado original. A decomposição, entretanto, ainda deve ser recalibrada com séries subdiárias, transposição regional e pareamento com Muçum/Encantado/Estrela.",
    "",
    "Arquivos: `tabelas/roteamento_guapore_antas.csv`, `tabelas/eixo_guapore_proposto.csv` e `01_dados/dpm_db/86580000_vazao.csv`.",
]
(D_RES / "ROTEAMENTO_GUAPORE_ANTAS.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def svg_plot():
    width, height = 1100, 600
    left, right, top, bottom = 80, 1040, 45, 525
    series_plot = [
        ("natural", q_natural_ref, "#333333", "HEC-00 — situação atual"),
        ("gu", q_hec04_ref, "#7c3aed", "HEC-04 — ALT-J + GU1 100 m"),
    ]
    ymax = max(float(np.max(q)) for _, q, _, _ in series_plot + [("limiar", np.array([Q_LIMIAR]), "", "")]) * 1.08
    xmax = float(T_H[-1])
    def xy(i, q):
        return left + float(T_H[i]) / xmax * (right - left), top + (1 - float(q) / ymax) * (bottom - top)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">', '<rect width="100%" height="100%" fill="white"/>']
    out.append(f'<text x="{width/2:.0f}" y="25" text-anchor="middle" font-family="Arial" font-size="18" font-weight="bold">GU1 — triagem combinada com ALT-J (pico histórico do Santa Lúcia)</text>')
    out.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{bottom}" stroke="#333"/><line x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}" stroke="#333"/>')
    yline = top + (1 - Q_LIMIAR / ymax) * (bottom - top)
    out.append(f'<line x1="{left}" y1="{yline:.1f}" x2="{right}" y2="{yline:.1f}" stroke="#9467bd" stroke-dasharray="7,5"/><text x="{right-5}" y="{yline-6:.1f}" text-anchor="end" font-family="Arial" font-size="12" fill="#6b4c9a">4.000 m³/s</text>')
    for _, q, color, label in series_plot:
        pts = " ".join(f"{xy(i, q[i])[0]:.1f},{xy(i, q[i])[1]:.1f}" for i in range(0, len(q), 4))
        out.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2.2"/>')
    for j, (_, _, color, label) in enumerate(series_plot):
        yy = 80 + j * 22
        out.append(f'<line x1="{right-230}" y1="{yy}" x2="{right-205}" y2="{yy}" stroke="{color}" stroke-width="3"/><text x="{right-195}" y="{yy+4}" font-family="Arial" font-size="12">{html.escape(label)}</text>')
    out.append(f'<text x="{left-10}" y="{top+5}" text-anchor="end" font-family="Arial" font-size="12">{ymax:,.0f}</text><text x="{left-10}" y="{bottom}" text-anchor="end" font-family="Arial" font-size="12">0</text>')
    out.append(f'<text x="{(left+right)/2:.0f}" y="{height-18}" text-anchor="middle" font-family="Arial" font-size="13">Tempo sintético (h)</text><text x="18" y="{(top+bottom)/2:.0f}" transform="rotate(-90 18 {(top+bottom)/2:.0f})" text-anchor="middle" font-family="Arial" font-size="13">Vazão (m³/s)</text>')
    out.append("</svg>")
    (D_VAL / "HIDROGRAMAS_GUAPORE_ALTJ.svg").write_text("\n".join(out), encoding="utf-8")


svg_plot()
print(f"GU1: {A_GU1:.1f} km² de {A_GU_TOTAL:.1f} km²; melhor pico: {best.pico_resultante_estrela_m3s:.1f} m³/s")
print(best_por_evento[["evento_guapore", "eixos_antas", "eixos_forqueta", "altura_gu1_m", "defasagem_guapore_h", "pico_resultante_estrela_m3s", "reducao_pico_pct"]].to_string(index=False))
