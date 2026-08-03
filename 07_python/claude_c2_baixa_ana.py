# -*- coding: utf-8 -*-
"""
EUROCLIMA / Estrela-RS — C2: SERIES FLUVIOMETRICAS DA ANA.

O script em R (`02_R/01_baixa_dados_ana.R`) retornava "sem dados" para todos os
postos. O endpoint SOAP legado FUNCIONA — o problema era o parser, que procurava
o elemento `<DadosHidrometereologicos>`. A resposta real usa:

    <DocumentElement>
      <SerieHistorica diffgr:id="..." msdata:rowOrder="0">
        <EstacaoCodigo>86510000</EstacaoCodigo>
        <NivelConsistencia>1</NivelConsistencia>
        <DataHora>2024-12-01 00:00:00</DataHora>
        <Maxima>...</Maxima> <Minima>...</Minima> <Media>...</Media>
        <Vazao01>...</Vazao01> ... <Vazao31>...</Vazao31>
      </SerieHistorica>

Cada registro e' um MES; os valores diarios estao em Vazao01..Vazao31
(ou Cota01..Cota31 para tipoDados=1). O elemento traz atributos, o que tambem
quebrava buscas por `<SerieHistorica>` literal.

Postos: 86870000 e 86879300 (Lajeado/Estrela), 86510000 (Mucum),
86720000 (Encantado), 86560000 e 86440000 (cabeceiras).

Saidas: 01_dados/ana_hidroweb/<codigo>_<tipo>.csv
        06_resultados/CLAUDE/claude_c2_series_resumo.csv
        06_resultados/CLAUDE/claude_c2_maximas_anuais.csv
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

URL = "http://telemetriaws1.ana.gov.br/ServiceANA.asmx/HidroSerieHistorica"
POSTOS = [
    (86870000, "Lajeado (antigo)"),
    (86879300, "Estrela / Lajeado (atual)"),
    (86510000, "Mucum"),
    (86720000, "Encantado"),
    (86560000, "Passo Tainhas / Antas"),
    (86440000, "Bento Goncalves"),
]
TIPOS = {1: "cota", 3: "vazao"}
CAMPO = {1: "Cota", 3: "Vazao"}


def baixa(cod, tipo, ini="01/01/1930", fim="31/12/2026", tentativas=3):
    q = urllib.parse.urlencode(dict(
        codEstacao=cod, dataInicio=ini, dataFim=fim,
        tipoDados=tipo, nivelConsistencia=""))
    for k in range(tentativas):
        try:
            req = urllib.request.Request(f"{URL}?{q}",
                                         headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=300) as r:
                return r.read().decode("utf-8", "ignore")
        except Exception as e:
            log(f"    tentativa {k+1}/{tentativas} falhou: {str(e)[:60]}")
            time.sleep(3)
    return None


def parse(xml, tipo):
    """Extrai a serie diaria dos registros mensais."""
    if not xml: return None
    corpo = xml.split("</xs:schema>")[-1]
    recs = re.findall(r"<SerieHistorica[^>]*>(.*?)</SerieHistorica>", corpo, re.S)
    if not recs: return None
    campo = CAMPO[tipo]
    linhas = []
    for r in recs:
        dh = re.search(r"<DataHora>([^<]*)</DataHora>", r)
        nc = re.search(r"<NivelConsistencia>([^<]*)</NivelConsistencia>", r)
        if not dh: continue
        try:
            base = pd.Timestamp(dh.group(1)[:10])
        except Exception:
            continue
        consist = int(nc.group(1)) if nc and nc.group(1).strip() else 0
        for d in range(1, 32):
            m = re.search(rf"<{campo}{d:02d}>([^<]*)</{campo}{d:02d}>", r)
            if not m or not m.group(1).strip(): continue
            try:
                v = float(m.group(1))
            except ValueError:
                continue
            try:
                data = base.replace(day=d)
            except ValueError:
                continue          # dia inexistente no mes
            linhas.append((data, v, consist))
    if not linhas: return None
    df = pd.DataFrame(linhas, columns=["data", campo.lower(), "consistencia"])
    # mantem o dado CONSISTIDO (nivel 2) quando ha' duplicidade
    df = df.sort_values(["data", "consistencia"], ascending=[True, False])
    return df.drop_duplicates("data").reset_index(drop=True)


log("=== baixando series ANA/HidroWeb ===")
resumo, series = [], {}
for cod, nome in POSTOS:
    for tipo, rot in TIPOS.items():
        arq = os.path.join(D_ANA, f"{cod}_{rot}.csv")
        if os.path.exists(arq) and os.path.getsize(arq) > 200:
            df = pd.read_csv(arq, sep=";", decimal=",", parse_dates=["data"])
            log(f"  {cod} {rot}: ja existe ({len(df)} registros)")
        else:
            log(f"  {cod} ({nome}) - {rot} ...")
            df = parse(baixa(cod, tipo), tipo)
            if df is None or not len(df):
                log("    sem dados"); resumo.append(dict(
                    codigo=cod, nome=nome, tipo=rot, n=0)); continue
            df.to_csv(arq, index=False, sep=";", decimal=",")
            log(f"    {len(df)} registros | {df.data.min().date()} a {df.data.max().date()}")
        col = "vazao" if rot == "vazao" else "cota"
        series[(cod, rot)] = df
        resumo.append(dict(
            codigo=cod, nome=nome, tipo=rot, n=len(df),
            inicio=str(df.data.min().date()), fim=str(df.data.max().date()),
            anos=round((df.data.max() - df.data.min()).days / 365.25, 1),
            maximo=round(float(df[col].max()), 2),
            media=round(float(df[col].mean()), 2),
            pct_consistido=round(100 * float((df.consistencia == 2).mean()), 1)))

res = pd.DataFrame(resumo)
res.to_csv(os.path.join(D_OUT, "claude_c2_series_resumo.csv"),
           index=False, sep=";", decimal=",")
pd.set_option("display.width", 200)
print("\n" + "=" * 118)
print("SERIES OBTIDAS")
print("=" * 118)
print(res.to_string(index=False))

# =============================================================================
# MAXIMAS ANUAIS — base da analise de frequencia (C3)
# =============================================================================
print("\n" + "=" * 118)
print("MAXIMAS ANUAIS DE VAZAO")
print("=" * 118)
maxs = []
for (cod, rot), df in series.items():
    if rot != "vazao": continue
    nome = dict(POSTOS)[cod]
    g = df.copy(); g["ano"] = g.data.dt.year
    mx = g.groupby("ano").vazao.agg(["max", "count"]).reset_index()
    mx = mx[mx["count"] >= 300]        # so anos com cobertura suficiente
    for _, r in mx.iterrows():
        maxs.append(dict(codigo=cod, nome=nome, ano=int(r.ano),
                         q_max_m3s=round(float(r["max"]), 2),
                         dias_com_dado=int(r["count"])))
if maxs:
    mdf = pd.DataFrame(maxs)
    mdf.to_csv(os.path.join(D_OUT, "claude_c2_maximas_anuais.csv"),
               index=False, sep=";", decimal=",")
    for cod in mdf.codigo.unique():
        s = mdf[mdf.codigo == cod]
        print(f"\n  {s.nome.iloc[0]} ({cod}): {len(s)} anos completos "
              f"({s.ano.min()}-{s.ano.max()})")
        print(f"    maxima da serie: {s.q_max_m3s.max():,.0f} m3/s em {int(s.loc[s.q_max_m3s.idxmax(),'ano'])}")
        print(f"    media das maximas anuais: {s.q_max_m3s.mean():,.0f} m3/s")
        top = s.nlargest(5, "q_max_m3s")[["ano", "q_max_m3s"]]
        print("    cinco maiores: " +
              ", ".join(f"{int(r.ano)}={r.q_max_m3s:,.0f}" for _, r in top.iterrows()))
else:
    print("  nenhuma serie de vazao obtida")
log("FIM")
