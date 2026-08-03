# -*- coding: utf-8 -*-
"""
EUROCLIMA / Estrela-RS — AVALIACAO ENERGETICA SINV DOS EIXOS DO FORQUETA.

Fecha o item 6 do PLANO_FORQUETA_CODEX_CLAUDE.md ("implicacoes para energia /
SINV"). Usa os MESMOS parametros de claude_01_sinv_energetico.py, para que os
resultados sejam comparaveis aos eixos do rio das Antas.

NAjn — o Forqueta e' tributario independente. Nenhum dos aproveitamentos
existentes (cascata CERAN e demais) esta' no Forqueta nem a jusante dele em
posicao de causar remanso no eixo. Adota-se portanto o nivel natural no local
como NAjn, sem restricao de jusante. Essa hipotese deve ser conferida pelo
Codex no item de remanso.

Saida: claude_fq_sinv.csv
"""
import os, time, warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd

DEST = os.path.join(os.environ["EURO"], "05_MODELAGEM")
D_FQ  = os.path.join(DEST, "01_dados", "cav_forqueta")
D_OUT = os.path.join(DEST, "06_resultados", "CLAUDE")
RD = dict(sep=";", decimal=",", encoding="utf-8-sig")
t0 = time.time()
def log(*a): print(f"[{time.time()-t0:6.1f}s]", *a, flush=True)
pd.set_option("display.width", 220)

PAR = dict(K_EF=0.0088, PERDA_CARGA=0.02, FK=0.55, DEPLEC_MAX=1/3,
           TAXA=0.08, VIDA=50, COM=25.0, Q_ESPEC=0.0269, RAZAO_CRIT=0.55,
           T_CRITICO_M=60, BDI_CASA=1.25)
FRC = (PAR["TAXA"] * (1 + PAR["TAXA"]) ** PAR["VIDA"]) / \
      ((1 + PAR["TAXA"]) ** PAR["VIDA"] - 1)

# de-para do pipeline isolado (ver claude_fq_roteamento_calibrado.py)
TRAD = {"E02": "FQ1", "E01": "FQ2"}
AREA = {"FQ1": 2350.1, "FQ2": 2204.2}
COTA = {"FQ1": 22.5,   "FQ2": 40.0}      # cota do eixo, m

geo = pd.read_csv(os.path.join(D_FQ, "geometria_todos.csv"), **RD)
geo = geo[geo.eixo.isin(TRAD)].copy(); geo["eixo"] = geo.eixo.map(TRAD)

# fracoes de volume de espera testadas (0 = so' energia; 1 = barragem seca)
FRACOES = [0.00, 0.20, 0.35, 0.50, 0.65, 0.80]

def avalia(cod, H, frac_esp):
    sub = geo[geo.eixo == cod].sort_values("altura_m")
    f_vol = lambda h: float(np.interp(h, sub.altura_m, sub.volume_hm3))
    f_are = lambda h: float(np.interp(h, sub.altura_m, sub.area_alagada_km2))
    f_cus = lambda h: float(np.interp(h, sub.altura_m, sub.custo_total_MRS))
    cota, area = COTA[cod], AREA[cod]

    V_max = f_vol(H)
    if V_max <= 0: return None
    V_esp = V_max * frac_esp
    V_mxn = V_max - V_esp
    h_mxn = float(np.interp(V_mxn, sub.volume_hm3, sub.altura_m))
    NA_mxn = cota + h_mxn
    NA_jn = cota                                   # nivel natural, sem remanso
    Hb_mxn = NA_mxn - NA_jn
    if Hb_mxn <= 1.0: return None

    d_max = PAR["DEPLEC_MAX"] * Hb_mxn
    h_min = max(h_mxn - d_max, 0.0)
    V_min = f_vol(h_min)
    V_util = max(V_mxn - V_min, 0.0)
    V_med = V_mxn - 0.5 * V_util
    h_med = float(np.interp(V_med, sub.volume_hm3, sub.altura_m))
    Hb_m = (cota + h_med) - NA_jn
    Hl_m = Hb_m * (1 - PAR["PERDA_CARGA"])
    A_med = f_are(h_med)

    Qmlt = PAR["Q_ESPEC"] * area                   # m3/s
    T_SEG = PAR["T_CRITICO_M"] * 30.44 * 86400.0
    Q_crit = Qmlt * PAR["RAZAO_CRIT"]
    Qlm = Q_crit + V_util * 1e6 / T_SEG            # regularizacao no periodo critico
    Qlm = min(Qlm, Qmlt)                           # nao pode superar a afluencia media

    Ef = PAR["K_EF"] * Hl_m * Qlm                  # MW medios — eq. 4.6.1.01
    P = Ef / PAR["FK"]                             # MW instalados
    Ef = min(Ef, P)                                # coerencia
    C = f_cus(H) * PAR["BDI_CASA"]                 # MR$
    CT = C * 1e6 * FRC + P * 1e3 * PAR["COM"]      # R$/ano
    ICB = CT / (Ef * 8760) if Ef > 0 else np.nan   # R$/ano / (MWh/ano) = R$/MWh

    return dict(eixo=cod, altura_m=H, frac_espera=frac_esp,
                V_max_hm3=round(V_max, 1), V_espera_hm3=round(V_esp, 1),
                V_util_hm3=round(V_util, 1),
                NA_mxn_m=round(NA_mxn, 1), queda_liq_media_m=round(Hl_m, 1),
                area_alagada_km2=round(A_med, 1),
                Qmlt_m3s=round(Qmlt, 1), Qlm_m3s=round(Qlm, 1),
                Ef_MWmed=round(Ef, 1), P_MW=round(P, 1),
                custo_MRS=round(C, 0), ICB_RS_MWh=round(ICB, 1))

log(f"FRC = {FRC:.5f} (j={PAR['TAXA']:.0%}, z={PAR['VIDA']} anos)")
regs = []
for cod in ("FQ1", "FQ2"):
    for H in (25, 30, 35, 40, 50, 60):
        for fe in FRACOES:
            r = avalia(cod, H, fe)
            if r: regs.append(r)
sv = pd.DataFrame(regs)
sv.to_csv(os.path.join(D_OUT, "claude_fq_sinv.csv"), index=False, sep=";", decimal=",")

print("=" * 118)
print("SINV — EIXOS DO FORQUETA (altura otima de amortecimento = 30 m, ver claude_fq_roteamento)")
print("=" * 118)
for cod in ("FQ1", "FQ2"):
    s = sv[(sv.eixo == cod) & (sv.altura_m == 30)]
    print(f"\n  --- {cod} | H = 30 m | Qmlt = {s.Qmlt_m3s.iloc[0]:.1f} m3/s ---")
    print(s[["frac_espera", "V_espera_hm3", "V_util_hm3", "queda_liq_media_m",
             "Qlm_m3s", "Ef_MWmed", "P_MW", "custo_MRS", "ICB_RS_MWh"]].to_string(index=False))

print("\n" + "=" * 118)
print("TRADE-OFF espera x energia em FQ1 — melhor ICB por altura")
print("=" * 118)
mel = (sv[sv.eixo == "FQ1"].sort_values("ICB_RS_MWh")
       .groupby("altura_m").first().reset_index())
print(mel[["altura_m", "frac_espera", "V_max_hm3", "queda_liq_media_m",
           "Ef_MWmed", "P_MW", "custo_MRS", "ICB_RS_MWh"]].to_string(index=False))

print("\n" + "-" * 118)
print("LEITURA")
print("-" * 118)
f0 = sv[(sv.eixo == "FQ1") & (sv.altura_m == 30) & (sv.frac_espera == 0.0)].iloc[0]
f8 = sv[(sv.eixo == "FQ1") & (sv.altura_m == 30) & (sv.frac_espera == 0.80)].iloc[0]
print(f"  FQ1 com 30 m e reservatorio dedicado a energia: {f0.Ef_MWmed:.1f} MW medios, "
      f"ICB R$ {f0.ICB_RS_MWh:,.0f}/MWh")
print(f"  FQ1 com 30 m e 80% do volume reservado a espera: {f8.Ef_MWmed:.1f} MW medios, "
      f"ICB R$ {f8.ICB_RS_MWh:,.0f}/MWh")
print(f"  perda de energia ao priorizar o controle de cheias: "
      f"{100*(1-f8.Ef_MWmed/max(f0.Ef_MWmed,1e-9)):.0f}%")
print(f"\n  Referencia de competitividade adotada em claude_01: ICB de R$ 250 a 300/MWh.")
print(f"  O melhor ICB de FQ1 e' R$ {sv[sv.eixo=='FQ1'].ICB_RS_MWh.min():,.0f}/MWh "
      f"e o de FQ2, R$ {sv[sv.eixo=='FQ2'].ICB_RS_MWh.min():,.0f}/MWh.")
print("\n  A queda disponivel no Forqueta e' baixa e a area alagada e' grande")
print(f"  ({f0.area_alagada_km2:.1f} km2 no NA medio com 30 m). O eixo se justifica pelo")
print("  AMORTECIMENTO, nao pela energia; a geracao e' subproduto marginal.")
print("  Comparar com os eixos do Antas, onde a relacao se inverte.")
log("FIM")
