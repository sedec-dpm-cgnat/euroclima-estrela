# -*- coding: utf-8 -*-
"""
EUROCLIMA / Estrela-RS — INTERFERENCIA DOS EIXOS DO FORQUETA COM APROVEITAMENTOS
EXISTENTES E EM ESTUDO.

Motivo (levantado pelo usuario): o rio Forqueta JA' TEM PCHs em operacao. Propor
reservatorio de acumulacao em FQ1 ou FQ2 exige verificar se o nivel de agua
maximo maximorum AFOGA esses aproveitamentos. O criterio e' de COTA, nao de
distancia.

Fonte das cotas: 06_resultados/tabelas/aproveitamentos_existentes.csv, que ja'
traz cota_terreno_m amostrada do MDE para cada aproveitamento (ANEEL + SIGA),
e as cotas de eixo do pipeline de CAV do Forqueta. Nao depende de GDAL.

Criterio (o mesmo de claude_04_interferencia_energetica.py):
    AFOGA   : NA maximo do eixo acima da cota do aproveitamento
    REMANSO : NA maximo entre a cota e 5 m abaixo dela
    livre   : NA maximo mais de 5 m abaixo da cota

Saidas: claude_fq_interferencia_pch.csv
        claude_fq_altura_livre_interferencia.csv
"""
import os, time, warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd

DEST = os.path.join(os.environ["EURO"], "05_MODELAGEM")
D_TAB = os.path.join(DEST, "06_resultados", "tabelas")
D_OUT = os.path.join(DEST, "06_resultados", "CLAUDE")
RD = dict(sep=";", decimal=",", encoding="utf-8-sig")
os.makedirs(D_OUT, exist_ok=True)
t0 = time.time()
def log(*a): print(f"[{time.time()-t0:6.1f}s]", *a, flush=True)
pd.set_option("display.width", 230)

# eixos propostos (pipeline 01_dados/cav_forqueta)
EIXOS = {
    "FQ1": dict(lat=-29.403114, lon=-52.029566, cota_eixo=22.5, area=2350.1,
                papel="candidato prioritario"),
    "FQ2": dict(lat=-29.322861, lon=-52.090824, cota_eixo=40.0, area=2204.2,
                papel="sensibilidade locacional"),
}
ALTURAS = [15, 20, 25, 30, 35, 40, 45, 50, 60, 70]
MARGEM_REMANSO = 5.0

# caixa da bacia do Forqueta
CX = dict(lat=(-29.55, -28.95), lon=(-52.60, -51.95))

apr = pd.read_csv(os.path.join(D_TAB, "aproveitamentos_existentes.csv"), **RD)
apr["potencia_MW"] = pd.to_numeric(
    apr.potencia_kW.astype(str).str.replace(",", "."), errors="coerce") / 1000.0
fq = apr[apr.lat.between(*CX["lat"]) & apr.lon.between(*CX["lon"])].copy()
fq = fq.sort_values("area_drenagem_km2")
log(f"{len(fq)} aproveitamentos na caixa da bacia do Forqueta")

print("=" * 122)
print("1. APROVEITAMENTOS NA BACIA DO FORQUETA")
print("=" * 122)
print(fq[["situacao", "nome", "potencia_MW", "municipio", "area_drenagem_km2",
          "cota_terreno_m", "curso_dagua"]].to_string(index=False))

# =============================================================================
# 2. INTERFERENCIA MUTUA ENTRE OS DOIS EIXOS PROPOSTOS
# =============================================================================
print("\n" + "=" * 122)
print("2. INTERFERENCIA MUTUA ENTRE FQ1 E FQ2")
print("=" * 122)
c1, c2 = EIXOS["FQ1"]["cota_eixo"], EIXOS["FQ2"]["cota_eixo"]
print(f"  cota do eixo FQ1 (jusante, 2.350,1 km2): {c1:.1f} m")
print(f"  cota do eixo FQ2 (montante, 2.204,2 km2): {c2:.1f} m")
print(f"  desnivel entre os dois eixos: {c2 - c1:.1f} m\n")
mut = []
for H in ALTURAS:
    NA1 = c1 + H
    if NA1 > c2:                       sit = "AFOGA o eixo FQ2"
    elif NA1 > c2 - MARGEM_REMANSO:    sit = "REMANSO sobre FQ2"
    else:                              sit = "livre"
    mut.append(dict(altura_FQ1_m=H, NA_mx_FQ1_m=round(NA1, 1),
                    cota_eixo_FQ2_m=c2, folga_m=round(c2 - NA1, 1), situacao=sit))
mu = pd.DataFrame(mut)
print(mu.to_string(index=False))
h_lim_mutuo = max([H for H in ALTURAS if c1 + H <= c2 - MARGEM_REMANSO] or [0])
print(f"\n  Altura maxima de FQ1 sem interferir em FQ2: {h_lim_mutuo} m")
print(f"  Na altura de projeto de 30 m, o NA de FQ1 fica {c1+30-c2:+.1f} m em")
print(f"  relacao ao eixo de FQ2. Os dois eixos NAO sao compativeis nessa altura.")

# =============================================================================
# 3. INTERFERENCIA COM OS APROVEITAMENTOS
# =============================================================================
regs = []
for eixo, e in EIXOS.items():
    # so' interferem os que estao A MONTANTE: area menor e cota igual ou maior
    alvo = fq[(fq.area_drenagem_km2 < e["area"]) &
              (fq.cota_terreno_m >= e["cota_eixo"])].copy()
    for _, a in alvo.iterrows():
        for H in ALTURAS:
            NA = e["cota_eixo"] + H
            if NA > a.cota_terreno_m:                    sit = "AFOGA"
            elif NA > a.cota_terreno_m - MARGEM_REMANSO: sit = "REMANSO"
            else:                                        sit = "livre"
            regs.append(dict(
                eixo=eixo, altura_m=H, NA_mx_m=round(NA, 1),
                aproveitamento=a["nome"], situacao_apr=a.situacao,
                potencia_MW=a.potencia_MW, area_km2=a.area_drenagem_km2,
                cota_apr_m=a.cota_terreno_m,
                folga_m=round(a.cota_terreno_m - NA, 1), situacao=sit))
it = pd.DataFrame(regs)
it.to_csv(os.path.join(D_OUT, "claude_fq_interferencia_pch.csv"),
          index=False, sep=";", decimal=",")

print("\n" + "=" * 122)
print("3. INTERFERENCIA COM APROVEITAMENTOS A MONTANTE")
print("=" * 122)
for eixo in EIXOS:
    s = it[it.eixo == eixo]
    print(f"\n  --- {eixo} (cota do eixo {EIXOS[eixo]['cota_eixo']:.1f} m) — "
          f"{s.aproveitamento.nunique()} aproveitamentos a montante ---")
    if not len(s): print("    nenhum"); continue
    crit = (s.groupby(["aproveitamento", "situacao_apr", "potencia_MW",
                       "cota_apr_m"]).size().reset_index()
            .sort_values("cota_apr_m").head(6))
    print("    mais baixos (primeiros a serem atingidos):")
    for _, r in crit.iterrows():
        print(f"      {r.aproveitamento[:28]:<28} {r.situacao_apr:<9} "
              f"{r.potencia_MW:>7.2f} MW  cota {r.cota_apr_m:>7.1f} m")
    afoga = s[s.situacao == "AFOGA"]
    if len(afoga):
        print(f"    primeira altura que afoga algum: "
              f"{afoga.altura_m.min()} m ({afoga.loc[afoga.altura_m.idxmin(),'aproveitamento']})")
    else:
        print(f"    nenhum e' afogado ate' {max(ALTURAS)} m")

# =============================================================================
# 4. ALTURA MAXIMA LIVRE
# =============================================================================
lim = []
for eixo, e in EIXOS.items():
    s = it[it.eixo == eixo]
    if len(s):
        c_min = s.cota_apr_m.min()
        alvo0 = s.loc[s.cota_apr_m.idxmin(), "aproveitamento"]
        h_apr = max([H for H in ALTURAS
                     if e["cota_eixo"] + H <= c_min - MARGEM_REMANSO] or [0])
    else:
        c_min, alvo0, h_apr = np.nan, "nenhum", max(ALTURAS)
    h_mut = h_lim_mutuo if eixo == "FQ1" else max(ALTURAS)
    lim.append(dict(eixo=eixo, altura_livre_aproveitamentos_m=h_apr,
                    aproveitamento_limitante=alvo0,
                    cota_limitante_m=c_min,
                    altura_livre_eixo_vizinho_m=h_mut,
                    altura_maxima_recomendada_m=min(h_apr, h_mut)))
lm = pd.DataFrame(lim)
lm.to_csv(os.path.join(D_OUT, "claude_fq_altura_livre_interferencia.csv"),
          index=False, sep=";", decimal=",")
print("\n" + "=" * 122)
print("4. ALTURA MAXIMA LIVRE DE INTERFERENCIA")
print("=" * 122)
print(lm.to_string(index=False))

print("\n" + "-" * 122)
print("LEITURA")
print("-" * 122)
for _, r in lm.iterrows():
    ok = "COMPATIVEL" if r.altura_maxima_recomendada_m >= 30 else "CONFLITO"
    print(f"  {r.eixo}: altura de projeto 30 m contra limite de "
          f"{r.altura_maxima_recomendada_m} m -> {ok}")
print(f"\n  As PCHs em operacao no Forqueta (Vale do Leite 6,4 MW, Salto Forqueta")
print(f"  6,1 MW, Rastro de Auto 7,0 MW) ficam entre as cotas 130,9 e 277,4 m,")
print(f"  muito acima do NA de FQ1 (52,5 m) e de FQ2 (70,0 m) com 30 m de altura.")
print(f"  A restricao efetiva NAO vem das PCHs, e sim da INCOMPATIBILIDADE ENTRE")
print(f"  OS DOIS EIXOS PROPOSTOS: FQ1 com mais de {h_lim_mutuo} m afoga o eixo de FQ2.")
print(f"\n  Ressalva: cota_terreno_m e' a cota do TERRENO no ponto, nao o NA")
print(f"  operativo nem a cota da casa de forca. Confirmar junto a CERTEL e a")
print(f"  ANEEL antes de qualquer decisao. O remanso de FQ1 sobre a planicie do")
print(f"  Forqueta tambem precisa ser calculado em regime permanente (Codex).")
log("FIM")
