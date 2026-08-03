# -*- coding: utf-8 -*-
"""
EUROCLIMA / Estrela-RS — SERIES DO RIO FORQUETA e defasagem MEDIDA ate Estrela.

claude_fq_busca_posto.py localizou postos da ANA no Forqueta que nao estavam
no conjunto baixado em C2:

    86780000  BARRA DO FAO      2.077 km2   73% da bacia do Forqueta
    86745000  PASSO DO COIMBRA    791 km2   28%
    86700000  PONTE JACARE        436 km2   (arroio Jacare, outro tributario)

Com eles e' possivel:
  1. substituir o pico de projeto REGIONALIZADO do Forqueta (3.183 m3/s,
     obtido por A^-0.15 sobre o rendimento do Antas) por valor MEDIDO;
  2. medir a defasagem real entre o pico do Forqueta e o de Estrela, hoje o
     parametro mais sensivel de claude_fq_roteamento_calibrado.py.

Reaproveita o parser de claude_c2_baixa_ana.py (elemento <SerieHistorica>,
valores diarios em Vazao01..Vazao31 dentro de registros MENSAIS).

Saidas: 01_dados/ana_hidroweb/<cod>_vazao.csv
        06_resultados/CLAUDE/claude_fq_series_resumo.csv
        06_resultados/CLAUDE/claude_fq_defasagem_medida.csv
"""
import os, re, time, warnings, urllib.request, urllib.parse
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd

DEST = os.path.join(os.environ["EURO"], "05_MODELAGEM")
D_ANA = os.path.join(DEST, "01_dados", "ana_hidroweb")
D_OUT = os.path.join(DEST, "06_resultados", "CLAUDE")
for d in (D_ANA, D_OUT): os.makedirs(d, exist_ok=True)
t0 = time.time()
def log(*a): print(f"[{time.time()-t0:6.1f}s]", *a, flush=True)
pd.set_option("display.width", 220)

URL = "http://telemetriaws1.ana.gov.br/ServiceANA.asmx/HidroSerieHistorica"
POSTOS = [
    (86780000, "BARRA DO FAO (Forqueta)",     2077.0),
    (86745000, "PASSO DO COIMBRA (Forqueta)",  791.0),
    (86700000, "PONTE JACARE (arroio Jacare)", 436.0),
]
AREA_FORQUETA = 2845.6

def baixa(cod, tipo=3, ini="01/01/1930", fim="31/12/2026", tent=3):
    q = urllib.parse.urlencode(dict(codEstacao=cod, dataInicio=ini, dataFim=fim,
                                    tipoDados=tipo, nivelConsistencia=""))
    for k in range(tent):
        try:
            req = urllib.request.Request(f"{URL}?{q}",
                                         headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=300) as r:
                return r.read().decode("utf-8", "ignore")
        except Exception as e:
            log(f"    tentativa {k+1}/{tent}: {str(e)[:60]}"); time.sleep(3)
    return None

def parse(xml, campo="Vazao"):
    if not xml: return None
    corpo = xml.split("</xs:schema>")[-1]
    recs = re.findall(r"<SerieHistorica[^>]*>(.*?)</SerieHistorica>", corpo, re.S)
    if not recs: return None
    linhas = []
    for r in recs:
        dh = re.search(r"<DataHora>([^<]*)</DataHora>", r)
        nc = re.search(r"<NivelConsistencia>([^<]*)</NivelConsistencia>", r)
        if not dh: continue
        try: base = pd.Timestamp(dh.group(1)[:10])
        except Exception: continue
        cons = int(nc.group(1)) if nc and nc.group(1).strip() else 0
        for d in range(1, 32):
            m = re.search(rf"<{campo}{d:02d}>([^<]*)</{campo}{d:02d}>", r)
            if not m or not m.group(1).strip(): continue
            try: v = float(m.group(1))
            except ValueError: continue
            try: data = base.replace(day=d)
            except ValueError: continue
            linhas.append((data, v, cons))
    if not linhas: return None
    df = pd.DataFrame(linhas, columns=["data", campo.lower(), "consistencia"])
    df = df.sort_values(["data", "consistencia"], ascending=[True, False])
    return df.drop_duplicates("data").reset_index(drop=True)

log("=== baixando series do Forqueta ===")
resumo, series = [], {}
for cod, nome, area in POSTOS:
    arq = os.path.join(D_ANA, f"{cod}_vazao.csv")
    if os.path.exists(arq) and os.path.getsize(arq) > 200:
        df = pd.read_csv(arq, sep=";", decimal=",", parse_dates=["data"])
        log(f"  {cod} ja existe ({len(df)} registros)")
    else:
        log(f"  {cod} ({nome}) ...")
        df = parse(baixa(cod))
        if df is None or not len(df):
            log("    sem dados de vazao")
            resumo.append(dict(codigo=cod, nome=nome, area_km2=area, n=0)); continue
        df.to_csv(arq, index=False, sep=";", decimal=",")
        log(f"    {len(df)} registros | {df.data.min().date()} a {df.data.max().date()}")
    series[cod] = df
    resumo.append(dict(codigo=cod, nome=nome, area_km2=area, n=len(df),
                       inicio=str(df.data.min().date()), fim=str(df.data.max().date()),
                       anos=round((df.data.max()-df.data.min()).days/365.25, 1),
                       q_max_m3s=round(float(df.vazao.max()), 1),
                       q_medio_m3s=round(float(df.vazao.mean()), 2),
                       q_esp_medio=round(float(df.vazao.mean())/area, 4),
                       pct_consistido=round(100*float((df.consistencia == 2).mean()), 1)))
res = pd.DataFrame(resumo)
res.to_csv(os.path.join(D_OUT, "claude_fq_series_resumo.csv"),
           index=False, sep=";", decimal=",")
print("\n" + "=" * 118)
print("1. SERIES OBTIDAS NOS TRIBUTARIOS DE JUSANTE")
print("=" * 118)
print(res.to_string(index=False))

# Barra do Fao (2.077 km2) so' tem serie de COTA — nao ha vazao publicada.
# O posto de referencia do Forqueta passa a ser PASSO DO COIMBRA (791 km2),
# que tem 68,7 anos de vazao com 97,8% de dado consistido.
POSTO_FQ, A_POSTO_FQ = 86745000, 791.0
if POSTO_FQ not in series:
    log("sem serie de vazao no Forqueta — encerrando")
    raise SystemExit(0)
log(f"posto de referencia do Forqueta: {POSTO_FQ} ({A_POSTO_FQ:,.0f} km2)")
fq = series[POSTO_FQ].rename(columns={"vazao": "forqueta"})[["data", "forqueta"]]

# =============================================================================
# 2. PICO DE PROJETO MEDIDO
# =============================================================================
g = fq.copy(); g["ano"] = g.data.dt.year
mx = g.groupby("ano").forqueta.agg(["max", "count"]).reset_index()
mx = mx[mx["count"] >= 300]
print("\n" + "=" * 118)
print(f"2. MAXIMAS ANUAIS EM PASSO DO COIMBRA ({A_POSTO_FQ:,.0f} km2)")
print("=" * 118)
print(f"  {len(mx)} anos completos ({int(mx.ano.min())}-{int(mx.ano.max())})")
top = mx.nlargest(8, "max")
print("  oito maiores: " + ", ".join(f"{int(r.ano)}={r['max']:,.0f}" for _, r in top.iterrows()))

# Gumbel por momentos-L (mesmo metodo de C3)
x = np.sort(mx["max"].values); n = len(x)
b0 = x.mean()
b1 = sum((i) / (n - 1) * x[i] for i in range(n)) / n
l1, l2 = b0, 2 * b1 - b0
alfa = l2 / np.log(2); u = l1 - 0.5772 * alfa
TR = [2, 5, 10, 25, 50, 100, 200, 500, 1000]
qtr = {T: u - alfa * np.log(-np.log(1 - 1 / T)) for T in TR}
print(f"\n  Gumbel por momentos-L: u = {u:,.0f} | alfa = {alfa:,.0f}")
print("  " + " | ".join(f"TR{T}={qtr[T]:,.0f}" for T in TR))

# transposicao do posto (2.077 km2) para a bacia do Forqueta (2.845,6 km2)
f_area = (AREA_FORQUETA / A_POSTO_FQ) ** 0.85
print(f"\n  transposicao {A_POSTO_FQ:,.0f} -> {AREA_FORQUETA:,.1f} km2 "
      f"(expoente 0,85): fator {f_area:.3f}")
print(f"  ATENCAO: extrapolacao de {AREA_FORQUETA/A_POSTO_FQ:.1f}x em area. "
      f"Barra do Fao (2.077 km2) seria")
print(f"  o posto adequado, mas nao tem vazao publicada — so' cota. Reativar a")
print(f"  curva-chave de Barra do Fao e' recomendacao direta para o Eixo 1 do TR.")
q_max_obs = float(fq.forqueta.max())
print(f"  maxima observada          : {q_max_obs:,.0f} m3/s  -> "
      f"{q_max_obs*f_area:,.0f} m3/s na foz")
for T in (100, 200, 500):
    print(f"  Gumbel TR {T:>3d} anos        : {qtr[T]:,.0f} m3/s  -> "
          f"{qtr[T]*f_area:,.0f} m3/s na foz")
print(f"\n  valor REGIONALIZADO adotado em claude_fq_roteamento: 3.183 m3/s")

# =============================================================================
# 3. DEFASAGEM MEDIDA ATE ESTRELA
# =============================================================================
es = pd.read_csv(os.path.join(D_ANA, "86879300_vazao.csv"), sep=";", decimal=",",
                 parse_dates=["data"]).rename(columns={"vazao": "estrela"})
mu = pd.read_csv(os.path.join(D_ANA, "86510000_vazao.csv"), sep=";", decimal=",",
                 parse_dates=["data"]).rename(columns={"vazao": "mucum"})
j = (es[["data", "estrela"]].merge(fq, on="data", how="inner")
     .merge(mu[["data", "mucum"]], on="data", how="inner").sort_values("data"))
print("\n" + "=" * 118)
print("3. DEFASAGEM MEDIDA — Forqueta x Mucum x Estrela")
print("=" * 118)
print(f"  periodo comum aos tres postos: {len(j)} dias")

if len(j) < 30:
    print("  serie comum curta demais para medir defasagem por evento.")
    print("  Barra do Fao e Estrela tem periodos de operacao pouco sobrepostos.")
else:
    JAN, LIM = 5, 3000.0
    cand = j[j.estrela >= LIM]; usados, evs = set(), []
    for _, r in cand.sort_values("estrela", ascending=False).iterrows():
        if any(abs((r.data - d).days) < JAN for d in usados): continue
        usados.add(r.data)
        w = j[(j.data >= r.data - pd.Timedelta(days=JAN)) &
              (j.data <= r.data + pd.Timedelta(days=JAN))]
        evs.append(dict(
            evento=str(r.data.date()),
            q_forqueta=round(float(w.forqueta.max()), 1),
            data_pico_fq=str(w.loc[w.forqueta.idxmax(), "data"].date()),
            q_mucum=round(float(w.mucum.max()), 1),
            data_pico_mucum=str(w.loc[w.mucum.idxmax(), "data"].date()),
            q_estrela=round(float(w.estrela.max()), 1),
            data_pico_estrela=str(w.loc[w.estrela.idxmax(), "data"].date()),
            defasagem_fq_estrela_d=int((w.loc[w.estrela.idxmax(), "data"] -
                                        w.loc[w.forqueta.idxmax(), "data"]).days),
            contrib_fq_pct=round(100*float(w.forqueta.max())*f_area /
                                 float(w.estrela.max()), 1)))
    if evs:
        ed = pd.DataFrame(evs).sort_values("q_estrela", ascending=False)
        ed.to_csv(os.path.join(D_OUT, "claude_fq_defasagem_medida.csv"),
                  index=False, sep=";", decimal=",")
        print(ed.to_string(index=False))
        print(f"\n  defasagem Forqueta->Estrela: mediana "
              f"{ed.defasagem_fq_estrela_d.median():.0f} dia(s), "
              f"faixa {ed.defasagem_fq_estrela_d.min()} a "
              f"{ed.defasagem_fq_estrela_d.max()}")
        print(f"  contribuicao do Forqueta ao pico de Estrela: mediana "
              f"{ed.contrib_fq_pct.median():.0f}%, faixa "
              f"{ed.contrib_fq_pct.min():.0f}% a {ed.contrib_fq_pct.max():.0f}%")
    else:
        print(f"  nenhum evento acima de {LIM:,.0f} m3/s no periodo comum")
log("FIM")
