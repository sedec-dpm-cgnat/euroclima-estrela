# -*- coding: utf-8 -*-
"""
EUROCLIMA / Estrela-RS — ALTURA ADMISSIVEL REVISADA, por posicao longitudinal.

MOTIVO DA REVISAO
-----------------
A versao anterior (`12_altura_maxima_admissivel.py`) determina quem esta' a
MONTANTE de cada eixo comparando AREA DE DRENAGEM e COTA. Esse criterio falha
quando dois barramentos tem areas quase iguais: a diferenca de area fica dentro
do erro do MDE e a ordem montante/jusante sai trocada.

Caso concreto detectado no perfil longitudinal:
    E09        — area 12.330 km², cota 106,0 m, estaca 303,3 km
    Monte Claro— area 12.414 km², cota 132,5 m, estaca 279,5 km
A area de Monte Claro e' 0,7% MAIOR, o que pelo criterio antigo o classificava
como JUSANTE de E09; mas ele esta' 24 km ACIMA no talvegue, ou seja, e'
MONTANTE. Com isso, a restricao de E09 foi atribuida a Foz do Prata
(cota 171,3 m), resultando em altura admissivel de 63,3 m — quando o limite
real e' imposto por Monte Claro (cota 132,5 m).

CRITERIO REVISADO
-----------------
Monta-se o perfil do canal principal e ordena-se TUDO por estaca (km ao longo
do talvegue). Um aproveitamento esta' a montante de um eixo se, e somente se,
sua estaca for MENOR. A restricao de altura passa a ser a cota de restituicao
do aproveitamento imediatamente a montante NO TALVEGUE.

Para eixos fora do canal principal (tributarios), mantem-se o criterio por
area + cota, sinalizando-os na saida.

Saidas (06_resultados/CLAUDE/):
  claude_altura_admissivel_revisada.csv
  claude_comparacao_altura_admissivel.csv
"""
import os, time, warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import geopandas as gpd

DEST = os.path.join(os.environ["EURO"], "05_MODELAGEM")
D_CAV = os.path.join(DEST, "01_dados", "cav")
D_TAB = os.path.join(DEST, "06_resultados", "tabelas")
D_OUT = os.path.join(DEST, "06_resultados", "CLAUDE")
UTM22 = 31982
os.makedirs(D_OUT, exist_ok=True)

t0 = time.time()
def log(*a): print(f"[{time.time()-t0:6.1f}s]", *a, flush=True)

FOLGA_M = 2.0
DIST_STEM_M = 1500.0
# Teto tecnico: acima disso a altura deixa de ser governada pelo remanso e
# passa a ser governada por topografia, geotecnia, custo e meio ambiente.
# E' tambem o limite ate onde as curvas cota-area-volume foram calculadas.
H_TETO_M = 120.0

# ------------------------------------------------------------------ entradas
pf = pd.read_csv(os.path.join(D_OUT, "claude_perfil_principal.csv"), sep=";", decimal=",")
geo = pd.read_csv(os.path.join(D_CAV, "geometria_todos.csv"), sep=";", decimal=",")
eix = pd.read_csv(os.path.join(D_CAV, "eixos_todos.csv"), sep=";", decimal=",")
apr = pd.read_csv(os.path.join(D_TAB, "aproveitamentos_existentes.csv"), sep=";", decimal=",")
ant = pd.read_csv(os.path.join(D_TAB, "altura_maxima_admissivel.csv"), sep=";", decimal=",")
apr["potencia_MW"] = pd.to_numeric(
    apr.potencia_kW.astype(str).str.replace(",", "."), errors="coerce") / 1000.0

# ------------------------------------------------------------- estacas
# O perfil (claude_02) traz as coordenadas UTM de cada estaca. A posicao de
# cada barramento e' obtida GEOMETRICAMENTE — nunca por area de drenagem, que
# projeta usinas de tributarios em estacas erradas do canal principal.
from shapely.geometry import Point

pf = pf.sort_values("dist_km").reset_index(drop=True)
_xy = pf[["x_utm", "y_utm"]].values

def localiza(x, y):
    d2 = (_xy[:, 0] - x) ** 2 + (_xy[:, 1] - y) ** 2
    i = int(np.argmin(d2))
    return float(pf.dist_km.values[i]), float(np.sqrt(d2[i]))

gapr = gpd.GeoDataFrame(apr, geometry=gpd.points_from_xy(apr.lon, apr.lat),
                        crs=4674).to_crs(UTM22)
geix = gpd.GeoDataFrame(eix, geometry=gpd.points_from_xy(eix.lon, eix.lat),
                        crs=4326).to_crs(UTM22)

apr["estaca_km"], apr["dist_canal_m"] = zip(
    *[localiza(g.x, g.y) for g in gapr.geometry])
eix["estaca_km"], eix["dist_canal_m"] = zip(
    *[localiza(g.x, g.y) for g in geix.geometry])
apr["no_canal"] = apr.dist_canal_m <= DIST_STEM_M
eix["no_canal"] = eix.dist_canal_m <= DIST_STEM_M

# ---------------------------------------------------------------- filtros
# (1) So aproveitamentos EM OPERACAO impoem restricao. Os registros "em
#     estudo" da ANEEL tem coordenadas arredondadas a 2 casas decimais
#     (~1 km), e a cota amostrada no MDE cai em encosta — chegando a 218 m
#     e 465 m para pontos que deveriam estar no leito. Sao mantidos apenas
#     como informacao, nunca como restricao.
# (2) A cota do aproveitamento precisa ser COMPATIVEL com o talvegue na sua
#     estaca (tolerancia TOL_COTA), senao o ponto nao esta' sobre o rio.
TOL_COTA_M = 40.0
_z_talv = lambda d: float(np.interp(d, pf.dist_km.values, pf.cota_m.values))
apr["cota_talvegue_m"] = apr.estaca_km.apply(_z_talv)
apr["coerente"] = (apr.cota_terreno_m - apr.cota_talvegue_m).abs() <= TOL_COTA_M
apr["valida_restricao"] = (apr.situacao == "operacao") & apr.no_canal & apr.coerente

n_est = int((apr.situacao != "operacao").sum())
n_inc = int((~apr.coerente & (apr.situacao == "operacao")).sum())
log(f"descartados como restricao: {n_est} em estudo, {n_inc} com cota incoerente")
log(f"aproveitamentos validos como restricao: {int(apr.valida_restricao.sum())}")

log(f"existentes no canal principal: {apr.no_canal.sum()} de {len(apr)}")
log(f"eixos no canal principal: {eix.no_canal.sum()} de {len(eix)}")

# ============================================================================
# restricao revisada
# ============================================================================
linhas = []
for _, e in eix.iterrows():
    cod, cota_e, area_e = e.codigo, float(e.cota_eixo_m), float(e.area_km2)
    est_e = float(e.estaca_km)

    if e.no_canal:
        # criterio por POSICAO: montante = estaca menor, no canal principal
        mont = apr[apr.valida_restricao & (apr.estaca_km < est_e) &
                   (apr.cota_terreno_m > cota_e)]
        criterio = "posicao longitudinal"
        if len(mont):
            lim = mont.loc[mont.estaca_km.idxmax()]      # o imediatamente acima
        else:
            lim = None
    else:
        # tributario: mantem area + cota
        mont = apr[(apr.situacao == "operacao") & apr.coerente &
                   (apr.area_drenagem_km2 < area_e) &
                   (apr.area_drenagem_km2 > area_e * 0.25) &
                   (apr.cota_terreno_m > cota_e)]
        criterio = "area + cota (fora do canal principal)"
        lim = mont.loc[mont.cota_terreno_m.idxmin()] if len(mont) else None

    if lim is None:
        h_rem, restr, cota_r, pot = np.inf, "sem aproveitamento a montante", np.nan, np.nan
    else:
        cota_r = float(lim.cota_terreno_m)
        h_rem = cota_r - FOLGA_M - cota_e
        restr = f"{lim['nome'][:26]} ({lim.situacao})"
        pot = float(lim.potencia_MW) if np.isfinite(lim.potencia_MW) else np.nan

    # A altura adotada e' a MENOR entre o limite de remanso e o teto tecnico.
    # Quando o remanso nao e' o fator limitante, isso e' dito explicitamente:
    # o eixo nao sofre interferencia da cascata existente.
    if h_rem >= H_TETO_M:
        h_max = H_TETO_M
        limitante = "teto tecnico (remanso nao e' limitante)"
    else:
        h_max = h_rem
        limitante = "remanso do aproveitamento de montante"

    sub = geo[geo.eixo == cod].sort_values("altura_m")
    if np.isfinite(h_max) and h_max > 0 and len(sub):
        vol = float(np.interp(h_max, sub.altura_m, sub.volume_hm3))
        are = float(np.interp(h_max, sub.altura_m, sub.area_alagada_km2))
        cus = float(np.interp(h_max, sub.altura_m, sub.custo_total_MRS))
    else:
        vol = are = cus = np.nan

    linhas.append(dict(
        eixo=cod, area_km2=area_e, cota_eixo_m=cota_e,
        estaca_km=round(est_e, 1), no_canal_principal=bool(e.no_canal),
        criterio=criterio, restricao=restr, limitante=limitante,
        h_remanso_m=round(h_rem, 1) if np.isfinite(h_rem) else np.nan,
        potencia_restr_MW=round(pot, 1) if np.isfinite(pot) else np.nan,
        cota_restricao_m=round(cota_r, 1) if np.isfinite(cota_r) else np.nan,
        altura_max_m=round(h_max, 1) if np.isfinite(h_max) else np.nan,
        volume_max_hm3=round(vol, 1) if np.isfinite(vol) else np.nan,
        area_alagada_km2=round(are, 2) if np.isfinite(are) else np.nan,
        custo_MRS=round(cus) if np.isfinite(cus) else np.nan))

rev = pd.DataFrame(linhas).sort_values("estaca_km")
rev.to_csv(os.path.join(D_OUT, "claude_altura_admissivel_revisada.csv"),
           index=False, sep=";", decimal=",")

# ------------------------------------------------------------- comparacao
cmp = rev[["eixo", "estaca_km", "no_canal_principal", "restricao",
           "altura_max_m", "volume_max_hm3"]].merge(
    ant[["eixo", "restricao", "altura_max_m", "volume_max_hm3"]],
    on="eixo", suffixes=("_rev", "_ant"))
cmp["delta_altura_m"] = (cmp.altura_max_m_rev - cmp.altura_max_m_ant).round(1)
cmp["delta_volume_hm3"] = (cmp.volume_max_hm3_rev - cmp.volume_max_hm3_ant).round(1)
cmp.to_csv(os.path.join(D_OUT, "claude_comparacao_altura_admissivel.csv"),
           index=False, sep=";", decimal=",")

pd.set_option("display.width", 230)
print("\n" + "=" * 126)
print("ALTURA ADMISSIVEL REVISADA — restricao por POSICAO LONGITUDINAL")
print("=" * 126)
print(rev[["eixo", "area_km2", "cota_eixo_m", "estaca_km", "no_canal_principal",
           "restricao", "h_remanso_m", "altura_max_m", "limitante",
           "volume_max_hm3", "area_alagada_km2", "custo_MRS"]].to_string(index=False))

livres = rev[rev.limitante.str.startswith("teto")]
print(f"\n  {len(livres)} eixo(s) SEM interferencia da cascata existente ate {H_TETO_M:.0f} m:")
for _, r_ in livres.iterrows():
    print(f"    {r_.eixo}: montante e' {r_.restricao}, {r_.h_remanso_m:.0f} m acima — nao limita")

print("\n" + "=" * 126)
print("COMPARACAO COM A VERSAO ANTERIOR (criterio por area + cota)")
print("=" * 126)
print(cmp.to_string(index=False))

mud = cmp[cmp.delta_altura_m.abs() > 1]
print(f"\n  {len(mud)} eixo(s) com alteracao relevante de altura admissivel.")
if len(mud):
    for _, m in mud.iterrows():
        print(f"    {m.eixo}: {m.altura_max_m_ant:>5.1f} m -> {m.altura_max_m_rev:>5.1f} m "
              f"({m.delta_altura_m:+.1f} m) | volume {m.volume_max_hm3_ant:>7.1f} -> "
              f"{m.volume_max_hm3_rev:>7.1f} hm3 ({m.delta_volume_hm3:+.1f})")
        print(f"        antes: {m.restricao_ant}")
        print(f"        agora: {m.restricao_rev}")

v_ant = ant[ant.altura_max_m > 0].volume_max_hm3.sum()
v_rev = rev[rev.altura_max_m > 0].volume_max_hm3.sum()
print(f"\n  Volume total mobilizavel:  antes {v_ant:,.0f} hm3  ->  revisado {v_rev:,.0f} hm3")
print(f"  Variacao: {v_rev - v_ant:+,.0f} hm3 ({100*(v_rev/v_ant - 1):+.1f}%)")
log("FIM")
