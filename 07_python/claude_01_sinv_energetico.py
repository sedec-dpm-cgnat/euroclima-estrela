# -*- coding: utf-8 -*-
"""
EUROCLIMA / Estrela-RS — AVALIACAO ENERGETICA PELA METODOLOGIA SINV
restrita as ALTURAS ADMISSIVEIS (sem afogar aproveitamento existente).

Referencia normativa
--------------------
MME/CEPEL. Manual de Inventario Hidroeletrico de Bacias Hidrograficas,
edicao 2007. Capitulo 4, itens 4.6 (Estudos Energeticos) e 4.11 (Comparacao e
Selecao de Alternativas). Metodologia implementada no sistema SINV.

Formulas implementadas
----------------------
  4.6.1.01  Ef_i   = 0,0088 x Hlm_i x Qlm_i                      [MW medios]
            0,0088 = 1000 kg/m3 x 0,93 (turbina) x 0,97 (gerador) x 9,81 / 1e6
  4.6.1.03  Qlm_i  = Qn_i - Qr_i + (1/T) x SOMA_k (Vu_k - Vesp_k - Evap_k x Amed_k)
  4.6.2.01  Ef     = SOMA Ef_i                                   (alternativa)
  4.6.5.01  P_i    = Ef_i / Fk                                   [MW]
  4.6.6     verificacao de reenchimento do volume util em ate 36 meses
  4.11.1.01 ICB_i  = CT_i / (dEf_i x 8760)                       [R$/MWh]
  4.11.1.02 CT_i   = C_i x FRC + P_i x COM x 1e3                 [R$/ano]
  4.11.1.03 FRC    = j(1+j)^z / ((1+j)^z - 1)

Criterios do manual respeitados
-------------------------------
  - NAmxn de reservatorio COM volume de espera = nivel correspondente ao volume
    maximo DESCONTADA a media dos volumes de espera (item 4.6.1);
  - NAjn = nivel natural a jusante OU o NAmxn do reservatorio imediatamente a
    jusante, se este for mais elevado — e' por aqui que a cascata EXISTENTE
    (Monte Claro, Castro Alves, 14 de Julho, Foz do Prata) entra no calculo;
  - deplecao maxima <= 1/3 da queda bruta maxima;
  - perdas de carga: 2% (circuito compacto) ou 3% (circuito longo).

ESCOPO: apenas alturas admissiveis de `altura_maxima_admissivel.csv`.
E05 e' excluido (altura admissivel negativa — eixo ja nasce afogado).

Saidas (prefixo claude_, em 06_resultados/CLAUDE/):
  claude_sinv_energetico.csv       — resultado por eixo e por fracao de espera
  claude_sinv_sintese_eixos.csv    — melhor arranjo de cada eixo
  claude_sinv_alternativas.csv     — alternativas (conjuntos de eixos)
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

t0 = time.time()
def log(*a): print(f"[{time.time()-t0:6.1f}s]", *a, flush=True)

# =============================================================================
# PARAMETROS  (item 2.6 do manual e criterios Eletrobras)
# =============================================================================
PAR = dict(
    K_EF        = 0.0088,   # coeficiente da eq. 4.6.1.01
    PERDA_CARGA = 0.02,     # 2% — circuito de geracao compacto
    FK          = 0.55,     # fator de capacidade de referencia
    DEPLEC_MAX  = 1/3,      # deplecao maxima / queda bruta maxima
    TAXA        = 0.08,     # taxa anual de desconto (j)
    VIDA        = 50,       # vida economica util (z), anos
    COM         = 25.0,     # custo anual de O&M, R$/kW/ano
    EVAP_MM_ANO = 150.0,    # evaporacao liquida anual, mm  [CALIBRAR]
    Q_ESPEC     = 0.0269,   # m3/s/km2 — CALIBRADA com Qmlt oficial das tres
                            # UHEs do rio das Antas (SNIRH). Antes: 0,020 arbitrado.
                            # Ver claude_vazao_especifica_calibrada.csv
    RAZAO_CRIT  = 0.55,     # Qn(periodo critico) / Qmlt  [CALIBRAR]
    T_CRITICO_M = 60,       # duracao do periodo critico, meses
    BDI_CASA    = 1.25,     # acrescimo de custo por casa de forca e equipamentos
)
FRACOES_ESPERA = [0.00, 0.20, 0.35, 0.50, 0.65, 0.80]   # Vesp / Vmax

# =============================================================================
# ENTRADAS
# =============================================================================
# Alturas admissiveis REVISADAS (claude_03), que corrigem a ordem
# montante/jusante por posicao longitudinal e descartam registros "em estudo"
# com coordenada imprecisa. Cai de volta para a versao original se ausente.
_p_rev = os.path.join(D_OUT, "claude_altura_admissivel_revisada.csv")
if os.path.exists(_p_rev):
    adm = pd.read_csv(_p_rev, sep=";", decimal=",")
    FONTE_ALTURAS = "claude_altura_admissivel_revisada.csv (posicao longitudinal)"
else:
    adm = pd.read_csv(os.path.join(D_TAB, "altura_maxima_admissivel.csv"),
                      sep=";", decimal=",")
    FONTE_ALTURAS = "altura_maxima_admissivel.csv (versao original)"
geo = pd.read_csv(os.path.join(D_CAV, "geometria_todos.csv"), sep=";", decimal=",")

# Curva cota-area-volume INTERPOLADA em passos de 1 m (PCHIP monotonica),
# auditada em claude_05_auditoria_cav.py: reproduz exatamente os 23 nos
# originais de cada eixo. Substitui a interpolacao linear sobre os pontos de
# 5 m. O custo continua vindo de geometria_todos.csv, que nao foi densificado.
_p_cav1m = os.path.join(D_TAB, "cav_eixos_novos_interpolada_1m.csv")
if os.path.exists(_p_cav1m):
    _c1 = pd.read_csv(_p_cav1m, sep=";", decimal=",", encoding="utf-8-sig")
    _cus = geo[["eixo", "altura_m", "custo_total_MRS"]]
    geo = _c1.merge(_cus, on=["eixo", "altura_m"], how="left")
    # o custo so existe nos multiplos de 5 m; interpola linearmente no restante
    geo["custo_total_MRS"] = geo.groupby("eixo").custo_total_MRS.transform(
        lambda s_: s_.interpolate(limit_direction="both"))
    FONTE_CAV = "cav_eixos_novos_interpolada_1m.csv (PCHIP 1 m)"
else:
    FONTE_CAV = "geometria_todos.csv (pontos de 5 m, interpolacao linear)"
eix = pd.read_csv(os.path.join(D_CAV, "eixos_todos.csv"), sep=";", decimal=",")
topo = pd.read_csv(os.path.join(D_CAV, "topologia_eixos.csv"), sep=";", decimal=",")
apr = pd.read_csv(os.path.join(D_TAB, "aproveitamentos_existentes.csv"),
                  sep=";", decimal=",")
apr["potencia_MW"] = pd.to_numeric(
    apr.potencia_kW.astype(str).str.replace(",", "."), errors="coerce") / 1000.0

# E05 excluido: altura admissivel negativa
EXCLUIDOS = []   # E05 reavaliado: altura revisada e positiva (67 m)
adm = adm[(~adm.eixo.isin(EXCLUIDOS)) & (adm.altura_max_m > 0)].copy()
log(f"fonte das alturas: {FONTE_ALTURAS}")
log(f"fonte das curvas CAV: {FONTE_CAV}")
log(f"{len(adm)} eixos com altura admissivel positiva")

# =============================================================================
# NAjn — nivel de agua normal a jusante  (item 4.6.1)
# =============================================================================
# "Corresponde ao nivel de agua no canal de fuga; admitido nos Estudos
#  Preliminares como sendo o nivel de agua natural no local, [...] ou o NAmxn
#  do reservatorio imediatamente a jusante, se este nivel for mais elevado."
#
# Aqui: procura-se, entre os aproveitamentos EXISTENTES e entre os demais
# EIXOS propostos, aquele imediatamente a jusante no mesmo curso (area de
# drenagem MAIOR e cota MENOR). Se o NA desse reservatorio superar a cota do
# eixo, ele passa a governar o NAjn e ha' perda de queda.
def naj_n(cod, cota_eixo, area):
    cand_e = apr[(apr.area_drenagem_km2 > area) &
                 (apr.cota_terreno_m < cota_eixo) &
                 apr.cota_terreno_m.notna()]
    nivel, quem = cota_eixo, "nivel natural no local"
    if len(cand_e):
        # o imediatamente a jusante e' o de MENOR area entre os de area maior
        j = cand_e.loc[cand_e.area_drenagem_km2.idxmin()]
        if j.cota_terreno_m > nivel:
            nivel, quem = float(j.cota_terreno_m), f"NA de {j['nome'][:24]} (existente)"
    return nivel, quem

# =============================================================================
# NUCLEO — avaliacao SINV de um eixo com uma dada fracao de volume de espera
# =============================================================================
FRC = (PAR["TAXA"] * (1 + PAR["TAXA"]) ** PAR["VIDA"]) / \
      ((1 + PAR["TAXA"]) ** PAR["VIDA"] - 1)
T_SEG = PAR["T_CRITICO_M"] * 30.44 * 86400.0        # segundos do periodo critico
log(f"FRC = {FRC:.5f}  (j={PAR['TAXA']:.0%}, z={PAR['VIDA']} anos)")

def avalia(cod, H, frac_esp):
    """Avaliacao energetica SINV de um eixo, para altura H e fracao de espera."""
    sub = geo[geo.eixo == cod].sort_values("altura_m")
    if len(sub) < 3: return None
    e = eix[eix.codigo == cod].iloc[0]
    cota_eixo, area = float(e.cota_eixo_m), float(e.area_km2)

    f_vol = lambda h: float(np.interp(h, sub.altura_m, sub.volume_hm3))
    f_are = lambda h: float(np.interp(h, sub.altura_m, sub.area_alagada_km2))
    f_cus = lambda h: float(np.interp(h, sub.altura_m, sub.custo_total_MRS))

    V_max = f_vol(H)                       # hm3 no NA maximo maximorum
    if V_max <= 0: return None
    V_esp = V_max * frac_esp               # volume de espera (controle de cheias)

    # --- NAmxn: nivel do volume maximo DESCONTADO o volume de espera --------
    V_mxn = V_max - V_esp
    h_mxn = float(np.interp(V_mxn, sub.volume_hm3, sub.altura_m))
    NA_mxn = cota_eixo + h_mxn

    # --- NAjn ---------------------------------------------------------------
    NA_jn, restr_jus = naj_n(cod, cota_eixo, area)

    Hb_mxn = NA_mxn - NA_jn                # queda bruta maxima
    if Hb_mxn <= 1.0: return None

    # --- deplecao maxima <= 1/3 da queda bruta maxima -----------------------
    d_max = PAR["DEPLEC_MAX"] * Hb_mxn
    h_min = max(h_mxn - d_max, 0.0)
    NA_min = cota_eixo + h_min
    Hb_min = NA_min - NA_jn
    V_min = f_vol(h_min)
    V_util = max(V_mxn - V_min, 0.0)       # volume util (hm3)

    # --- NA medio (deplecao media ~ metade do volume util) ------------------
    V_med = V_mxn - 0.5 * V_util
    h_med = float(np.interp(V_med, sub.volume_hm3, sub.altura_m))
    NA_m = cota_eixo + h_med
    Hb_m = NA_m - NA_jn
    A_med = f_are(h_med)                   # km2, area no NA medio

    # --- quedas liquidas (perdas de carga) ----------------------------------
    Hl_m = Hb_m * (1 - PAR["PERDA_CARGA"])

    # --- Qlm — eq. 4.6.1.03 -------------------------------------------------
    # ATENCAO METODOLOGICA: o volume de espera e' descontado UMA UNICA VEZ.
    # No manual, o NAmxn ja e' definido liquido da MEDIA dos volumes de espera
    # (item 4.6.1) e a eq. 4.6.1.03 desconta o volume de espera NO INICIO do
    # periodo critico — que, no manual, pode diferir da media. Nesta aplicacao
    # simplificada adota-se um unico valor de Vesp; portanto ele ja esta
    # embutido em V_util (que parte do NAmxn liquido) e NAO pode ser subtraido
    # de novo, sob pena de dupla contagem.
    Qn = area * PAR["Q_ESPEC"] * PAR["RAZAO_CRIT"]      # vazao no periodo critico
    evap_m = PAR["EVAP_MM_ANO"] / 1000.0 * (PAR["T_CRITICO_M"] / 12.0)
    aporte = (V_util * 1e6 - evap_m * A_med * 1e6) / T_SEG
    Qlm = Qn + aporte
    if Qlm <= 0: return None

    # --- energia firme e potencia ------------------------------------------
    Ef = PAR["K_EF"] * Hl_m * Qlm                       # MW medios
    P = Ef / PAR["FK"]                                  # MW instalados

    # --- custo total anual e ICB -------------------------------------------
    C = f_cus(H) * 1e6 * PAR["BDI_CASA"]                # R$ (civil + eletromec.)
    CT = C * FRC + P * PAR["COM"] * 1e3                 # R$/ano
    ICB = CT / (Ef * 8760) if Ef > 0 else np.nan        # R$/MWh

    # --- reenchimento do volume util (item 4.6.6) --------------------------
    # criterio simplificado: o volume util deve reencher com a vazao media
    # dos 36 meses subsequentes ao periodo critico
    Q_reench = area * PAR["Q_ESPEC"]
    t_reench_m = (V_util * 1e6) / (Q_reench * 30.44 * 86400) if Q_reench > 0 else np.inf

    return dict(
        eixo=cod, altura_m=round(H, 1), frac_espera=frac_esp,
        area_km2=round(area, 1), cota_eixo_m=round(cota_eixo, 1),
        NA_jn_m=round(NA_jn, 1), restricao_jusante=restr_jus,
        NA_mxn_m=round(NA_mxn, 1), NA_min_m=round(NA_min, 1),
        Hb_mxn_m=round(Hb_mxn, 1), Hb_med_m=round(Hb_m, 1),
        Hl_med_m=round(Hl_m, 1),
        V_max_hm3=round(V_max, 1), V_espera_hm3=round(V_esp, 1),
        V_util_hm3=round(V_util, 1),
        area_alagada_km2=round(f_are(H), 2),
        Qn_m3s=round(Qn, 1), Qlm_m3s=round(Qlm, 1),
        Ef_MWmed=round(Ef, 1), P_MW=round(P, 1),
        custo_MRS=round(C / 1e6),
        CT_MRS_ano=round(CT / 1e6, 1),
        ICB_RS_MWh=round(ICB, 1),
        t_reenchimento_meses=round(t_reench_m, 1),
        reench_ok=bool(t_reench_m <= 36))

# =============================================================================
# VARREDURA
# =============================================================================
log("avaliando eixos nas alturas admissiveis...")
regs = []
for _, a in adm.iterrows():
    H = float(a.altura_max_m)
    for fe in FRACOES_ESPERA:
        r = avalia(a.eixo, H, fe)
        if r:
            r["restricao_montante"] = a.restricao
            regs.append(r)

df = pd.DataFrame(regs)
if not len(df):
    raise SystemExit("nenhum eixo avaliado")
df.to_csv(os.path.join(D_OUT, "claude_sinv_energetico_v2.csv"),
          index=False, sep=";", decimal=",")
log(f"{len(df)} combinacoes avaliadas")

pd.set_option("display.width", 250)
print("\n" + "=" * 132)
print("AVALIACAO ENERGETICA SINV — ALTURAS ADMISSIVEIS")
print("(Manual de Inventario Hidroeletrico, MME 2007, itens 4.6 e 4.11)")
print("=" * 132)
cols = ["eixo", "altura_m", "frac_espera", "NA_mxn_m", "NA_jn_m", "Hb_med_m",
        "Hl_med_m", "V_max_hm3", "V_espera_hm3", "V_util_hm3", "Qlm_m3s",
        "Ef_MWmed", "P_MW", "custo_MRS", "ICB_RS_MWh", "reench_ok"]
print(df[cols].to_string(index=False))

# =============================================================================
# SINTESE POR EIXO — melhor ICB e trade-off espera x energia
# =============================================================================
print("\n" + "=" * 132)
print("SINTESE POR EIXO — sem volume de espera (so energia) x com 50% de espera")
print("=" * 132)
sin = []
for cod in df.eixo.unique():
    d0 = df[(df.eixo == cod) & (df.frac_espera == 0.0)]
    d5 = df[(df.eixo == cod) & (df.frac_espera == 0.50)]
    if not len(d0): continue
    r0 = d0.iloc[0]
    r5 = d5.iloc[0] if len(d5) else None
    sin.append(dict(
        eixo=cod, altura_m=r0.altura_m, area_km2=r0.area_km2,
        restricao_montante=r0.restricao_montante,
        restricao_jusante=r0.restricao_jusante,
        Hl_m=r0.Hl_med_m, V_max_hm3=r0.V_max_hm3,
        Ef_sem_espera=r0.Ef_MWmed, P_sem_espera=r0.P_MW, ICB_sem_espera=r0.ICB_RS_MWh,
        Ef_com_espera=r5.Ef_MWmed if r5 is not None else np.nan,
        V_espera_hm3=r5.V_espera_hm3 if r5 is not None else np.nan,
        ICB_com_espera=r5.ICB_RS_MWh if r5 is not None else np.nan,
        perda_energia_pct=round(100 * (1 - r5.Ef_MWmed / r0.Ef_MWmed), 1)
        if (r5 is not None and r0.Ef_MWmed > 0) else np.nan))
sd = pd.DataFrame(sin).sort_values("ICB_sem_espera")
sd.to_csv(os.path.join(D_OUT, "claude_sinv_sintese_eixos_v2.csv"),
          index=False, sep=";", decimal=",")
print(sd.to_string(index=False))

# =============================================================================
# ALTERNATIVAS — conjuntos de eixos (energia firme da alternativa, eq. 4.6.2.01)
# =============================================================================
# Eixos independentes (sem outro eixo a montante) segundo a topologia.
indep = set(eix[eix.n_montante == 0].codigo) - set(EXCLUIDOS)
log(f"eixos independentes: {sorted(indep)}")

ALTERNATIVAS = {
    "ALT-1 — E02 isolado (sem interferencia)": ["E02"],
    "ALT-2 — E04 isolado (sem interferencia)": ["E04"],
    "ALT-3 — E02 + E04 (ambos livres de interferencia)": ["E02", "E04"],
    "ALT-4 — E02 + E04 + E01": ["E02", "E04", "E01"],
    "ALT-5 — E12 isolado (cascata critica)": ["E12"],
    "ALT-6 — E02 + E04 + E12": ["E02", "E04", "E12"],
    "ALT-7 — E08 + E02 + E04": ["E08", "E02", "E04"],
}

print("\n" + "=" * 132)
print("ALTERNATIVAS — energia firme do conjunto (eq. 4.6.2.01) com 50% de espera")
print("=" * 132)
alts = []
for nome, eixos in ALTERNATIVAS.items():
    sel = df[(df.eixo.isin(eixos)) & (df.frac_espera == 0.50)]
    if len(sel) != len(eixos):
        log(f"  {nome}: nem todos os eixos disponiveis — pulando")
        continue
    sel0 = df[(df.eixo.isin(eixos)) & (df.frac_espera == 0.0)]
    alts.append(dict(
        alternativa=nome, n_eixos=len(eixos), eixos="+".join(eixos),
        area_controlada_km2=round(sel.area_km2.sum(), 0),
        V_max_hm3=round(sel.V_max_hm3.sum(), 0),
        V_espera_hm3=round(sel.V_espera_hm3.sum(), 0),
        V_util_hm3=round(sel.V_util_hm3.sum(), 0),
        area_alagada_km2=round(sel.area_alagada_km2.sum(), 1),
        Ef_MWmed=round(sel.Ef_MWmed.sum(), 1),
        Ef_sem_espera=round(sel0.Ef_MWmed.sum(), 1),
        P_MW=round(sel.P_MW.sum(), 1),
        custo_MRS=round(sel.custo_MRS.sum()),
        ICB_RS_MWh=round(sel.CT_MRS_ano.sum() * 1e6 / (sel.Ef_MWmed.sum() * 8760), 1)
        if sel.Ef_MWmed.sum() > 0 else np.nan))
ad = pd.DataFrame(alts).sort_values("ICB_RS_MWh")
ad.to_csv(os.path.join(D_OUT, "claude_sinv_alternativas_v2.csv"),
          index=False, sep=";", decimal=",")
print(ad.to_string(index=False))

print("\n" + "-" * 132)
print("NOTAS")
print("-" * 132)
print("  ICB = indice custo-beneficio energetico (R$/MWh). Quanto MENOR, melhor.")
print("  Para referencia, empreendimentos hidreletricos sao usualmente")
print("  considerados competitivos com ICB abaixo de ~R$ 250-300/MWh.")
print("  V_espera = volume alocado ao controle de cheias, que NAO gera energia.")
print("  reench_ok = volume util reenche em ate 36 meses (item 4.6.6).")
print("\n  Vazao especifica adotada: %.3f m3/s/km2 — NAO CALIBRADA." % PAR["Q_ESPEC"])
print("  Toda a energia escala linearmente com esse parametro.")
log("FIM")
