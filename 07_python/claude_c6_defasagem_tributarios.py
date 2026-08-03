# -*- coding: utf-8 -*-
"""
EUROCLIMA / Estrela-RS — C6: DEFASAGEM E PESO DOS TRIBUTARIOS.

Substitui a decomposicao PURAMENTE PROPORCIONAL A AREA usada em C1/C4 por uma
decomposicao calibrada com os dados observados, e introduz a defasagem entre a
contribuicao de montante e a dos tributarios de jusante.

POR QUE ISSO IMPORTA
--------------------
O pareamento de eventos (claude_c8) mostrou que a razao de vazao entre Estrela
e Mucum varia de 1,14 a 1,89 conforme onde chove:

    set/2023  Mucum 15.092 -> Estrela 17.145   razao 1,14
    nov/2023  Mucum  9.401 -> Estrela 17.261   razao 1,84

Mucum drena 16.000 dos 22.472 km2 do posto de Estrela, ou seja 71% da area.
Mas contribuiu com 88% do pico em setembro e apenas 54% em novembro. A
decomposicao proporcional a area, usada ate aqui, corresponde ao caso
intermediario e SUBESTIMA o peso dos tributarios nos eventos em que eles
dominam.

Como todos os eixos da carteira (E01 a E12) estao a MONTANTE, quanto mais o
evento for dominado pelos tributarios de jusante, MENOS as barragens podem
fazer. Este script quantifica esse efeito.

CENARIOS DE DISTRIBUICAO
------------------------
  'proporcional'   — peso = fracao de area (o que C1/C4 usaram)
  'montante'       — calibrado no evento de set/2023 (montante domina)
  'jusante'        — calibrado no evento de nov/2023 (tributarios dominam)

DEFASAGEM
---------
A defasagem observada entre os picos de Mucum e Estrela e' de 0 dias na
resolucao diaria disponivel, ou seja inferior a ~24 h. Adota-se o tempo de
translacao estimado pela celeridade cinematica ao longo do talvegue, com
sensibilidade.

Saidas: claude_c6_pesos_cenarios.csv, claude_c6_roteamento_com_defasagem.csv
"""
import os, time, math, warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd

DEST = os.path.join(os.environ["EURO"], "05_MODELAGEM")
D_CAV = os.path.join(DEST, "01_dados", "cav")
D_TAB = os.path.join(DEST, "06_resultados", "tabelas")
D_OUT = os.path.join(DEST, "06_resultados", "CLAUDE")
RD = dict(sep=";", decimal=",", encoding="utf-8-sig")
os.makedirs(D_OUT, exist_ok=True)

t0 = time.time()
def log(*a): print(f"[{time.time()-t0:6.1f}s]", *a, flush=True)

PAR = dict(
    AREA_ESTRELA = 19440.0,
    Q_PICO       = 16300.0,   # calibrado em C3
    Q_BASE       = 926.0,
    LAMINA_MM    = 227.0,
    Q_SEM_DANO   = 4000.0,
    DT_H         = 1.0,
    FORMA_M      = 3.0,
)
EXCLUIDOS = ["E10"]

# =============================================================================
# 1. PESOS OBSERVADOS
# =============================================================================
AREA_MUCUM, AREA_POSTO_ES = 16000.0, 22472.0
EVENTOS_OBS = [
    dict(evento="set/2023", q_mucum=15092.3, q_estrela=17145.1),
    dict(evento="nov/2023", q_mucum=9401.1,  q_estrela=17260.9),
]
frac_area_mucum = AREA_MUCUM / AREA_POSTO_ES

pesos = []
for e in EVENTOS_OBS:
    fp = e["q_mucum"] / e["q_estrela"]        # fracao do pico vinda de montante
    pesos.append(dict(
        evento=e["evento"], q_mucum=e["q_mucum"], q_estrela=e["q_estrela"],
        fracao_area_montante=round(frac_area_mucum, 3),
        fracao_pico_montante=round(fp, 3),
        fator_concentracao=round(fp / frac_area_mucum, 3)))
pesos.append(dict(evento="proporcional (C1/C4)", q_mucum=np.nan, q_estrela=np.nan,
                  fracao_area_montante=round(frac_area_mucum, 3),
                  fracao_pico_montante=round(frac_area_mucum, 3),
                  fator_concentracao=1.0))
pz = pd.DataFrame(pesos)
pz.to_csv(os.path.join(D_OUT, "claude_c6_pesos_cenarios.csv"),
          index=False, sep=";", decimal=",")

pd.set_option("display.width", 200)
print("=" * 110)
print("1. PESO DA CONTRIBUICAO DE MONTANTE — observado x proporcional")
print("=" * 110)
print(pz.to_string(index=False))
print("\n  fator_concentracao = fracao do pico / fracao da area.")
print("  Acima de 1: montante contribui mais que a sua area sugere.")
print("  Abaixo de 1: tributarios de jusante dominam.")

# fatores a aplicar sobre a parcela CONTROLADA (que esta toda a montante)
FATORES = {
    "proporcional": 1.000,
    "montante domina (set/2023)": float(pz.loc[pz.evento == "set/2023",
                                               "fator_concentracao"].iloc[0]),
    "jusante domina (nov/2023)": float(pz.loc[pz.evento == "nov/2023",
                                              "fator_concentracao"].iloc[0]),
}
log(f"fatores de concentracao: { {k: round(v,3) for k,v in FATORES.items()} }")

# =============================================================================
# 2. ENTRADAS DO ROTEAMENTO
# =============================================================================
rev = pd.read_csv(os.path.join(D_OUT, "claude_altura_admissivel_revisada.csv"), **RD)
cav = pd.read_csv(os.path.join(D_TAB, "cav_eixos_novos_interpolada_1m.csv"), **RD)
eix = pd.read_csv(os.path.join(D_CAV, "eixos_todos.csv"), **RD)
topo = pd.read_csv(os.path.join(D_CAV, "topologia_eixos.csv"), **RD)
geo = pd.read_csv(os.path.join(D_CAV, "geometria_todos.csv"), **RD)
AREA = dict(zip(eix.codigo, eix.area_km2))
H_ADM = dict(zip(rev.eixo, rev.altura_max_m))
MONT = {e: set(topo.loc[topo.eixo == e, "montante"]) for e in eix.codigo}

def mont_imed(e, conj):
    ms = [m for m in conj if m != e and m in MONT.get(e, set())]
    return [m for m in ms if not any(o in MONT.get(m, set()) for o in ms)]
def area_inc(e, conj):
    return AREA[e] - sum(AREA[m] for m in mont_imed(e, conj))
def jus(e, conj):
    return [o for o in conj if o != e and e in MONT.get(o, set())]

def hidrograma(qp, area=None, lam=None):
    area = area or PAR["AREA_ESTRELA"]; lam = lam or PAR["LAMINA_MM"]
    Vt = lam / 1000 * area * 1e6; m = PAR["FORMA_M"]
    fV = math.gamma(m + 1) * np.exp(m) / m ** (m + 1)
    qb = PAR["Q_BASE"] * area / PAR["AREA_ESTRELA"]
    tp = Vt / ((qp - qb) * fV)
    t = np.arange(0, 10 * tp, PAR["DT_H"] * 3600)
    q = qb + (qp - qb) * (t / tp) ** m * np.exp(m * (1 - t / tp))
    q[~np.isfinite(q)] = qb
    return t / 3600, q

T_H, Q_NAT = hidrograma(PAR["Q_PICO"])
PICO_NAT = float(Q_NAT.max())
N = len(T_H)

def desloca(q, horas):
    """Aplica defasagem temporal, preenchendo com a vazao de base."""
    k = int(round(horas / PAR["DT_H"]))
    if k <= 0: return q.copy()
    out = np.full_like(q, q[0]); out[k:] = q[:-k]
    return out

def vertedouro(h, hs, L, C=2.1): return C * L * max(h - hs, 0.0) ** 1.5
def orificio(h, A, Cd=0.62): return Cd * A * np.sqrt(2 * 9.81 * h) if h > 0 else 0.0
def A_para_Q(Q, carga, Cd=0.62): return Q / (Cd * np.sqrt(2 * 9.81 * max(carga, 1.0)))

def rotear(hin, cv, H, Q_meta, L_sol):
    """Barragem seca — a regra que se mostrou eficaz em C1/C4."""
    dt = PAR["DT_H"] * 3600
    cv = cv.sort_values("altura_m")
    V_de_h = lambda h: float(np.interp(h, cv.altura_m, cv.volume_hm3)) * 1e6
    h_de_V = lambda V: float(np.interp(V / 1e6, cv.volume_hm3, cv.altura_m))
    V_max = V_de_h(H); h_sol = H - 4; A_f = A_para_Q(Q_meta, H / 2)
    n = len(hin); V = np.zeros(n); h = np.zeros(n); Qo = np.zeros(n); sat = False
    for i in range(1, n):
        I = (hin[i - 1] + hin[i]) / 2
        Vp, hp = V[i - 1], h[i - 1]
        cap = vertedouro(hp, h_sol, L_sol) + orificio(hp, A_f)
        Qt = min(cap, I) if Vp >= V_max * 0.995 else min(Q_meta, cap)
        if Vp >= V_max * 0.995: sat = True
        else:
            ocup = (Vp - 0.0) / max(V_max, 1.0)
            if ocup > 0.85: Qt = min(cap, max(Q_meta, I * (ocup - 0.85) / 0.15))
        Vn = Vp + (I - Qt) * dt
        if Vn > V_max: Qt = max(Qt, I); Vn = min(Vp + (I - Qt) * dt, V_max); sat = True
        if Vn < 0: Qt = max(Qt + Vn / dt, 0.0); Vn = 0.0
        V[i] = Vn; h[i] = h_de_V(Vn); Qo[i] = Qt
    return Qo, float(V.max() / 1e6), sat

def avalia(conj, fator, lag_h):
    """Roteia respeitando topologia, peso de concentracao e defasagem."""
    conj = [e for e in conj if e not in EXCLUIDOS]
    ordem = sorted(conj, key=lambda e: AREA[e])
    # parcela controlada recebe o FATOR; a livre recebe o complemento, de modo
    # que a soma continue reproduzindo o pico natural
    terminais = [e for e in conj if not jus(e, conj)]
    A_ctrl = sum(AREA[e] for e in terminais)
    f_ctrl = A_ctrl / PAR["AREA_ESTRELA"]
    p_ctrl = min(f_ctrl * fator, 0.98)          # fracao do pico vinda do controlado
    p_livre = 1.0 - p_ctrl
    esc_ctrl = p_ctrl / f_ctrl if f_ctrl > 0 else 1.0
    f_livre = 1.0 - f_ctrl
    esc_livre = p_livre / f_livre if f_livre > 0 else 1.0

    efl, vols, sat = {}, 0.0, False
    for e in ordem:
        inc = area_inc(e, conj)
        hin = Q_NAT * (inc / PAR["AREA_ESTRELA"]) * esc_ctrl
        for m in mont_imed(e, conj):
            hin = hin + efl[m]
        H = float(H_ADM[e]); cv = cav[cav.eixo == e]
        if not len(cv) or not np.isfinite(H) or H <= 0:
            efl[e] = hin; continue
        L_cr = float(np.interp(H, geo[geo.eixo == e].altura_m,
                               geo[geo.eixo == e].L_crista_m))
        Qm = PAR["Q_SEM_DANO"] * AREA[e] / PAR["AREA_ESTRELA"]
        Qo, v, s = rotear(hin, cv, H, Qm, max(L_cr * 0.25, 40.0))
        efl[e] = Qo; vols += v; sat = sat or s

    # a parcela nao controlada chega DEFASADA em relacao a de montante
    q_livre = desloca(Q_NAT * f_livre * esc_livre, -lag_h if lag_h < 0 else 0)
    q_est = q_livre.copy()
    for e in terminais:
        q_est = q_est + desloca(efl[e], max(lag_h, 0))
    return float(q_est.max()), vols, sat, A_ctrl

# =============================================================================
# 3. VARREDURA
# =============================================================================
ALTERNATIVAS = {
    "ALT-A — E02 + E04": ["E02", "E04"],
    "ALT-D — E02 + E04 + E08": ["E02", "E04", "E08"],
    "ALT-E — E02 + E04 + E12": ["E02", "E04", "E12"],
    "ALT-J — carteira completa": ["E02", "E04", "E01", "E05", "E08", "E12"],
}
LAGS_H = [0, 6, 12, 24]

log("roteando com pesos e defasagens...")
regs = []
for nome, conj in ALTERNATIVAS.items():
    for cen, fator in FATORES.items():
        for lag in LAGS_H:
            pico, vol, sat, A_ctrl = avalia(conj, fator, lag)
            regs.append(dict(
                alternativa=nome, cenario_distribuicao=cen,
                fator_concentracao=round(fator, 3),
                defasagem_h=lag,
                area_controlada_km2=round(A_ctrl),
                pct_bacia=round(100 * A_ctrl / PAR["AREA_ESTRELA"], 1),
                volume_usado_hm3=round(vol, 1),
                pico_m3s=round(pico),
                reducao_pct=round(100 * (1 - pico / PICO_NAT), 1),
                saturou=sat))
rd = pd.DataFrame(regs)
rd.to_csv(os.path.join(D_OUT, "claude_c6_roteamento_com_defasagem.csv"),
          index=False, sep=";", decimal=",")

print("\n" + "=" * 110)
print("2. REDUCAO DE PICO POR CENARIO DE DISTRIBUICAO (defasagem 0 h)")
print("=" * 110)
p0 = rd[rd.defasagem_h == 0].pivot(index="alternativa",
                                   columns="cenario_distribuicao",
                                   values="reducao_pct")
print(p0.to_string())

print("\n" + "=" * 110)
print("3. EFEITO DA DEFASAGEM (cenario proporcional)")
print("=" * 110)
pl = rd[rd.cenario_distribuicao == "proporcional"].pivot(
    index="alternativa", columns="defasagem_h", values="reducao_pct")
print(pl.to_string())

print("\n" + "-" * 110)
print("LEITURA")
print("-" * 110)
alt = "ALT-A — E02 + E04"
s = rd[(rd.alternativa == alt) & (rd.defasagem_h == 0)]
for _, r in s.iterrows():
    print(f"  {alt} | {r.cenario_distribuicao:<32} reducao {r.reducao_pct:>5.1f}% "
          f"(pico {r.pico_m3s:,.0f} m3/s)")
faixa = s.reducao_pct
print(f"\n  A eficacia de E02+E04 varia de {faixa.min():.1f}% a {faixa.max():.1f}% "
      f"conforme a distribuicao espacial da chuva.")
print("  Isso NAO e' incerteza de modelo: e' variabilidade real do fenomeno.")
print("  Todos os eixos da carteira estao a montante; quando os tributarios de")
print("  jusante dominam, as barragens controlam menos do que a area sugere.")
log("FIM")
