# -*- coding: utf-8 -*-
"""
Roteamento preliminar de barragens com comportas em rede/cascata.

Ferramenta de sensibilidade, não modelo de projeto. Usa a rede imediata D8/BHO,
CAVs PCHIP dos eixos novos, hidrograma sintético e uma regra simples de
comportas para impedir que o benefício seja estimado pela soma independente
dos volumes.

Hipóteses substituíveis: 18.000 m3/s, 260 mm, 4.000 m3/s, 6 h de viagem entre
conexões, reservatório inicial em 35% da altura, deplecionamento de 5 m, área
de comporta de fundo de 30 m2 e meta de descarga proporcional à área.
"""

from pathlib import Path
import math
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
D_CAV = ROOT / "01_dados" / "cav"
D_RES = ROOT / "06_resultados"
D_TAB = D_RES / "tabelas"
D_TAB.mkdir(parents=True, exist_ok=True)

AREA_ESTRELA = 19_440.0
Q_PICO = 18_000.0
LAMINA_MM = 260.0
Q_SEM_DANO = 4_000.0
DT_S = 3600.0
TEMPO_VIAGEM_H = 6
FRAC_NORMAL = 0.35
DEPLEC_PREV_M = 5.0
CD = 0.61
G = 9.81
C_WEIR = 2.1
AREA_COMPORTA_M2 = 30.0


def csv_model(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, sep=";", decimal=",")


eixos = csv_model(D_CAV / "eixos_todos.csv")
topo = csv_model(D_TAB / "rede_imediata_cascatas_comportas.csv")
cav = csv_model(D_RES / "tabelas" / "cav_eixos_novos_interpolada_1m.csv")
geo = csv_model(D_CAV / "geometria_todos.csv")
ficha = csv_model(ROOT / "06_resultados" / "CLAUDE" / "claude_eixos_ficha_final.csv")

area_eixo = eixos.set_index("codigo")["area_km2"].to_dict()
altura_adm = ficha.set_index("eixo")["altura_admissivel_m"].to_dict()

crista = (
    geo.sort_values("altura_m")
    .drop_duplicates("eixo", keep="last")
    .set_index("eixo")["L_crista_m"]
    .to_dict()
)

upstream = {}
for _, r in topo.iterrows():
    upstream.setdefault(r["jusante_imediato"], []).append(r["montante"])

nodes = sorted(area_eixo, key=lambda x: (area_eixo[x], x))
local_area = {}
for node in nodes:
    local_area[node] = max(
        area_eixo[node] - sum(area_eixo.get(u, 0.0) for u in upstream.get(node, [])),
        0.0,
    )


def hydrograph(area_km2: float, t_h: np.ndarray) -> np.ndarray:
    """Hidrograma gama escalado pela área incremental."""
    if area_km2 <= 0:
        return np.zeros_like(t_h)
    qpeak = Q_PICO * area_km2 / AREA_ESTRELA
    qbase = 600.0 * area_km2 / AREA_ESTRELA
    volume = LAMINA_MM / 1000.0 * area_km2 * 1e6
    m = 3.0
    fvol = math.gamma(m + 1) * np.exp(m) / m ** (m + 1)
    tp = volume / max((qpeak - qbase) * fvol, 1.0)
    x = np.maximum(t_h * 3600.0 / max(tp, 1.0), 0.0)
    q = qbase + (qpeak - qbase) * x**m * np.exp(m * (1.0 - x))
    q[~np.isfinite(q)] = qbase
    return q


T_H = np.arange(0.0, 480.0 + 1.0, 1.0)
q_local = {n: hydrograph(local_area[n], T_H) for n in nodes}
area_fora_e12 = max(AREA_ESTRELA - area_eixo.get("E12", 0.0), 0.0)
q_fora_e12 = hydrograph(area_fora_e12, T_H)

cav_por_eixo = {
    eixo: g.sort_values("altura_m")
    for eixo, g in cav.groupby("eixo", sort=False)
}


def cota_volume(eixo: str, h: float) -> float:
    g = cav_por_eixo[eixo]
    return float(np.interp(h, g["altura_m"], g["volume_hm3"])) * 1e6


def volume_cota(eixo: str, v_m3: float) -> float:
    g = cav_por_eixo[eixo]
    return float(np.interp(v_m3 / 1e6, g["volume_hm3"], g["altura_m"]))


SCENARIOS = {
    "C01": ["E02", "E04"],
    "C02": ["E02", "E04", "E12"],
    "C03": ["E02", "E04", "E08"],
    "C04": ["E09", "E10", "E11", "E12"],
    "C05": ["E01", "E02", "E04", "E08", "E09", "E10", "E11", "E12"],
}


def roteia(scenario: str, selecionados: list[str]):
    selecionados = [e for e in selecionados if e in cav_por_eixo]
    state = {}
    for eixo in selecionados:
        hmax = min(float(altura_adm[eixo]), float(cav_por_eixo[eixo]["altura_m"].max()))
        hnormal = max(min(hmax * FRAC_NORMAL, hmax - 1.0), 0.0)
        vini = cota_volume(eixo, max(hnormal - DEPLEC_PREV_M, 0.0))
        state[eixo] = {
            "hmax": hmax,
            "hnormal": hnormal,
            "vmax": cota_volume(eixo, hmax),
            "vini": vini,
            "v": vini,
            "qout": np.zeros(len(T_H)),
            "vin": np.zeros(len(T_H)),
            "vstore": np.zeros(len(T_H)),
            "h": np.zeros(len(T_H)),
            "opening": np.zeros(len(T_H)),
            "spill": np.zeros(len(T_H)),
            "saturou": False,
            "galgou": False,
        }

    lag = int(TEMPO_VIAGEM_H)
    all_qout = {n: np.zeros(len(T_H)) for n in nodes}

    for i, _ in enumerate(T_H):
        for node in nodes:
            qin = q_local[node][i]
            for up in upstream.get(node, []):
                qin += all_qout[up][i - lag] if i >= lag else 0.0
            all_qout[node][i] = qin

            if node not in state:
                continue

            st = state[node]
            h = volume_cota(node, st["v"])
            q_cap = CD * AREA_COMPORTA_M2 * np.sqrt(max(2 * G * h, 0.0))
            l_weir = min(max(crista.get(node, 100.0) * 0.35, 40.0), 120.0)
            q_cap += C_WEIR * l_weir * max(h - st["hnormal"], 0.0) ** 1.5
            q_target = Q_SEM_DANO * area_eixo[node] / AREA_ESTRELA
            qout = min(qin + st["v"] / DT_S, q_target, q_cap)
            qout = max(qout, 0.0)
            vtrial = st["v"] + (qin - qout) * DT_S
            spill = 0.0
            if vtrial > st["vmax"]:
                spill = (vtrial - st["vmax"]) / DT_S
                qout += spill
                vtrial = st["vmax"]
                st["saturou"] = True
                st["galgou"] = True
            if vtrial < 0.0:
                qout = qin + st["v"] / DT_S
                vtrial = 0.0

            opening = min(qout / max(q_cap, 1e-9), 1.0)
            st["v"] = vtrial
            st["qout"][i] = qout
            st["vin"][i] = qin
            st["vstore"][i] = vtrial
            st["h"][i] = volume_cota(node, vtrial)
            st["opening"][i] = opening
            st["spill"][i] = spill
            all_qout[node][i] = qout

    e12_q = all_qout["E12"] + q_fora_e12
    natural = hydrograph(AREA_ESTRELA, T_H)
    scenario_rows = pd.DataFrame(
        {
            "cenario": scenario,
            "tempo_h": T_H,
            "Q_natural_Estrela_m3s": natural,
            "Q_resultante_Estrela_m3s": e12_q,
            "Q_fora_E12_m3s": q_fora_e12,
        }
    )

    summary = {
        "cenario": scenario,
        "eixos_com_comportas": "+".join(selecionados),
        "pico_natural_m3s": float(natural.max()),
        "pico_resultante_m3s": float(e12_q.max()),
        "reducao_pico_pct": 100.0 * (1.0 - e12_q.max() / natural.max()),
        "volume_espera_inicial_hm3": sum(
            (st["vmax"] - st["vini"]) / 1e6 for st in state.values()
        ),
        "reservatorios_saturados": sum(st["saturou"] for st in state.values()),
        "galgamentos": sum(st["galgou"] for st in state.values()),
    }
    detalhes = []
    for eixo, st in state.items():
        detalhes.append(
            {
                "cenario": scenario,
                "eixo": eixo,
                "altura_admissivel_m": st["hmax"],
                "NA_normal_relativo_m": st["hnormal"],
                "volume_espera_inicial_hm3": (st["vmax"] - st["vini"]) / 1e6,
                "pico_afluente_m3s": st["vin"].max(),
                "pico_efluente_m3s": st["qout"].max(),
                "volume_maximo_hm3": st["vstore"].max() / 1e6,
                "NA_maximo_relativo_m": st["h"].max(),
                "abertura_maxima": st["opening"].max(),
                "saturou": st["saturou"],
                "galgou": st["galgou"],
            }
        )
    return scenario_rows, summary, detalhes


all_summary = []
all_detail = []
all_hydro = []
for scenario, axes in SCENARIOS.items():
    h, s, d = roteia(scenario, axes)
    all_hydro.append(h)
    all_summary.append(s)
    all_detail.extend(d)

pd.DataFrame(all_summary).to_csv(
    D_TAB / "roteamento_cascata_comportas_triagem.csv",
    sep=";",
    decimal=",",
    index=False,
)
pd.DataFrame(all_detail).to_csv(
    D_TAB / "roteamento_cascata_comportas_detalhe.csv",
    sep=";",
    decimal=",",
    index=False,
)
pd.concat(all_hydro, ignore_index=True).to_csv(
    D_TAB / "hidrogramas_cascatas_comportas_triagem.csv",
    sep=";",
    decimal=",",
    index=False,
)

summary_df = pd.DataFrame(all_summary)
md = [
    "# Roteamento preliminar de cascatas com comportas",
    "",
    "> **Triagem de sensibilidade.** Os resultados abaixo usam hidrograma sintético, CAVs de classe B, tempo de viagem fixo de 6 h, regra de descarga simplificada e parâmetros de comporta não calibrados. Não são dimensionamento, orçamento nem seleção final.",
    "",
    "| Cenário | Eixos com comportas | Pico resultante (m³/s) | Redução do pico | Volume de espera inicial (hm³) | Saturados | Galgamentos |",
    "|---|---|---:|---:|---:|---:|---:|",
]
for _, r in summary_df.iterrows():
    md.append(
        f"| {r.cenario} | {r.eixos_com_comportas} | {r.pico_resultante_m3s:,.0f} | {r.reducao_pico_pct:,.1f}% | {r.volume_espera_inicial_hm3:,.0f} | {int(r.reservatorios_saturados)} | {int(r.galgamentos)} |"
        .replace(",", "X").replace(".", ",").replace("X", ".")
    )
md += [
    "",
    "A leitura preliminar é que a operação em cascata pode aumentar o efeito do arranjo-base, mas o benefício depende da coordenação e da não saturação dos reservatórios. C04, que concentra apenas os eixos da cascata principal, satura todos os reservatórios e tem desempenho baixo. C05 apresenta maior redução neste conjunto de hipóteses, mas inclui um galgamento e o eixo E10, que está fora da carteira principal por balanço energético negativo.",
    "",
    "A próxima rodada deve substituir as hipóteses por séries ANA/ONS, regras operativas, tempos de viagem por trecho, curvas de descarga, níveis de segurança e remanso HEC-RAS 1D.",
    "",
]
(D_RES / "CASCATAS_COMPORTAS_TRIAGEM.md").write_text("\n".join(md), encoding="utf-8")

print("Roteamento preliminar de cascatas com comportas")
print(summary_df.to_string(index=False, float_format=lambda x: f"{x:,.1f}"))
