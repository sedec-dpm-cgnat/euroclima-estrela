# -*- coding: utf-8 -*-
"""
EUROCLIMA / Estrela-RS — C4: ROTEAMENTO COM PARAMETROS CALIBRADOS (C3).

Responde a pergunta que trava o fechamento da carteira:

    quanto do volume de espera de cada alternativa realmente se converte em
    REDUCAO DE PICO em Estrela?

Volume nao vira amortecimento automaticamente. O resultado depende de tres
coisas que ate aqui nao tinham sido tratadas em conjunto:

  (a) a FRACAO DA BACIA controlada — E02+E04 controlam apenas 57%, e os 43%
      restantes chegam a Estrela sem nenhum controle;
  (b) a REGRA OPERATIVA — barragem seca, comportas com deplecionamento
      preventivo ou vertedouro de soleira livre dao resultados muito
      diferentes para o mesmo volume;
  (c) a TOPOLOGIA — em cascata, o efluente do eixo de montante e' afluencia do
      de jusante, e o amortecimento nao e' aditivo.

METODO
------
1. Hidrograma natural em Estrela (gama de 2 parametros).
2. Decomposicao por AREA INCREMENTAL de cada no da rede, de modo que a soma
   dos sub-hidrogramas reproduza exatamente o natural. Evita o artefato de
   somar gamas independentes, que produzia "reducao negativa".
3. Roteamento de Puls de montante para jusante, respeitando a topologia:
   afluencia de um eixo = soma dos efluentes dos eixos imediatamente a
   montante + contribuicao da sua area incremental.
4. Vazao em Estrela = efluentes dos eixos mais a jusante + parcela nao
   controlada.

Curvas cota-area-volume: PCHIP de 1 m (`cav_eixos_novos_interpolada_1m.csv`).
Alturas: `claude_altura_admissivel_revisada.csv`.
E10 excluido por decisao (balanco energetico negativo).

Saidas (06_resultados/CLAUDE/):
  claude_c1_roteamento_alternativas.csv  — sintese por alternativa e regra
  claude_c1_hidrogramas.csv              — series do melhor arranjo
  claude_c1_sensibilidade_pico.csv       — sensibilidade ao pico de referencia
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

# =============================================================================
# PARAMETROS — a recalibrar em C3 com as series da ANA
# =============================================================================
PAR = dict(
    AREA_ESTRELA = 19440.0,   # km2
    # CALIBRADOS EM C3 com as series da ANA (86510000 Mucum, 86879300 Estrela)
    Q_PICO       = 16300.0,   # m3/s — evento set/2023 transposto ao ponto de analise
    Q_BASE       = 926.0,     # m3/s — percentil 10 da janela do evento
    LAMINA_MM    = 227.0,     # mm   — integracao do hidrograma observado
    Q_SEM_DANO   = 4000.0,    # m3/s [AINDA NAO CALIBRADO — depende do HEC-RAS]
    DT_H         = 1.0,
    FORMA_M      = 3.0,       # expoente da gama
)
EXCLUIDOS = ["E10"]

# =============================================================================
# ENTRADAS
# =============================================================================
rev = pd.read_csv(os.path.join(D_OUT, "claude_altura_admissivel_revisada.csv"), **RD)
cav = pd.read_csv(os.path.join(D_TAB, "cav_eixos_novos_interpolada_1m.csv"), **RD)
eix = pd.read_csv(os.path.join(D_CAV, "eixos_todos.csv"), **RD)
topo = pd.read_csv(os.path.join(D_CAV, "topologia_eixos.csv"), **RD)
geo = pd.read_csv(os.path.join(D_CAV, "geometria_todos.csv"), **RD)

AREA = dict(zip(eix.codigo, eix.area_km2))
H_ADM = dict(zip(rev.eixo, rev.altura_max_m))
log(f"{len(rev)} eixos com altura admissivel | E10 excluido")

# montantes de cada eixo (todos, nao so imediatos)
MONT = {e: set(topo.loc[topo.eixo == e, "montante"]) for e in eix.codigo}

def montantes_imediatos(e, conjunto):
    """Eixos do conjunto que estao a montante de e sem outro do conjunto entre eles."""
    ms = [m for m in conjunto if m != e and m in MONT.get(e, set())]
    return [m for m in ms if not any(o in MONT.get(m, set()) for o in ms)]

def area_incremental(e, conjunto):
    """Area que chega a e sem passar por nenhum outro eixo do conjunto."""
    return AREA[e] - sum(AREA[m] for m in montantes_imediatos(e, conjunto))

def jusantes(e, conjunto):
    return [o for o in conjunto if o != e and e in MONT.get(o, set())]

# =============================================================================
# HIDROLOGIA
# =============================================================================
def hidrograma(qp, area=None, lam=None):
    """Gama de 2 parametros ancorada em pico e lamina escoada."""
    area = area or PAR["AREA_ESTRELA"]
    lam = lam or PAR["LAMINA_MM"]
    Vt = lam / 1000 * area * 1e6
    m = PAR["FORMA_M"]
    fV = math.gamma(m + 1) * np.exp(m) / m ** (m + 1)
    qb = PAR["Q_BASE"] * area / PAR["AREA_ESTRELA"]
    tp = Vt / ((qp - qb) * fV)
    t = np.arange(0, 10 * tp, PAR["DT_H"] * 3600)
    q = qb + (qp - qb) * (t / tp) ** m * np.exp(m * (1 - t / tp))
    q[~np.isfinite(q)] = qb
    return t / 3600, q

T_H, Q_NAT = hidrograma(PAR["Q_PICO"])
PICO_NAT = float(Q_NAT.max())
log(f"hidrograma natural em Estrela: pico {PICO_NAT:,.0f} m3/s, "
    f"{len(T_H)} passos de {PAR['DT_H']:.0f} h")

def sub_hidrograma(area_km2):
    """Parcela do hidrograma natural correspondente a uma area de drenagem.

    A decomposicao e' PROPORCIONAL A AREA, de modo que a soma das parcelas
    reproduz exatamente o hidrograma natural. Ignora o defasamento entre
    sub-bacias — limitacao registrada; o HEC-HMS o capturaria.
    """
    return Q_NAT * (area_km2 / PAR["AREA_ESTRELA"])

# =============================================================================
# ESTRUTURAS DE DESCARGA E ROTEAMENTO
# =============================================================================
def vertedouro(h, h_sol, L, C=2.1):
    return C * L * max(h - h_sol, 0.0) ** 1.5

def orificio(h, A, Cd=0.62):
    return Cd * A * np.sqrt(2 * 9.81 * h) if h > 0 else 0.0

def A_para_Q(Q, carga, Cd=0.62):
    return Q / (Cd * np.sqrt(2 * 9.81 * max(carga, 1.0)))

def rotear(hin, cv, H_bar, regra, Q_meta, L_sol):
    """Roteamento de Puls com tres regras operativas.

    regra = 'convencional' : soleira livre a 3/4 da altura, reservatorio cheio
            'seca'         : reservatorio vazio, descarga de fundo p/ Q_meta
            'comportas'    : NA normal a 60% da altura, deplecionamento
                             preventivo, comportas modulando ate Q_meta
    """
    dt = PAR["DT_H"] * 3600
    cv = cv.sort_values("altura_m")
    V_de_h = lambda h: float(np.interp(h, cv.altura_m, cv.volume_hm3)) * 1e6
    h_de_V = lambda V: float(np.interp(V / 1e6, cv.volume_hm3, cv.altura_m))
    V_max = V_de_h(H_bar)

    if regra == "convencional":
        h_sol, V_ini, A_f = H_bar * 0.75, V_de_h(H_bar * 0.75), 20.0
    elif regra == "seca":
        h_sol, V_ini, A_f = H_bar - 4, 0.0, A_para_Q(Q_meta, H_bar / 2)
    else:  # comportas
        h_norm = H_bar * 0.60
        h_sol, V_ini = h_norm, V_de_h(max(h_norm - min(5.0, h_norm * 0.15), 0))
        A_f = A_para_Q(Q_meta, h_norm / 2)

    n = len(hin)
    V = np.zeros(n); h = np.zeros(n); Qo = np.zeros(n)
    V[0] = V_ini; h[0] = h_de_V(V_ini)
    sat = False
    for i in range(1, n):
        I = (hin[i - 1] + hin[i]) / 2
        Vp, hp = V[i - 1], h[i - 1]
        cap = vertedouro(hp, h_sol, L_sol) + orificio(hp, A_f)
        if Vp >= V_max * 0.995:
            # cheio: as comportas modulam para passar exatamente a afluencia
            Qt = min(cap, I); sat = True
        elif regra == "convencional":
            Qt = cap
        else:
            Qt = min(Q_meta, cap)
            ocup = (Vp - V_ini) / max(V_max - V_ini, 1.0)
            if ocup > 0.85:
                Qt = min(cap, max(Q_meta, I * (ocup - 0.85) / 0.15))
        Vn = Vp + (I - Qt) * dt
        if Vn > V_max:
            Qt = max(Qt, I); Vn = min(Vp + (I - Qt) * dt, V_max); sat = True
        if Vn < 0:
            Qt = max(Qt + Vn / dt, 0.0); Vn = 0.0
        V[i] = Vn; h[i] = h_de_V(Vn); Qo[i] = Qt
    return Qo, float(V.max() / 1e6), sat

# =============================================================================
# AVALIACAO DE UMA ALTERNATIVA
# =============================================================================
def avalia(conjunto, regra):
    conjunto = [e for e in conjunto if e not in EXCLUIDOS]
    # ordena de montante para jusante
    ordem = sorted(conjunto, key=lambda e: AREA[e])
    efl, vols, satur = {}, 0.0, False
    for e in ordem:
        imed = montantes_imediatos(e, conjunto)
        inc = area_incremental(e, conjunto)
        hin = sub_hidrograma(inc).copy()
        for m in imed:
            hin += efl[m]
        H = float(H_ADM[e])
        cv = cav[cav.eixo == e]
        if not len(cv) or not np.isfinite(H) or H <= 0:
            efl[e] = hin; continue
        L_cr = float(np.interp(H, geo[geo.eixo == e].altura_m,
                               geo[geo.eixo == e].L_crista_m))
        L_sol = max(L_cr * 0.25, 40.0)
        # meta de descarga proporcional a area controlada
        Q_meta = PAR["Q_SEM_DANO"] * AREA[e] / PAR["AREA_ESTRELA"]
        Qo, vmax, s = rotear(hin, cv, H, regra, Q_meta, L_sol)
        efl[e] = Qo; vols += vmax; satur = satur or s

    # eixos mais a jusante do conjunto (nao tem outro do conjunto a jusante)
    terminais = [e for e in conjunto if not jusantes(e, conjunto)]
    A_ctrl = sum(AREA[e] for e in terminais)
    q_livre = sub_hidrograma(PAR["AREA_ESTRELA"] - A_ctrl)
    q_est = q_livre.copy()
    for e in terminais:
        q_est = q_est + efl[e]
    return dict(pico=float(q_est.max()), volume_usado=vols, saturou=satur,
                area_ctrl=A_ctrl, serie=q_est, terminais=terminais)

# =============================================================================
# CARTEIRA
# =============================================================================
ALTERNATIVAS = {
    "ALT-A — E02 + E04 (prioritarios)": ["E02", "E04"],
    "ALT-B — E02 + E04 + E01": ["E02", "E04", "E01"],
    "ALT-C — E02 + E04 + E05": ["E02", "E04", "E05"],
    "ALT-D — E02 + E04 + E08": ["E02", "E04", "E08"],
    "ALT-E — E02 + E04 + E12": ["E02", "E04", "E12"],
    "ALT-F — E02 isolado": ["E02"],
    "ALT-G — E04 isolado": ["E04"],
    "ALT-H — E12 isolado": ["E12"],
    "ALT-I — E02+E04+E01+E05+E08": ["E02", "E04", "E01", "E05", "E08"],
    "ALT-J — E02+E04+E01+E05+E08+E12": ["E02", "E04", "E01", "E05", "E08", "E12"],
}
REGRAS = ["convencional", "seca", "comportas"]

log("roteando...")
regs = []
melhor = None
for nome, conj in ALTERNATIVAS.items():
    for regra in REGRAS:
        r = avalia(conj, regra)
        red = 100 * (1 - r["pico"] / PICO_NAT)
        reg = dict(
            alternativa=nome, eixos="+".join(conj), regra_operativa=regra,
            n_eixos=len(conj),
            area_controlada_km2=round(r["area_ctrl"]),
            pct_bacia=round(100 * r["area_ctrl"] / PAR["AREA_ESTRELA"], 1),
            volume_utilizado_hm3=round(r["volume_usado"], 1),
            pico_natural_m3s=round(PICO_NAT),
            pico_com_alternativa_m3s=round(r["pico"]),
            reducao_pico_pct=round(red, 1),
            atinge_Q_sem_dano=bool(r["pico"] <= PAR["Q_SEM_DANO"]),
            algum_reservatorio_saturou=r["saturou"])
        regs.append(reg)
        if melhor is None or red > melhor[0]:
            melhor = (red, nome, regra, r["serie"])

res = pd.DataFrame(regs)
res.to_csv(os.path.join(D_OUT, "claude_c4_roteamento_calibrado.csv"),
           index=False, sep=";", decimal=",")

pd.set_option("display.width", 240)
print("=" * 132)
print("C4 — REDUCAO DE PICO VERIFICADA POR ALTERNATIVA E REGRA OPERATIVA")
print("=" * 132)
for regra in REGRAS:
    print(f"\n--- regra: {regra.upper()} ---")
    s = res[res.regra_operativa == regra].sort_values("reducao_pico_pct",
                                                      ascending=False)
    print(s[["alternativa", "pct_bacia", "volume_utilizado_hm3",
             "pico_com_alternativa_m3s", "reducao_pico_pct",
             "atinge_Q_sem_dano", "algum_reservatorio_saturou"]].to_string(index=False))

# hidrogramas do melhor arranjo
red, nome, regra, serie = melhor
hid = pd.DataFrame(dict(t_h=T_H, Q_natural=np.round(Q_NAT, 1),
                        Q_com_alternativa=np.round(serie[:len(T_H)], 1)))
hid["alternativa"] = nome; hid["regra"] = regra
hid.to_csv(os.path.join(D_OUT, "claude_c4_hidrogramas_calibrado.csv"),
           index=False, sep=";", decimal=",")

# =============================================================================
# SENSIBILIDADE AO PICO DE REFERENCIA  (o parametro mais incerto)
# =============================================================================
print("\n" + "=" * 132)
print("SENSIBILIDADE AO PICO DE REFERENCIA — parametro ainda nao calibrado")
print("=" * 132)
sens = []
q_orig = PAR["Q_PICO"]
for qp in [10000, 14000, 18000, 22000, 26000]:
    PAR["Q_PICO"] = qp
    T_H, Q_NAT = hidrograma(qp)
    PICO_NAT = float(Q_NAT.max())
    for nome, conj in [("ALT-A — E02 + E04 (prioritarios)", ["E02", "E04"]),
                       ("ALT-J — carteira completa", ["E02", "E04", "E01",
                                                      "E05", "E08", "E12"])]:
        r = avalia(conj, "comportas")
        sens.append(dict(q_pico_referencia=qp, alternativa=nome,
                         pico_com=round(r["pico"]),
                         reducao_pct=round(100 * (1 - r["pico"] / PICO_NAT), 1),
                         saturou=r["saturou"]))
PAR["Q_PICO"] = q_orig
sd = pd.DataFrame(sens)
sd.to_csv(os.path.join(D_OUT, "claude_c4_sensibilidade_calibrado.csv"),
          index=False, sep=";", decimal=",")
print(sd.pivot(index="q_pico_referencia", columns="alternativa",
               values="reducao_pct").to_string())

# =============================================================================
# LEITURA
# =============================================================================
print("\n" + "-" * 132)
print("LEITURA")
print("-" * 132)
melhores = res.sort_values("reducao_pico_pct", ascending=False).head(3)
for _, r in melhores.iterrows():
    print(f"  {r.alternativa} ({r.regra_operativa}): reduz {r.reducao_pico_pct:.1f}% "
          f"— pico de {r.pico_natural_m3s:,.0f} para {r.pico_com_alternativa_m3s:,.0f} m3/s")
n_ok = int(res.atinge_Q_sem_dano.sum())
print(f"\n  Alternativas que levam o pico abaixo de {PAR['Q_SEM_DANO']:,.0f} m3/s: {n_ok} de {len(res)}")
prio = res[(res.eixos == "E02+E04")]
if len(prio):
    b = prio.sort_values("reducao_pico_pct", ascending=False).iloc[0]
    print(f"\n  Eixos prioritarios (E02+E04), melhor regra ({b.regra_operativa}):")
    print(f"    controla {b.pct_bacia:.1f}% da bacia, usa {b.volume_utilizado_hm3:,.0f} hm3")
    print(f"    reduz o pico em {b.reducao_pico_pct:.1f}% "
          f"({b.pico_natural_m3s:,.0f} -> {b.pico_com_alternativa_m3s:,.0f} m3/s)")
print("\n  NOTA: todos os parametros hidrologicos seguem NAO CALIBRADOS.")
print("  A ordenacao entre alternativas e' mais robusta que os valores absolutos.")
log("FIM")
