# -*- coding: utf-8 -*-
"""
EUROCLIMA / Estrela-RS — PAREAMENTO DE EVENTOS e revisao da transposicao.

ERRO CORRIGIDO
--------------
Em C3 a transposicao Mucum -> Estrela foi feita emparelhando os MAXIMOS ANUAIS
dos dois postos em 2023. Sao eventos DIFERENTES:

    Mucum   maximo anual: 15.092 m3/s em 05/09/2023
    Estrela maximo anual: 17.261 m3/s em 19/11/2023

No dia 19/11 Mucum registrou apenas 9.069 m3/s. Ou seja, a cheia que produziu o
maior pico em Estrela em 2023 NAO foi a mesma que produziu o maior pico em
Mucum. Emparelhar maximos anuais de postos distintos e' incorreto quando as
chuvas sao espacialmente variaveis.

O QUE SE FAZ AQUI
-----------------
1. Identifica os eventos independentes na serie comum aos dois postos.
2. Calcula a razao de vazao POR EVENTO, com pareamento por data.
3. Mostra como essa razao varia conforme a chuva se concentre a montante de
   Mucum ou nos tributarios de jusante (Forqueta e outros, 20,6% da bacia).
4. Reavalia o pico de referencia no ponto de analise.

Saidas: claude_c8_eventos_pareados.csv, claude_c8_transposicao_por_evento.csv
"""
import os, time, warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd

DEST = os.path.join(os.environ["EURO"], "05_MODELAGEM")
D_ANA = os.path.join(DEST, "01_dados", "ana_hidroweb")
D_OUT = os.path.join(DEST, "06_resultados", "CLAUDE")
RD = dict(sep=";", decimal=",", parse_dates=["data"])
os.makedirs(D_OUT, exist_ok=True)

t0 = time.time()
def log(*a): print(f"[{time.time()-t0:6.1f}s]", *a, flush=True)

AREA_MUCUM   = 16000.0
AREA_ESTRELA = 22472.0
AREA_ANALISE = 19440.0
JANELA_DIAS  = 5      # separacao minima entre eventos independentes
LIM_EVENTO   = 3000.0 # m3/s em Estrela para caracterizar evento de interesse

mu = pd.read_csv(os.path.join(D_ANA, "86510000_vazao.csv"), **RD)
es = pd.read_csv(os.path.join(D_ANA, "86879300_vazao.csv"), **RD)
j = (es[["data", "vazao"]].rename(columns={"vazao": "estrela"})
     .merge(mu[["data", "vazao"]].rename(columns={"vazao": "mucum"}),
            on="data", how="inner").sort_values("data").reset_index(drop=True))
log(f"periodo comum aos dois postos: {j.data.min().date()} a {j.data.max().date()} "
    f"({len(j)} dias)")

# =============================================================================
# 1. EVENTOS INDEPENDENTES
# =============================================================================
cand = j[j.estrela >= LIM_EVENTO].copy()
eventos = []
usados = set()
for _, r in cand.sort_values("estrela", ascending=False).iterrows():
    if any(abs((r.data - d).days) < JANELA_DIAS for d in usados): continue
    usados.add(r.data)
    # pico de cada posto na janela do evento
    w = j[(j.data >= r.data - pd.Timedelta(days=JANELA_DIAS)) &
          (j.data <= r.data + pd.Timedelta(days=JANELA_DIAS))]
    q_es = float(w.estrela.max()); q_mu = float(w.mucum.max())
    d_es = w.loc[w.estrela.idxmax(), "data"]
    d_mu = w.loc[w.mucum.idxmax(), "data"]
    eventos.append(dict(
        evento=str(r.data.date()),
        data_pico_estrela=str(d_es.date()), q_estrela=round(q_es, 1),
        data_pico_mucum=str(d_mu.date()), q_mucum=round(q_mu, 1),
        defasagem_dias=int((d_es - d_mu).days),
        razao_q=round(q_es / q_mu, 3) if q_mu > 0 else np.nan))
ev = pd.DataFrame(eventos).sort_values("q_estrela", ascending=False)
ev.to_csv(os.path.join(D_OUT, "claude_c8_eventos_pareados.csv"),
          index=False, sep=";", decimal=",")

pd.set_option("display.width", 200)
print("=" * 110)
print(f"1. EVENTOS INDEPENDENTES (Estrela >= {LIM_EVENTO:,.0f} m3/s)")
print("=" * 110)
print(ev.to_string(index=False))

# =============================================================================
# 2. TRANSPOSICAO POR EVENTO
# =============================================================================
rz_area = AREA_ESTRELA / AREA_MUCUM
ev["expoente"] = np.log(ev.razao_q) / np.log(rz_area)
ev["origem_da_cheia"] = np.where(
    ev.expoente > 1.0, "tributarios de jusante dominam",
    np.where(ev.expoente < 0.5, "montante de Mucum domina; forte amortecimento",
             "distribuida"))

print("\n" + "=" * 110)
print("2. EXPOENTE DE TRANSPOSICAO POR EVENTO")
print("=" * 110)
print(f"  razao de area Estrela/Mucum = {rz_area:.3f}\n")
print(ev[["evento", "q_mucum", "q_estrela", "razao_q", "expoente",
          "origem_da_cheia"]].to_string(index=False))
ev.to_csv(os.path.join(D_OUT, "claude_c8_transposicao_por_evento.csv"),
          index=False, sep=";", decimal=",")

print(f"\n  expoente: minimo {ev.expoente.min():.3f} | mediana "
      f"{ev.expoente.median():.3f} | maximo {ev.expoente.max():.3f}")

# =============================================================================
# 3. LEITURA
# =============================================================================
print("\n" + "-" * 110)
print("LEITURA")
print("-" * 110)
print("  A razao de vazao entre Estrela e Mucum NAO e' uma propriedade fixa da")
print("  bacia: varia de evento para evento conforme a chuva se concentre a")
print("  montante de Mucum ou nos tributarios de jusante. O Rio Forqueta")
print("  sozinho responde por 14,63% da area em Estrela.")
print("\n  Consequencia: a TRANSPOSICAO POR AREA nao e' metodo valido para")
print("  definir o pico de referencia neste caso. O expoente 'observado' de")
print("  0,395 calculado em C3 era artefato de emparelhar maximos anuais de")
print("  eventos diferentes.")

top = ev.iloc[0]
print(f"\n  Maior pico registrado em Estrela: {top.q_estrela:,.0f} m3/s em "
      f"{top.data_pico_estrela}")
print(f"    naquele evento Mucum registrou {top.q_mucum:,.0f} m3/s "
      f"(razao {top.razao_q:.2f})")
setembro = ev[ev.data_pico_mucum.str.startswith("2023-09")]
if len(setembro):
    s = setembro.iloc[0]
    print(f"\n  Evento de setembro/2023 (o maior em Mucum):")
    print(f"    Mucum {s.q_mucum:,.0f} | Estrela {s.q_estrela:,.0f} "
          f"(razao {s.razao_q:.2f})")

print("\n  RECOMENDACAO para o pico de referencia no ponto de analise")
print("  (19.440 km2, limite de montante do trecho):")
print("    - a serie de Estrela e' curta (3,1 anos) mas e' a UNICA medicao")
print("      direta proxima do ponto de analise;")
print("    - o maior valor registrado e' 17.261 m3/s;")
print("    - a transposicao para 19.440 km2 depende do evento, e por isso")
print("      recomenda-se adotar a FAIXA e nao um valor unico.")
q_lo = 17260.9 * (AREA_ANALISE / AREA_ESTRELA) ** 1.0
q_hi = 17260.9 * (AREA_ANALISE / AREA_ESTRELA) ** 0.0
print(f"    faixa: {q_lo:,.0f} a {q_hi:,.0f} m3/s "
      f"(expoentes 1,0 e 0,0 como limites)")
print(f"    valor adotado em C3/C4: 16.300 m3/s — dentro da faixa, "
      f"corresponde a expoente 0,395")
log("FIM")
