# -*- coding: utf-8 -*-
"""
EUROCLIMA / Estrela-RS — ROTEAMENTO COM OS EIXOS DO FORQUETA (FQ1 / FQ2).

Atende ao PLANO_FORQUETA_CODEX_CLAUDE.md, itens 1 a 6 da coluna Claude.

DUAS CORRECOES ESTRUTURAIS EM RELACAO A C1/C4
---------------------------------------------
1. DOMINIO. Todo o roteamento anterior teve como exutorio o inicio do trecho
   modelado, 19.440 km2. O rio Forqueta (2.845,6 km2) desagua ABAIXO desse
   ponto: 19.440 + 2.845,6 = 22.286 km2, contra 22.472 km2 medidos no posto de
   Estrela (86879300). A diferenca de 186 km2 e' area incremental de margem.
   Logo, no dominio de 19.440 km2 os eixos do Forqueta seriam invisiveis. Este
   script move o exutorio para o POSTO DE ESTRELA, 22.472 km2.

   Consequencia de projeto: os eixos do Antas (E01..E12) e os do Forqueta
   protegem trechos COMPLEMENTARES. Mucum e Encantado so' dependem do Antas;
   Lajeado, Estrela e Bom Retiro do Sul recebem as duas contribuicoes.

2. DECOMPOSICAO. C1/C4 repartiam o hidrograma natural proporcionalmente a area.
   claude_c6 mostrou que a repartição real varia por evento (o Forqueta e' mais
   rapido e mais ingreme, e pode dominar). Aqui o Forqueta tem hidrograma
   PROPRIO, com tempo de pico proprio, somado COM DEFASAGEM.

CODIGOS — ARMADILHA
-------------------
O pipeline isolado em 01_dados/cav_forqueta/ RENUMEROU os eixos: ali FQ1 recebeu
o codigo 'E02' e FQ2 o codigo 'E01', que no pipeline canonico designam eixos
completamente diferentes no rio das Antas. O rotulo '#NN' do KMZ tambem mudou.
A juncao aqui e' feita por AREA DE DRENAGEM (tolerancia 2 km2), unica chave
estavel entre os dois pipelines, e os eixos do Forqueta recebem os codigos
proprios FQ1 e FQ2.

Saidas em 06_resultados/CLAUDE/:
  claude_fq_roteamento_calibrado.csv    cenarios do plano
  claude_fq_hidrogramas.csv             hidrogramas dos cenarios
  claude_fq_sensibilidade_defasagem.csv sensibilidade ao lag
  claude_fq_altura_volume.csv           varredura de altura de FQ1 e FQ2
  claude_fq_mapa_codigos.csv            de-para dos codigos entre pipelines
"""
import os, time, math, warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd

DEST = os.path.join(os.environ["EURO"], "05_MODELAGEM")
D_CAV = os.path.join(DEST, "01_dados", "cav")
D_FQ  = os.path.join(DEST, "01_dados", "cav_forqueta")
D_OUT = os.path.join(DEST, "06_resultados", "CLAUDE")
RD = dict(sep=";", decimal=",", encoding="utf-8-sig")
os.makedirs(D_OUT, exist_ok=True)

t0 = time.time()
def log(*a): print(f"[{time.time()-t0:6.1f}s]", *a, flush=True)
pd.set_option("display.width", 220)

# =============================================================================
# PARAMETROS
# =============================================================================
A_ANALISE  = 19440.0    # km2 — inicio do trecho modelado (dominio de C1/C4)
A_FORQUETA = 2845.6     # km2 — bacia total do Forqueta
A_ESTRELA  = 22472.0    # km2 — posto 86879300, novo exutorio
A_MARGEM   = A_ESTRELA - A_ANALISE - A_FORQUETA

Q_PICO_ANTAS = 16300.0  # m3/s em 19.440 km2 — calibrado em C3/C4
Q_BASE_TOT   = 926.0    # m3/s
LAMINA_MM    = 227.0    # mm — calibrado em C3/C4
Q_SEM_DANO   = 4000.0   # m3/s no ponto de analise
DT_H         = 1.0
FORMA_M      = 3.0

# --- pico de projeto do Forqueta ---------------------------------------------
# Duas fontes, ambas mantidas para comparacao:
#  (a) REGIONALIZADO — rendimento especifico do Antas corrigido por A^-0.15.
#      Era a unica disponivel antes de claude_fq_baixa_serie.py.
#  (b) MEDIDO — maxima de 68,7 anos em PASSO DO COIMBRA (86745000, 791 km2),
#      1.292 m3/s, transposta para 2.845,6 km2 com expoente 0,85 (fator 2,969).
#      Coincide com o Gumbel de TR 100 anos daquela serie (1.289 m3/s).
EXP_RENDIMENTO = -0.15
q_esp_antas = Q_PICO_ANTAS / A_ANALISE
Q_PICO_FQ_REGIONAL = A_FORQUETA * q_esp_antas * (A_FORQUETA / A_ANALISE) ** EXP_RENDIMENTO
Q_PICO_FQ_MEDIDO   = 1292.3 * (A_FORQUETA / 791.0) ** 0.85
FONTE_PICO_FQ = "medido em Passo do Coimbra e transposto"
Q_PICO_FQ = Q_PICO_FQ_MEDIDO

EXCLUIDOS = ["E10"]     # sobreposto a E09/E11 no pipeline canonico

# =============================================================================
# 1. DE-PARA DOS CODIGOS
# =============================================================================
can = pd.read_csv(os.path.join(D_CAV, "eixos_todos.csv"), **RD)
fqe = pd.read_csv(os.path.join(D_FQ, "eixos_todos.csv"), **RD)
fqc = pd.read_csv(os.path.join(D_FQ, "cav_todos.csv"), **RD)
fqg = pd.read_csv(os.path.join(D_FQ, "geometria_todos.csv"), **RD)

mapa = []
for _, r in fqe.iterrows():
    d = (can.area_km2 - r.area_km2).abs()
    if d.min() <= 2.0:
        alvo = can.loc[d.idxmin()]
        mapa.append(dict(codigo_pipeline_fq=r.codigo, codigo_canonico=alvo.codigo,
                         area_fq_km2=r.area_km2, area_canonica_km2=alvo.area_km2,
                         origem="EUROCLIMA-rev.kmz"))
    else:
        novo = "FQ1" if r.area_km2 > 2300 else "FQ2"
        mapa.append(dict(codigo_pipeline_fq=r.codigo, codigo_canonico=novo,
                         area_fq_km2=r.area_km2, area_canonica_km2=np.nan,
                         origem="eixos_forqueta_propostos.kmz"))
mp = pd.DataFrame(mapa)
mp.to_csv(os.path.join(D_OUT, "claude_fq_mapa_codigos.csv"),
          index=False, sep=";", decimal=",")
TRAD = dict(zip(mp.codigo_pipeline_fq, mp.codigo_canonico))

print("=" * 115)
print("1. DE-PARA DOS CODIGOS entre o pipeline canonico e o do Forqueta")
print("=" * 115)
print(mp.sort_values("area_fq_km2").to_string(index=False))
n_novos = (mp.codigo_canonico.isin(["FQ1", "FQ2"])).sum()
log(f"{len(mp)-n_novos} eixos reconciliados por area, {n_novos} novos (Forqueta)")

for df in (fqc, fqg, fqe):
    df["eixo"] = df["eixo"].map(TRAD) if "eixo" in df else df["eixo"]
fqe["codigo"] = fqe["codigo"].map(TRAD)
AREA = dict(zip(fqe.codigo, fqe.area_km2))
AREA["FQ1"] = float(fqe.loc[fqe.codigo == "FQ1", "area_km2"].iloc[0])
AREA["FQ2"] = float(fqe.loc[fqe.codigo == "FQ2", "area_km2"].iloc[0])

topo = pd.read_csv(os.path.join(D_FQ, "topologia_eixos.csv"), **RD)
topo["eixo"] = topo["eixo"].map(TRAD); topo["montante"] = topo["montante"].map(TRAD)
MONT = {c: set(topo.loc[topo.eixo == c, "montante"]) for c in fqe.codigo}
MONT.setdefault("FQ1", set()); MONT.setdefault("FQ2", set())

rev = pd.read_csv(os.path.join(D_OUT, "claude_altura_admissivel_revisada.csv"), **RD)
H_ADM = dict(zip(rev.eixo, rev.altura_max_m))

print("\n  Verificacao do Forqueta na topologia:")
print(f"    FQ1 area {AREA['FQ1']:,.1f} km2 | montantes: {sorted(MONT['FQ1']) or 'nenhum'}")
print(f"    FQ2 area {AREA['FQ2']:,.1f} km2 | montantes: {sorted(MONT['FQ2']) or 'nenhum'}")
tem_fq = [e for e in MONT if e not in ("FQ1", "FQ2") and MONT[e] & {"FQ1", "FQ2"}]
print(f"    eixos do Antas que teriam FQ1/FQ2 a montante: {tem_fq or 'nenhum'} "
      f"-> confirma tributario independente")
print(f"\n  Fechamento de areas no posto de Estrela:")
print(f"    ponto de analise {A_ANALISE:>9,.1f} + Forqueta {A_FORQUETA:>8,.1f} "
      f"+ margem {A_MARGEM:>6,.1f} = {A_ESTRELA:>9,.1f} km2")

# =============================================================================
# 2. HIDROGRAMAS DAS DUAS VERTENTES
# =============================================================================
def gamma_hidro(qp, qb, area_km2, lamina_mm, m=FORMA_M, tp_fator=1.0, n_h=400):
    """Hidrograma gama de dois parametros; tp_fator escala o tempo de pico."""
    Vt = lamina_mm / 1000 * area_km2 * 1e6
    fV = math.gamma(m + 1) * np.exp(m) / m ** (m + 1)
    tp = Vt / ((qp - qb) * fV) * tp_fator
    t = np.arange(0, n_h * 3600, DT_H * 3600)
    q = qb + (qp - qb) * (t / tp) ** m * np.exp(m * (1 - t / tp))
    q[~np.isfinite(q)] = qb
    return t / 3600.0, q, tp / 3600.0

# tempo de pico escala com A^0.3 (relacao tipo Snyder)
FATOR_TP_FQ = (A_FORQUETA / A_ANALISE) ** 0.3
qb_antas = Q_BASE_TOT * A_ANALISE / A_ESTRELA
qb_fq    = Q_BASE_TOT * A_FORQUETA / A_ESTRELA
qb_marg  = Q_BASE_TOT * A_MARGEM / A_ESTRELA

T_H, Q_ANTAS, TP_ANTAS = gamma_hidro(Q_PICO_ANTAS, qb_antas, A_ANALISE, LAMINA_MM)
_,   Q_FQ,    TP_FQ    = gamma_hidro(Q_PICO_FQ, qb_fq, A_FORQUETA, LAMINA_MM,
                                     tp_fator=FATOR_TP_FQ)
Q_MARG = np.full_like(Q_ANTAS, qb_marg) + (Q_ANTAS - qb_antas) * (A_MARGEM / A_ANALISE)
N = len(T_H)

# --- defasagem de referencia -------------------------------------------------
# A estimativa por escalonamento do tempo de pico (tp ~ A^0.3) dava
# TP_ANTAS - TP_FQ = 31 h. claude_fq_baixa_serie.py MEDIU a defasagem em 13
# eventos com dado simultaneo em Passo do Coimbra, Mucum e Estrela: mediana de
# 0 dia. Na resolucao diaria disponivel os picos sao simultaneos, e a estimativa
# de 31 h esta' fora do que os dados suportam. Adota-se 0 h como referencia; a
# estimativa teorica fica na varredura de sensibilidade.
LAG_TEORICO = round(TP_ANTAS - TP_FQ)
LAG_REF = 0
FONTE_LAG = "medida em 13 eventos (mediana 0 dia, resolucao diaria)"

print("\n" + "=" * 115)
print("2. HIDROGRAMAS DAS DUAS VERTENTES")
print("=" * 115)
print(f"  Antas    ate 19.440 km2 : pico {Q_PICO_ANTAS:>8,.0f} m3/s | tp {TP_ANTAS:>5.1f} h")
print(f"  Forqueta      2.845,6 km2: pico {Q_PICO_FQ:>8,.0f} m3/s | tp {TP_FQ:>5.1f} h "
      f"(rendimento especifico {Q_PICO_FQ/A_FORQUETA:.3f} contra "
      f"{q_esp_antas:.3f} m3/s/km2)")
print(f"    fonte do pico do Forqueta: {FONTE_PICO_FQ}")
print(f"    alternativa regionalizada: {Q_PICO_FQ_REGIONAL:,.0f} m3/s "
      f"({100*(Q_PICO_FQ_REGIONAL/Q_PICO_FQ-1):+.0f}%)")
print(f"  defasagem adotada: {LAG_REF} h — {FONTE_LAG}")
print(f"    estimativa teorica por tp ~ A^0.3 seria {LAG_TEORICO} h; "
      f"os dados NAO a sustentam")

def desloca(q, h):
    k = int(round(h / DT_H))
    if k == 0: return q.copy()
    out = np.full_like(q, q[0])
    if k > 0: out[k:] = q[:-k]
    else:     out[:k] = q[-k:]
    return out

def soma_estrela(q_antas, q_fq, lag_h):
    """Soma em Estrela: o Forqueta chega adiantado de lag_h em relacao ao Antas."""
    return q_antas + desloca(q_fq, lag_h) + Q_MARG

PICO_NAT_EST = float(soma_estrela(Q_ANTAS, Q_FQ, LAG_REF).max())
PICO_NAT_ANL = float(Q_ANTAS.max())
print(f"\n  pico natural em Estrela (22.472 km2) : {PICO_NAT_EST:,.0f} m3/s")
print(f"  maximo observado no posto (19/11/2023): 17.261 m3/s  "
      f"[diferenca {100*(PICO_NAT_EST/17260.9-1):+.1f}%]")
print(f"  pico natural no ponto de analise      : {PICO_NAT_ANL:,.0f} m3/s")

# =============================================================================
# 3. ROTEAMENTO
# =============================================================================
def vertedouro(h, hs, L, C=2.1): return C * L * max(h - hs, 0.0) ** 1.5
def orificio(h, A, Cd=0.62): return Cd * A * np.sqrt(2 * 9.81 * h) if h > 0 else 0.0
def A_para_Q(Q, carga, Cd=0.62): return Q / (Cd * np.sqrt(2 * 9.81 * max(carga, 1.0)))

def rotear(hin, cv, H, Q_meta, L_sol, regra="seca"):
    """Puls. regra: 'seca' | 'comportas' | 'convencional'."""
    dt = DT_H * 3600
    cv = cv.sort_values("altura_m")
    V_de_h = lambda h: float(np.interp(h, cv.altura_m, cv.volume_hm3)) * 1e6
    h_de_V = lambda V: float(np.interp(V / 1e6, cv.volume_hm3, cv.altura_m))
    V_max = V_de_h(H)
    if regra == "seca":
        h_sol, V0, A_f = H - 4, 0.0, A_para_Q(Q_meta, H / 2)
    elif regra == "comportas":
        # NA normal a 70% da altura; volume de espera acima
        h_sol, V0 = 0.70 * H, V_de_h(0.70 * H)
        A_f = A_para_Q(Q_meta, H * 0.35)
    else:                              # convencional: reservatorio cheio
        h_sol, V0, A_f = 0.95 * H, V_de_h(0.95 * H), 0.0
    n = len(hin); V = np.zeros(n); h = np.zeros(n); Qo = np.zeros(n); sat = False
    V[0], h[0] = V0, h_de_V(V0)
    for i in range(1, n):
        I = (hin[i - 1] + hin[i]) / 2
        Vp, hp = V[i - 1], h[i - 1]
        cap = vertedouro(hp, h_sol, L_sol) + orificio(hp, A_f)
        cheio = Vp >= V_max * 0.995
        if cheio:
            Qt = min(cap, I); sat = True
        else:
            Qt = min(Q_meta, cap)
            ocup = Vp / max(V_max, 1.0)
            if ocup > 0.85:
                Qt = min(cap, max(Q_meta, I * (ocup - 0.85) / 0.15))
        Vn = Vp + (I - Qt) * dt
        if Vn > V_max:
            Qt = max(Qt, I); Vn = min(Vp + (I - Qt) * dt, V_max); sat = True
        if Vn < V0: Qt = max(Qt + (Vn - V0) / dt, 0.0); Vn = V0
        V[i] = Vn; h[i] = h_de_V(Vn); Qo[i] = Qt
    return Qo, float((V.max() - V0) / 1e6), sat

def mont_imed(e, conj):
    ms = [m for m in conj if m != e and m in MONT.get(e, set())]
    return [m for m in ms if not any(o in MONT.get(m, set()) for o in ms)]
def jus(e, conj):
    return [o for o in conj if o != e and e in MONT.get(o, set())]

def rota_vertente(conj, q_nat, area_ref, regra):
    """Roteia um conjunto de eixos dentro de UMA vertente."""
    conj = [e for e in conj if e not in EXCLUIDOS]
    if not conj: return q_nat.copy(), 0.0, False
    efl, vol, sat = {}, 0.0, False
    for e in sorted(conj, key=lambda x: AREA[x]):
        inc = AREA[e] - sum(AREA[m] for m in mont_imed(e, conj))
        hin = q_nat * (inc / area_ref)
        for m in mont_imed(e, conj): hin = hin + efl[m]
        cv = fqc[fqc.eixo == e]; g = fqg[fqg.eixo == e]
        H = float(H_ADM.get(e, np.nan))
        if e in ("FQ1", "FQ2"): H = ALT_FQ[e]
        if not len(cv) or not np.isfinite(H) or H <= 0:
            efl[e] = hin; continue
        L_cr = float(np.interp(H, g.altura_m, g.L_crista_m))
        Qm = Q_SEM_DANO * AREA[e] / A_ANALISE
        Qo, v, s = rotear(hin, cv, H, Qm, max(L_cr * 0.25, 40.0), regra)
        efl[e] = Qo; vol += v; sat = sat or s
    terminais = [e for e in conj if not jus(e, conj)]
    A_ctrl = sum(AREA[e] for e in terminais)
    q = q_nat * (1 - A_ctrl / area_ref)
    for e in terminais: q = q + efl[e]
    return q, vol, sat

ALT_FQ = {"FQ1": 30.0, "FQ2": 30.0}   # altura de triagem, varrida adiante

def avalia(eixos_antas, eixos_fq, lag_h=None, regra="seca"):
    lag_h = LAG_REF if lag_h is None else lag_h
    qa, va, sa = rota_vertente(eixos_antas, Q_ANTAS, A_ANALISE, regra)
    qf, vf, sf = rota_vertente(eixos_fq, Q_FQ, A_FORQUETA, regra)
    q_est = soma_estrela(qa, qf, lag_h)
    return dict(pico_estrela=float(q_est.max()), pico_analise=float(qa.max()),
                volume_hm3=va + vf, vol_antas_hm3=va, vol_fq_hm3=vf,
                saturou=sa or sf, hidro=q_est)

# =============================================================================
# 4. CENARIOS DO PLANO
# =============================================================================
ALT_J = ["E02", "E04", "E01", "E05", "E08", "E12"]
CEN = {
    "ALT-J sem Forqueta":        (ALT_J, []),
    "ALT-J + FQ1":               (ALT_J, ["FQ1"]),
    "ALT-J + FQ2":               (ALT_J, ["FQ2"]),
    # INVIAVEL na pratica: claude_fq_interferencia_pch.py mostra que o NA de FQ1
    # com 30 m (52,5 m) fica 12,5 m acima da cota do eixo de FQ2 (40,0 m).
    # Mantido apenas como limite superior teorico, conforme pedido no plano.
    "ALT-J + FQ1 + FQ2 (inviavel)": (ALT_J, ["FQ1", "FQ2"]),
    "FQ1 isolado":               ([],    ["FQ1"]),
    "FQ2 isolado":               ([],    ["FQ2"]),
    "ALT-A (E02+E04) + FQ1":     (["E02", "E04"], ["FQ1"]),
}
log("roteando cenarios...")
regs, hidros = [], {"tempo_h": T_H, "natural": soma_estrela(Q_ANTAS, Q_FQ, LAG_REF)}
for nome, (ea, ef) in CEN.items():
    for regra in ("seca", "comportas", "convencional"):
        r = avalia(ea, ef, regra=regra)
        regs.append(dict(
            cenario=nome, regra=regra,
            eixos_antas=",".join(ea) or "-", eixos_forqueta=",".join(ef) or "-",
            volume_total_hm3=round(r["volume_hm3"], 1),
            vol_antas_hm3=round(r["vol_antas_hm3"], 1),
            vol_forqueta_hm3=round(r["vol_fq_hm3"], 1),
            pico_estrela_m3s=round(r["pico_estrela"]),
            reducao_estrela_pct=round(100 * (1 - r["pico_estrela"] / PICO_NAT_EST), 1),
            pico_analise_m3s=round(r["pico_analise"]),
            reducao_analise_pct=round(100 * (1 - r["pico_analise"] / PICO_NAT_ANL), 1),
            saturou=r["saturou"]))
        if regra == "seca": hidros[nome] = r["hidro"]
rc = pd.DataFrame(regs)
rc.to_csv(os.path.join(D_OUT, "claude_fq_roteamento_calibrado.csv"),
          index=False, sep=";", decimal=",")
pd.DataFrame(hidros).round(1).to_csv(
    os.path.join(D_OUT, "claude_fq_hidrogramas.csv"), index=False, sep=";", decimal=",")

print("\n" + "=" * 115)
print("3. CENARIOS — regra de BARRAGEM SECA "
      f"(altura FQ1={ALT_FQ['FQ1']:.0f} m, FQ2={ALT_FQ['FQ2']:.0f} m)")
print("=" * 115)
print(rc[rc.regra == "seca"][
    ["cenario", "volume_total_hm3", "vol_forqueta_hm3", "pico_estrela_m3s",
     "reducao_estrela_pct", "pico_analise_m3s", "reducao_analise_pct",
     "saturou"]].to_string(index=False))

print("\n" + "=" * 115)
print("4. EFEITO DA REGRA OPERATIVA — reducao do pico em Estrela (%)")
print("=" * 115)
print(rc.pivot(index="cenario", columns="regra",
               values="reducao_estrela_pct").to_string())

# =============================================================================
# 5. SENSIBILIDADE A DEFASAGEM
# =============================================================================
LAGS = sorted(set([-12, -6, 0, 6, 12, 18, 24, LAG_TEORICO, 36]))
log("sensibilidade a defasagem...")
sl = []
for nome, (ea, ef) in CEN.items():
    for lag in LAGS:
        pn = float(soma_estrela(Q_ANTAS, Q_FQ, lag).max())
        r = avalia(ea, ef, lag_h=lag)
        sl.append(dict(cenario=nome, defasagem_h=lag,
                       pico_natural_m3s=round(pn),
                       pico_estrela_m3s=round(r["pico_estrela"]),
                       reducao_pct=round(100 * (1 - r["pico_estrela"] / pn), 1)))
sd = pd.DataFrame(sl)
sd.to_csv(os.path.join(D_OUT, "claude_fq_sensibilidade_defasagem.csv"),
          index=False, sep=";", decimal=",")
print("\n" + "=" * 115)
print("5. SENSIBILIDADE A DEFASAGEM — reducao do pico em Estrela (%)")
print("   (cada coluna usa o SEU proprio pico natural, calculado com a mesma defasagem)")
print("=" * 115)
print(sd.pivot(index="cenario", columns="defasagem_h",
               values="reducao_pct").to_string())
print("\n  pico natural em Estrela por defasagem (m3/s):")
pn_ = sd.groupby("defasagem_h").pico_natural_m3s.first()
print("   " + " | ".join(f"{k:>+3d}h {v:>7,.0f}" for k, v in pn_.items()))

# =============================================================================
# 6. VARREDURA DE ALTURA
# =============================================================================
log("varredura de altura em FQ1 e FQ2...")
va = []
for eixo in ("FQ1", "FQ2"):
    for H in [15, 20, 25, 30, 35, 40, 45, 50, 60, 70]:
        ALT_FQ[eixo] = float(H)
        outro = "FQ2" if eixo == "FQ1" else "FQ1"
        guarda = ALT_FQ[outro]; ALT_FQ[outro] = 30.0
        r_iso = avalia([], [eixo]); r_alt = avalia(ALT_J, [eixo])
        cv = fqc[fqc.eixo == eixo]
        va.append(dict(
            eixo=eixo, altura_m=H,
            volume_cav_hm3=round(float(np.interp(H, cv.altura_m, cv.volume_hm3)), 1),
            area_alagada_km2=round(float(np.interp(H, cv.altura_m, cv.area_alagada_km2)), 1),
            vol_usado_isolado_hm3=round(r_iso["vol_fq_hm3"], 1),
            reducao_isolado_pct=round(100 * (1 - r_iso["pico_estrela"] / PICO_NAT_EST), 1),
            reducao_com_ALTJ_pct=round(100 * (1 - r_alt["pico_estrela"] / PICO_NAT_EST), 1),
            saturou_isolado=r_iso["saturou"]))
        ALT_FQ[outro] = guarda
    ALT_FQ[eixo] = 30.0
vh = pd.DataFrame(va)
vh.to_csv(os.path.join(D_OUT, "claude_fq_altura_volume.csv"),
          index=False, sep=";", decimal=",")
print("\n" + "=" * 115)
print("6. VARREDURA DE ALTURA")
print("=" * 115)
for eixo in ("FQ1", "FQ2"):
    print(f"\n  --- {eixo} ---")
    print(vh[vh.eixo == eixo].drop(columns="eixo").to_string(index=False))

# =============================================================================
# LEITURA
# =============================================================================
print("\n" + "-" * 115)
print("LEITURA")
print("-" * 115)
b = rc[(rc.regra == "seca")].set_index("cenario")
d_fq1 = b.loc["ALT-J + FQ1", "reducao_estrela_pct"] - b.loc["ALT-J sem Forqueta", "reducao_estrela_pct"]
d_fq2 = b.loc["ALT-J + FQ2", "reducao_estrela_pct"] - b.loc["ALT-J sem Forqueta", "reducao_estrela_pct"]
d_amb = b.loc["ALT-J + FQ1 + FQ2 (inviavel)", "reducao_estrela_pct"] - b.loc["ALT-J sem Forqueta", "reducao_estrela_pct"]
print(f"  ganho marginal sobre ALT-J:  FQ1 {d_fq1:+.1f} pp | FQ2 {d_fq2:+.1f} pp | "
      f"FQ1+FQ2 {d_amb:+.1f} pp")
v1 = b.loc["ALT-J + FQ1", "vol_forqueta_hm3"]; v2 = b.loc["ALT-J + FQ2", "vol_forqueta_hm3"]
if v1 > 0: print(f"  eficiencia: FQ1 {d_fq1/v1*100:.2f} pp por 100 hm3 usados ({v1:,.0f} hm3)")
if v2 > 0: print(f"              FQ2 {d_fq2/v2*100:.2f} pp por 100 hm3 usados ({v2:,.0f} hm3)")
print(f"\n  FQ1 isolado reduz {b.loc['FQ1 isolado','reducao_estrela_pct']:.1f}% do pico em Estrela")
print(f"  e nao altera o pico no ponto de analise "
      f"({b.loc['FQ1 isolado','reducao_analise_pct']:.1f}%), como esperado de um")
print("  tributario de jusante: FQ1 nao protege Mucum nem Encantado.")
print(f"\n  A defasagem e' determinante. Entre {min(LAGS):+d} h e {max(LAGS):+d} h o pico")
print(f"  natural em Estrela varia de {pn_.min():,.0f} a {pn_.max():,.0f} m3/s "
      f"({100*(pn_.max()/pn_.min()-1):.0f}% de amplitude), sem qualquer barragem.")
print("  Confirmar o tempo de viagem Forqueta->Taquari e' pre-requisito para")
print("  fechar o dimensionamento; a serie diaria da ANA nao tem resolucao para isso.")
log("FIM")
