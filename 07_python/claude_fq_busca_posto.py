# -*- coding: utf-8 -*-
"""
EUROCLIMA / Estrela-RS — busca de posto fluviometrico no rio FORQUETA.

O pico de projeto do Forqueta usado em claude_fq_roteamento_calibrado.py
(3.183 m3/s) e' REGIONALIZADO: vem do rendimento especifico do Antas corrigido
por A^-0.15. Nao ha' medicao. Essa e' a maior incerteza do dimensionamento de
FQ1. Este script consulta o HidroInventario da ANA a procura de postos com
serie de vazao no Forqueta e nos seus formadores.

Saida: claude_fq_postos_candidatos.csv
"""
import os, re, time, warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import requests

D_OUT = os.path.join(os.environ["EURO"], "05_MODELAGEM", "06_resultados", "CLAUDE")
os.makedirs(D_OUT, exist_ok=True)
t0 = time.time()
def log(*a): print(f"[{time.time()-t0:6.1f}s]", *a, flush=True)
pd.set_option("display.width", 220)

URL = "http://telemetriaws1.ana.gov.br/ServiceANA.asmx/HidroInventario"
# retangulo generoso cobrindo a bacia do Forqueta
CX = dict(latitude=-29.6, longitude=-52.6, latitude2=-28.8, longitude2=-51.7)

def num(s):
    try: return float(str(s).replace(",", "."))
    except Exception: return np.nan

par = dict(codEstDE="", codEstATE="", tpEst="1", nmEst="", nmRio="",
           codSubBacia="", codBacia="", nmMunicipio="", nmEstado="",
           sgResp="", sgOper="", telemetrica="")
log("consultando HidroInventario da ANA...")
try:
    r = requests.get(URL, params=par, timeout=180)
    r.raise_for_status()
    xml = r.text
except Exception as e:
    log(f"FALHA na consulta: {e}")
    raise SystemExit(1)

corpo = xml.split("</xs:schema>")[-1]
recs = re.findall(r"<Table[^>]*>(.*?)</Table>", corpo, re.S)
log(f"{len(recs)} registros no inventario")

def campo(bloco, tag):
    m = re.search(rf"<{tag}>(.*?)</{tag}>", bloco, re.S)
    return m.group(1).strip() if m else ""

linhas = []
for b in recs:
    linhas.append(dict(
        codigo=campo(b, "Codigo"), nome=campo(b, "Nome"),
        rio=campo(b, "nmRio"), municipio=campo(b, "nmMunicipio"),
        estado=campo(b, "nmEstado"),
        lat=num(campo(b, "Latitude")), lon=num(campo(b, "Longitude")),
        area=num(campo(b, "AreaDrenagem")),
        tipo=campo(b, "TipoEstacao"),
        vazao=campo(b, "TipoEstacaoVazoes"),
        resp=campo(b, "ResponsavelSigla"),
        ini=campo(b, "PeriodoDescLiquidaInicio"),
        fim=campo(b, "PeriodoDescLiquidaFim")))
inv = pd.DataFrame(linhas)
log(f"{len(inv)} estacoes parseadas")

# filtro geografico + por nome do rio
na_caixa = inv[(inv.lat.between(CX["latitude"], CX["latitude2"])) &
               (inv.lon.between(CX["longitude"], CX["longitude2"]))].copy()
log(f"{len(na_caixa)} estacoes na caixa do Forqueta/Taquari")

print("\n  amostra dos campos disponiveis no primeiro registro:")
print("   ", {k: v for k, v in linhas[0].items()})
print(f"\n  registros na caixa com nmRio preenchido: "
      f"{(na_caixa.rio.str.len() > 0).sum()} de {len(na_caixa)}")

# O nome do rio nao vem preenchido no HidroInventario. Seleciona-se entao pela
# GEOMETRIA: postos dentro do poligono aproximado da bacia do Forqueta, que se
# estende a noroeste de Lajeado. Complementa-se pelo nome da estacao.
CAIXA_FQ = dict(lat=(-29.55, -29.00), lon=(-52.55, -51.85))
alvo = na_caixa[na_caixa.lat.between(*CAIXA_FQ["lat"]) &
                na_caixa.lon.between(*CAIXA_FQ["lon"])].copy()
alvo["provavel_forqueta"] = alvo.area.between(50, 3000)
alvo = alvo.sort_values("area", ascending=False)
alvo.to_csv(os.path.join(D_OUT, "claude_fq_postos_candidatos.csv"),
            index=False, sep=";", decimal=",")

print("\n" + "=" * 118)
print("POSTOS NA REGIAO DO FORQUETA (selecao geografica)")
print("=" * 118)
print(alvo[["codigo", "nome", "municipio", "lat", "lon", "area", "vazao",
            "resp", "provavel_forqueta"]].to_string(index=False))

fq = alvo[alvo.provavel_forqueta]
print("\n" + "-" * 118)
print("LEITURA")
print("-" * 118)
print(f"  {len(fq)} posto(s) com area entre 50 e 3.000 km2 na regiao — compativel")
print(f"  com a bacia do Forqueta (2.845,6 km2).")
if len(fq):
    com_q = fq[fq.vazao.astype(str).str.strip().isin(["1", "True", "true"])]
    print(f"  destes, {len(com_q)} declaram medicao de vazao:")
    for _, r in com_q.iterrows():
        print(f"    {r.codigo}  {r['nome'][:34]:<34} {r.municipio[:18]:<18} "
              f"{r.area:>8,.0f} km2")
    print("\n  Baixar essas series permite substituir o pico regionalizado do")
    print("  Forqueta (3.183 m3/s) por valor medido, e estimar a defasagem real")
    print("  ate' Estrela — hoje o parametro mais sensivel do dimensionamento.")
else:
    print("  O pico de projeto do Forqueta permanece regionalizado; instalar")
    print("  estacao no Forqueta deve entrar como recomendacao do Eixo 1 do TR.")
log("FIM")
