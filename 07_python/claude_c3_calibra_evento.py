# -*- coding: utf-8 -*-
"""
EUROCLIMA / Estrela-RS — C3: CALIBRACAO DO EVENTO DE REFERENCIA.

Substitui os parametros arbitrados por valores derivados das series da ANA
obtidas em C2. Ate aqui o pico de 18.000 m3/s, a lamina de 260 mm e o tempo de
retorno de 100 anos eram estimativas sem base observada.

BASE DE DADOS
-------------
  Mucum      (86510000) — 86 anos completos, 1940-2025. Serie de referencia.
  Estrela    (86879300) — apenas 3,1 anos de vazao (2020-2023). Registro
                          pontual do evento de 2023, mas curva-chave curta.
  Encantado  (86720000) — 84 anos, MAS com falhas justamente nos anos de
                          cheia (245 dias em 2023, 223 em 2024). Os maximos
                          desses anos NAO sao validos e foram descartados.

O QUE SE FAZ
------------
1. Analise de frequencia das maximas anuais em Mucum (Gumbel por momentos-L
   e por momentos convencionais, para comparacao).
2. Transposicao para Estrela por relacao de area, com expoente ajustado
   contra o par observado de 2023.
3. Estimativa da lamina escoada do evento a partir do hidrograma observado.
4. Atribuicao do tempo de retorno ao evento de referencia.
5. Parametros calibrados para alimentar C1 e o SINV.

Saidas (06_resultados/CLAUDE/):
  claude_c3_frequencia_mucum.csv
  claude_c3_parametros_calibrados.csv
  claude_c3_hidrograma_observado.csv
"""
import os, time, warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd

DEST = os.path.join(os.environ["EURO"], "05_MODELAGEM")
D_ANA = os.path.join(DEST, "01_dados", "ana_hidroweb")
D_OUT = os.path.join(DEST, "06_resultados", "CLAUDE")
RD = dict(sep=";", decimal=",")
os.makedirs(D_OUT, exist_ok=True)

t0 = time.time()
def log(*a): print(f"[{time.time()-t0:6.1f}s]", *a, flush=True)

# Areas OFICIAIS do inventario da ANA (HidroInventario), nao estimadas:
#   86510000 MUCUM   -> 16.000 km2   (-29,1672 ; -51,8686)
#   86879300 ESTRELA -> 22.472 km2   (-29,4733 ; -51,9622)
#   86720000 ENCANTADO -> 19.100 km2
# ATENCAO: o POSTO de Estrela drena 22.472 km2, enquanto o PONTO DE ANALISE do
# estudo — limite de montante do trecho modelado — drena 19.440 km2. Sao
# secoes diferentes, e o pico observado precisa ser transposto entre elas.
AREA_MUCUM        = 16000.0    # posto 86510000
AREA_POSTO_ESTRELA = 22472.0   # posto 86879300
AREA_ESTRELA      = 19440.0    # ponto de analise do estudo (montante do trecho)
COBERTURA_MIN = 300       # dias/ano para o maximo anual ser aceito

# =============================================================================
# 1. MAXIMAS ANUAIS EM MUCUM
# =============================================================================
mu = pd.read_csv(os.path.join(D_ANA, "86510000_vazao.csv"), **RD,
                 parse_dates=["data"])
mu["ano"] = mu.data.dt.year
g = mu.groupby("ano").vazao.agg(["max", "count"]).reset_index()
g = g[g["count"] >= COBERTURA_MIN]
qmax = g["max"].to_numpy(float)
n = len(qmax)

print("=" * 104)
print("1. MAXIMAS ANUAIS EM MUCUM (86510000)")
print("=" * 104)
print(f"  anos completos ....... {n}  ({int(g.ano.min())}-{int(g.ano.max())})")
print(f"  media ................ {qmax.mean():,.0f} m3/s")
print(f"  desvio-padrao ........ {qmax.std(ddof=1):,.0f} m3/s")
print(f"  coeficiente de variacao {qmax.std(ddof=1)/qmax.mean():.3f}")
print(f"  maxima ............... {qmax.max():,.0f} m3/s "
      f"({int(g.loc[g['max'].idxmax(),'ano'])})")

# =============================================================================
# 2. ANALISE DE FREQUENCIA — Gumbel
# =============================================================================
def gumbel_momentos(x):
    s = x.std(ddof=1); m = x.mean()
    alpha = s * np.sqrt(6) / np.pi
    mu_ = m - 0.5772 * alpha
    return mu_, alpha

def gumbel_lmom(x):
    """Momentos-L: mais robusto a valores extremos que os momentos comuns."""
    xs = np.sort(x); N = len(xs)
    b0 = xs.mean()
    b1 = np.sum([(i) / (N - 1) * xs[i] for i in range(N)]) / N
    l1, l2 = b0, 2 * b1 - b0
    alpha = l2 / np.log(2)
    mu_ = l1 - 0.5772 * alpha
    return mu_, alpha

def q_tr(TR, mu_, alpha):
    y = -np.log(-np.log(1 - 1 / np.asarray(TR, float)))
    return mu_ + alpha * y

def tr_de_q(q, mu_, alpha):
    y = (q - mu_) / alpha
    p = 1 - np.exp(-np.exp(-y))
    return 1 / p

mu_m, al_m = gumbel_momentos(qmax)
mu_l, al_l = gumbel_lmom(qmax)

TRs = [2, 5, 10, 25, 50, 100, 200, 500, 1000]
freq = pd.DataFrame(dict(
    TR=TRs,
    Q_mucum_momentos=np.round(q_tr(TRs, mu_m, al_m)),
    Q_mucum_Lmomentos=np.round(q_tr(TRs, mu_l, al_l))))

print("\n" + "=" * 104)
print("2. ANALISE DE FREQUENCIA EM MUCUM — Gumbel")
print("=" * 104)
print(freq.to_string(index=False))
print(f"\n  TR do evento de 2023 ({qmax.max():,.0f} m3/s):")
print(f"    por momentos ...... {tr_de_q(qmax.max(), mu_m, al_m):.0f} anos")
print(f"    por momentos-L .... {tr_de_q(qmax.max(), mu_l, al_l):.0f} anos")
q2024 = float(g.loc[g.ano == 2024, "max"].iloc[0]) if (g.ano == 2024).any() else np.nan
if np.isfinite(q2024):
    print(f"  TR do evento de 2024 ({q2024:,.0f} m3/s):")
    print(f"    por momentos ...... {tr_de_q(q2024, mu_m, al_m):.0f} anos")
    print(f"    por momentos-L .... {tr_de_q(q2024, mu_l, al_l):.0f} anos")

# =============================================================================
# 3. TRANSPOSICAO PARA ESTRELA
# =============================================================================
print("\n" + "=" * 104)
print("3. TRANSPOSICAO PARA ESTRELA")
print("=" * 104)
es = pd.read_csv(os.path.join(D_ANA, "86879300_vazao.csv"), **RD,
                 parse_dates=["data"])
es["ano"] = es.data.dt.year
ge = es.groupby("ano").vazao.agg(["max", "count"]).reset_index()
ge = ge[ge["count"] >= COBERTURA_MIN]
print("  maximas anuais registradas em Estrela:")
print(ge.rename(columns={"max": "q_max_m3s", "count": "dias"}).to_string(index=False))

# par observado de 2023: mesmo evento nos dois postos
q_es_2023 = float(ge.loc[ge.ano == 2023, "max"].iloc[0])
q_mu_2023 = float(g.loc[g.ano == 2023, "max"].iloc[0])
razao_obs = q_es_2023 / q_mu_2023
razao_area = AREA_POSTO_ESTRELA / AREA_MUCUM
expoente = np.log(razao_obs) / np.log(razao_area)
# pico no PONTO DE ANALISE (19.440 km2), transposto do posto (22.472 km2)
q_analise_obs = q_es_2023 * (AREA_ESTRELA / AREA_POSTO_ESTRELA) ** expoente
q_analise_085 = q_es_2023 * (AREA_ESTRELA / AREA_POSTO_ESTRELA) ** 0.85

print(f"\n  evento de 2023:")
print(f"    Mucum   {q_mu_2023:,.0f} m3/s  (area {AREA_MUCUM:,.0f} km2)")
print(f"    Estrela {q_es_2023:,.0f} m3/s  (area {AREA_POSTO_ESTRELA:,.0f} km2)")
print(f"    razao de vazao {razao_obs:.3f} para razao de area {razao_area:.3f}")
print(f"    expoente implicito: {expoente:.3f}")
print("\n  ATENCAO: expoente muito abaixo de 1 indica forte amortecimento na")
print("  planicie entre Mucum e Estrela — ou incerteza na curva-chave de")
print("  Estrela, que tem apenas 3 anos de dados e extrapola muito alem das")
print("  medicoes. As duas hipoteses tem consequencias opostas para o projeto.")

# vazoes de projeto em Estrela pelas duas hipoteses
rz = AREA_ESTRELA / AREA_MUCUM     # Mucum -> ponto de analise
freq["Q_analise_transposta"] = np.round(freq.Q_mucum_Lmomentos * rz ** expoente)
freq["Q_analise_exp085"] = np.round(freq.Q_mucum_Lmomentos * rz ** 0.85)
print(f"\n  pico observado de 2023 transposto para o ponto de analise "
      f"({AREA_ESTRELA:,.0f} km2):")
print(f"    com expoente observado ({expoente:.3f}): {q_analise_obs:,.0f} m3/s")
print(f"    com expoente 0,85 ..................... {q_analise_085:,.0f} m3/s")
print("\n  vazoes de projeto em Estrela:")
print(freq[["TR", "Q_mucum_Lmomentos", "Q_analise_transposta",
            "Q_analise_exp085"]].to_string(index=False))
freq.to_csv(os.path.join(D_OUT, "claude_c3_frequencia_mucum.csv"),
            index=False, sep=";", decimal=",")

# =============================================================================
# 4. LAMINA ESCOADA DO EVENTO
# =============================================================================
print("\n" + "=" * 104)
print("4. LAMINA ESCOADA DO EVENTO DE REFERENCIA")
print("=" * 104)
def lamina(df, col, area_km2, ini, fim, qbase=None):
    s = df[(df.data >= ini) & (df.data <= fim)].copy()
    if not len(s): return None
    qb = qbase if qbase is not None else float(s[col].quantile(0.10))
    vol = float(np.maximum(s[col] - qb, 0).sum()) * 86400          # m3
    return dict(dias=len(s), q_base=round(qb, 1), q_pico=round(float(s[col].max()), 1),
                volume_hm3=round(vol / 1e6, 1),
                lamina_mm=round(vol / (area_km2 * 1e6) * 1000, 1))

ev = []
for rot, ini, fim in [("set/2023", "2023-08-25", "2023-09-30"),
                      ("mai/2024", "2024-04-25", "2024-05-31")]:
    r = lamina(mu, "vazao", AREA_MUCUM, ini, fim)
    if r: ev.append(dict(evento=rot, posto="Mucum", **r))
r = lamina(es, "vazao", AREA_POSTO_ESTRELA, "2023-08-25", "2023-09-30")
if r: ev.append(dict(evento="set/2023", posto="Estrela", **r))
evd = pd.DataFrame(ev)
print(evd.to_string(index=False))
evd.to_csv(os.path.join(D_OUT, "claude_c3_hidrograma_observado.csv"),
           index=False, sep=";", decimal=",")

# =============================================================================
# 5. PARAMETROS CALIBRADOS
# =============================================================================
print("\n" + "=" * 104)
print("5. PARAMETROS CALIBRADOS PARA C1 E SINV")
print("=" * 104)
q_pico_cal = q_analise_obs
tr_evento = float(tr_de_q(q_mu_2023, mu_l, al_l))
lam_cal = float(evd.loc[evd.posto == "Estrela", "lamina_mm"].iloc[0]) \
    if (evd.posto == "Estrela").any() else float(evd.lamina_mm.mean())
qb_cal = float(evd.loc[evd.posto == "Estrela", "q_base"].iloc[0]) \
    if (evd.posto == "Estrela").any() else 600.0
cv_cal = float(qmax.std(ddof=1) / qmax.mean())

par = pd.DataFrame([
    dict(parametro="Q_PICO", antes=18000, calibrado=round(q_pico_cal),
         unidade="m3/s",
         fonte="posto 86879300 (22.472 km2) transposto ao ponto de analise (19.440 km2)"),
    dict(parametro="LAMINA_MM", antes=260, calibrado=round(lam_cal, 1),
         unidade="mm", fonte="integracao do hidrograma observado em Estrela"),
    dict(parametro="Q_BASE", antes=600, calibrado=round(qb_cal),
         unidade="m3/s", fonte="percentil 10 da janela do evento"),
    dict(parametro="TR_EVENTO", antes=100, calibrado=round(tr_evento),
         unidade="anos", fonte="Gumbel por momentos-L em Mucum, 86 anos"),
    dict(parametro="CV_GUMBEL", antes=0.45, calibrado=round(cv_cal, 3),
         unidade="-", fonte="serie de maximas anuais de Mucum"),
])
par.to_csv(os.path.join(D_OUT, "claude_c3_parametros_calibrados.csv"),
           index=False, sep=";", decimal=",")
print(par.to_string(index=False))

print("\n" + "-" * 104)
print("LEITURA")
print("-" * 104)
print(f"  Pico observado no POSTO de Estrela em 2023: {q_es_2023:,.0f} m3/s (22.472 km2).")
print(f"  Transposto ao PONTO DE ANALISE (19.440 km2): {q_pico_cal:,.0f} m3/s.")
print(f"  Contra os 18.000 arbitrados: diferenca de {100*(q_pico_cal/18000-1):+.1f}%.")
print(f"\n  O tempo de retorno, porem, NAO se confirma. Pela serie de 86 anos de")
print(f"  Mucum, o evento de 2023 tem TR de {tr_evento:.0f} anos, e nao 100.")
print(f"\n  A lamina escoada calibrada e' de {lam_cal:.0f} mm, contra 260 arbitrados.")
print("\n  Em Mucum, SETEMBRO/2023 foi MAIOR que MAIO/2024 "
      f"({q_mu_2023:,.0f} contra {q2024:,.0f} m3/s).")
print("  O evento de referencia do estudo deve ser explicitado: 2023 ou 2024.")
log("FIM")
