# -*- coding: utf-8 -*-
"""
EUROCLIMA / Estrela-RS — CONSOLIDACAO FINAL DAS ALTERNATIVAS DE EIXOS.

Decisoes fixadas em `STATUS_ATUAL_PROJETO.md` e respeitadas aqui:
  - SINV v2 (vazao especifica calibrada 0,0269 m3/s/km2 e CAV PCHIP de 1 m);
  - PCHIP monotonica como curva operacional; polinomios nao sao usados;
  - E10 fora da carteira principal (balanco energetico negativo);
  - E02 e E04 sao os candidatos prioritarios; E01 e' alternativa em tributario;
    E05 permanece condicionado a Castro Alves;
  - resultados historicos nao sao sobrescritos (saida em CLAUDE/, sufixo final).

Produz:
  claude_alternativas_finais.csv    — carteira de alternativas comparadas
  claude_eixos_ficha_final.csv      — ficha por eixo, com todos os atributos
"""
import os, time, warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd

DEST = os.path.join(os.environ["EURO"], "05_MODELAGEM")
D_CAV = os.path.join(DEST, "01_dados", "cav")
D_TAB = os.path.join(DEST, "06_resultados", "tabelas")
D_OUT = os.path.join(DEST, "06_resultados", "CLAUDE")
os.makedirs(D_OUT, exist_ok=True)
RD = dict(sep=";", decimal=",", encoding="utf-8-sig")

t0 = time.time()
def log(*a): print(f"[{time.time()-t0:6.1f}s]", *a, flush=True)

# ---------------------------------------------------------------- referencias
AREA_ESTRELA = 19440.0     # km2 — area de drenagem em Estrela
Q_PICO_REF   = 18000.0     # m3/s — pico do evento de referencia [NAO CALIBRADO]
V_NECESSARIO = 3230.0      # hm3 — para nao ultrapassar 4.000 m3/s em Estrela
ICB_REF      = 300.0       # R$/MWh — limite usual de competitividade

# ------------------------------------------------------------------- entradas
sin = pd.read_csv(os.path.join(D_OUT, "claude_sinv_energetico_v2.csv"), **RD)
sint = pd.read_csv(os.path.join(D_OUT, "claude_sinv_sintese_eixos_v2.csv"), **RD)
cav = pd.read_csv(os.path.join(D_OUT, "claude_cav_eixos_consolidada.csv"), **RD)
rev = pd.read_csv(os.path.join(D_OUT, "claude_altura_admissivel_revisada.csv"), **RD)
bal = pd.read_csv(os.path.join(D_OUT, "claude_balanco_energetico_liquido.csv"), **RD)
topo = pd.read_csv(os.path.join(D_CAV, "topologia_eixos.csv"), **RD)
eix = pd.read_csv(os.path.join(D_CAV, "eixos_todos.csv"), **RD)
log(f"SINV v2: {len(sin)} combinacoes | CAV consolidada: {len(cav)} eixos")

# =============================================================================
# 1. FICHA POR EIXO
# =============================================================================
# classificacao decidida
CLASSE = {
    "E02": ("prioritario", "candidato prioritario — remanso nao limita ate 120 m"),
    "E04": ("prioritario", "candidato prioritario — remanso nao limita ate 120 m"),
    "E01": ("alternativa", "alternativa em tributario — restricao de Cotipora"),
    "E05": ("condicionado", "condicionado ao remanso de Castro Alves"),
    "E10": ("descartado", "balanco energetico negativo em toda a faixa viavel"),
}
def classifica(e):
    if e in CLASSE: return CLASSE[e]
    return ("condicionado", "condicionado a usina existente de montante")

# balanco energetico liquido na altura admissivel
bal_h = {}
for e in bal.eixo.unique():
    s = bal[bal.eixo == e]
    h_adm = rev.loc[rev.eixo == e, "altura_max_m"]
    if not len(h_adm) or not np.isfinite(h_adm.iloc[0]): continue
    H = float(h_adm.iloc[0])
    s2 = s[~s.VETO]
    if not len(s2):
        bal_h[e] = (np.nan, np.nan, True); continue
    i = (s2.altura_m - H).abs().idxmin()
    bal_h[e] = (float(s2.loc[i, "Ef_liquido_MWmed"]),
                float(s2.loc[i, "perda_montante_MWmed"]),
                bool(s.loc[s.altura_m.sub(H).abs().idxmin(), "VETO"]))

fichas = []
for _, c in cav.iterrows():
    e = c.eixo
    cl, just = classifica(e)
    sv = sint[sint.eixo == e]
    a_km2 = float(eix.loc[eix.codigo == e, "area_km2"].iloc[0])
    n_mont = int(eix.loc[eix.codigo == e, "n_montante"].iloc[0])
    liq, perda, veto = bal_h.get(e, (np.nan, np.nan, np.nan))
    fichas.append(dict(
        eixo=e, classe=cl, justificativa=just,
        area_controlada_km2=round(a_km2, 1),
        pct_bacia_estrela=round(100 * a_km2 / AREA_ESTRELA, 1),
        eixos_a_montante=n_mont,
        altura_admissivel_m=c.altura_m,
        limitante=rev.loc[rev.eixo == e, "limitante"].iloc[0],
        restricao_montante=c.restricao_montante,
        cota_NA_normal_m=c.cota_NA_normal_m,
        cota_NA_maximorum_m=c.cota_NA_maximorum_m,
        area_inundada_km2=c.area_inundada_km2,
        volume_acumulado_hm3=c.volume_acumulado_hm3,
        volume_util_hm3=c.volume_util_hm3,
        volume_espera_hm3=c.volume_espera_hm3,
        Ef_sem_espera_MWmed=float(sv.Ef_sem_espera.iloc[0]) if len(sv) else np.nan,
        Ef_com_espera_MWmed=float(sv.Ef_com_espera.iloc[0]) if len(sv) else np.nan,
        P_MW=float(sv.P_sem_espera.iloc[0]) if len(sv) else np.nan,
        ICB_sem_espera=float(sv.ICB_sem_espera.iloc[0]) if len(sv) else np.nan,
        ICB_com_espera=float(sv.ICB_com_espera.iloc[0]) if len(sv) else np.nan,
        perda_energia_espera_pct=float(sv.perda_energia_pct.iloc[0]) if len(sv) else np.nan,
        balanco_liquido_MWmed=round(liq, 1) if np.isfinite(liq) else np.nan,
        perda_usina_montante_MWmed=round(perda, 1) if np.isfinite(perda) else np.nan,
        confiabilidade_CAV="B — MDE natural, eixo sem reservatorio"))

fic = pd.DataFrame(fichas)
ordem = {"prioritario": 0, "alternativa": 1, "condicionado": 2, "descartado": 3}
fic["_o"] = fic.classe.map(ordem)
fic = fic.sort_values(["_o", "volume_acumulado_hm3"],
                      ascending=[True, False]).drop(columns="_o")
fic.to_csv(os.path.join(D_OUT, "claude_eixos_ficha_final.csv"),
           index=False, sep=";", decimal=",")

pd.set_option("display.width", 250)
print("=" * 136)
print("FICHA FINAL POR EIXO — alturas admissiveis revisadas, CAV PCHIP, SINV v2")
print("=" * 136)
print(fic[["eixo", "classe", "area_controlada_km2", "pct_bacia_estrela",
           "altura_admissivel_m", "area_inundada_km2", "volume_acumulado_hm3",
           "volume_espera_hm3", "P_MW", "ICB_sem_espera", "ICB_com_espera",
           "balanco_liquido_MWmed"]].to_string(index=False))

# =============================================================================
# 2. CARTEIRA DE ALTERNATIVAS
# =============================================================================
# Eixos aninhados podem coexistir em cascata; o que nao se pode e' somar duas
# vezes a mesma area de drenagem ao calcular a fracao controlada da bacia.
montantes = {e: set(topo.loc[topo.eixo == e, "montante"]) for e in eix.codigo}

def area_controlada(eixos):
    """Area efetivamente controlada por um conjunto, sem dupla contagem.

    Se A esta a montante de B e ambos entram, a area controlada e' a de B —
    a de A ja esta contida nela.
    """
    ativos = [e for e in eixos
              if not any((e in montantes.get(o, set())) for o in eixos if o != e)]
    return sum(float(eix.loc[eix.codigo == e, "area_km2"].iloc[0]) for e in ativos)

ALTERNATIVAS = {
    "ALT-A — E02 + E04 (prioritarios)": ["E02", "E04"],
    "ALT-B — E02 + E04 + E01": ["E02", "E04", "E01"],
    "ALT-C — E02 + E04 + E05": ["E02", "E04", "E05"],
    "ALT-D — E02 + E04 + E08": ["E02", "E04", "E08"],
    "ALT-E — E02 + E04 + E12": ["E02", "E04", "E12"],
    "ALT-F — E02 isolado": ["E02"],
    "ALT-G — E04 isolado": ["E04"],
    "ALT-H — E12 isolado (cascata critica)": ["E12"],
    "ALT-I — E02 + E04 + E01 + E05 + E08": ["E02", "E04", "E01", "E05", "E08"],
}

alts = []
for nome, es in ALTERNATIVAS.items():
    sub = fic[fic.eixo.isin(es)]
    if len(sub) != len(es):
        log(f"  {nome}: eixo ausente — pulando"); continue
    if "E10" in es:
        log(f"  {nome}: contem E10, descartado por decisao — pulando"); continue
    A = area_controlada(es)
    V_esp = sub.volume_espera_hm3.sum()
    V_ac = sub.volume_acumulado_hm3.sum()
    Ef = sub.Ef_com_espera_MWmed.sum()
    P = sub.P_MW.sum()
    # ICB do conjunto: soma dos custos anuais sobre a energia do conjunto
    cst = 0.0
    for e in es:
        s2 = sin[(sin.eixo == e) & (sin.frac_espera == 0.50)]
        if len(s2): cst += float(s2.CT_MRS_ano.iloc[0])
    icb = cst * 1e6 / (Ef * 8760) if Ef > 0 else np.nan
    # capacidade de amortecimento: fracao do volume necessario e da bacia
    alts.append(dict(
        alternativa=nome, n_eixos=len(es), eixos="+".join(es),
        area_controlada_km2=round(A),
        pct_bacia_controlada=round(100 * A / AREA_ESTRELA, 1),
        area_inundada_km2=round(sub.area_inundada_km2.sum(), 1),
        volume_acumulado_hm3=round(V_ac),
        volume_espera_hm3=round(V_esp),
        pct_do_volume_necessario=round(100 * V_esp / V_NECESSARIO, 1),
        Ef_MWmed=round(Ef, 1), P_MW=round(P, 1),
        ICB_RS_MWh=round(icb, 1) if np.isfinite(icb) else np.nan,
        competitivo_energia=bool(icb < ICB_REF) if np.isfinite(icb) else False,
        contem_apenas_prioritarios=all(fic.loc[fic.eixo == e, "classe"].iloc[0]
                                       in ("prioritario",) for e in es)))

alt = pd.DataFrame(alts).sort_values("volume_espera_hm3", ascending=False)
alt.to_csv(os.path.join(D_OUT, "claude_alternativas_finais.csv"),
           index=False, sep=";", decimal=",")

print("\n" + "=" * 136)
print("CARTEIRA DE ALTERNATIVAS")
print("=" * 136)
print(alt[["alternativa", "area_controlada_km2", "pct_bacia_controlada",
           "area_inundada_km2", "volume_espera_hm3", "pct_do_volume_necessario",
           "P_MW", "Ef_MWmed", "ICB_RS_MWh", "competitivo_energia"]].to_string(index=False))

# =============================================================================
# 3. LEITURA CRITICA
# =============================================================================
print("\n" + "-" * 136)
print("LEITURA")
print("-" * 136)
prio = alt[alt.contem_apenas_prioritarios]
if len(prio):
    b = prio.iloc[0]
    print(f"  Melhor arranjo so com eixos prioritarios: {b.alternativa}")
    print(f"    controla {b.pct_bacia_controlada:.1f}% da bacia em Estrela")
    print(f"    volume de espera {b.volume_espera_hm3:,.0f} hm3 "
          f"= {b.pct_do_volume_necessario:.0f}% do necessario")
    print(f"    ICB {b.ICB_RS_MWh:.0f} R$/MWh "
          f"({'competitivo' if b.competitivo_energia else 'NAO competitivo'})")

print("\n  ATENCAO — cobertura da bacia:")
for _, r in alt.iterrows():
    if r.pct_bacia_controlada < 60:
        print(f"    {r.alternativa}: controla apenas {r.pct_bacia_controlada:.1f}% "
              f"da bacia. A parcela nao controlada impoe piso de "
              f"{Q_PICO_REF*(1-r.pct_bacia_controlada/100):,.0f} m3/s em Estrela.")

print("\n  O volume de espera de uma alternativa NAO se converte diretamente em")
print("  reducao de pico: depende do hidrograma, da regra operativa e da")
print("  parcela nao controlada. A verificacao exige roteamento, ainda pendente.")
log("FIM")
