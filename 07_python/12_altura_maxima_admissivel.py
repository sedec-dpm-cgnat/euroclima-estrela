# -*- coding: utf-8 -*-
"""
EUROCLIMA / Estrela-RS — ALTURA MAXIMA ADMISSIVEL de cada eixo proposto.

A bacia do Taquari-Antas ja possui uma cascata de aproveitamentos em operacao
(complexo do rio das Antas: Monte Claro 130 MW, Castro Alves 130 MW,
14 de Julho 100 MW, alem de dezenas de PCH/CGH). O remanso de um novo
reservatorio nao pode afogar a casa de forca nem o canal de fuga de um
aproveitamento existente a montante.

Criterio (item 4.6.1 do Manual de Inventario Hidroeletrico, MME 2007):
  NAjn de um aproveitamento = nivel natural a jusante OU o NA maximo normal
  do reservatorio imediatamente a jusante, se este for mais elevado.

Aqui aplica-se a restricao inversa: a cota do NA maximo maximorum do eixo
proposto deve ficar ABAIXO da cota de restituicao do aproveitamento existente
imediatamente a montante, com uma folga de seguranca.

Saida: altura_maxima_admissivel.csv
"""
import os, warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import geopandas as gpd

DEST = os.path.join(os.environ["EURO"], "05_MODELAGEM")
D_GIS = os.path.join(DEST, "01_dados", "gis_derivado")
D_CAV = os.path.join(DEST, "01_dados", "cav")
D_TAB = os.path.join(DEST, "06_resultados", "tabelas")
UTM22 = 31982

FOLGA_M = 2.0          # folga entre o NA do novo reservatorio e o pe do existente

ap = gpd.read_file(os.path.join(D_GIS, "aproveitamentos.gpkg"), layer="aneel").to_crs(UTM22)
ap["potencia_MW"] = pd.to_numeric(
    ap.potencia_kW.astype(str).str.replace(",", "."), errors="coerce") / 1000.0
ex = pd.read_csv(os.path.join(D_CAV, "eixos_todos.csv"), sep=";", decimal=",")
geo = pd.read_csv(os.path.join(D_CAV, "geometria_todos.csv"), sep=";", decimal=",")

linhas = []
for _, e in ex.sort_values("area_km2").iterrows():
    # Aproveitamentos A MONTANTE do eixo, no MESMO curso d'agua.
    # Duas condicoes simultaneas, ambas necessarias:
    #   (a) area de drenagem MENOR  -> esta' mais acima na rede;
    #   (b) cota do terreno MAIOR   -> esta' mais alto que o eixo.
    # Sem a condicao (b) entram usinas de outros tributarios, que nao impoem
    # restricao alguma ao remanso do eixo analisado.
    mont = ap[(ap.area_drenagem_km2 < e.area_km2) &
              (ap.area_drenagem_km2 > e.area_km2 * 0.25) &
              (ap.cota_terreno_m > e.cota_eixo_m) &
              ap.cota_terreno_m.notna()].copy()
    if len(mont) == 0:
        h_max = np.nan; restr = "sem restricao identificada"; pot = np.nan; cota_r = np.nan
    else:
        # o que limita e' o de MENOR cota entre os de montante
        lim = mont.loc[mont.cota_terreno_m.idxmin()]
        cota_r = float(lim.cota_terreno_m)
        h_max = cota_r - FOLGA_M - e.cota_eixo_m
        restr = f"{lim['nome'][:26]} ({lim.situacao})"
        pot = lim.potencia_MW

    # volume e area disponiveis nessa altura
    sub = geo[geo.eixo == e.codigo].sort_values("altura_m")
    if np.isfinite(h_max) and h_max > 0 and len(sub):
        vol = float(np.interp(h_max, sub.altura_m, sub.volume_hm3))
        are = float(np.interp(h_max, sub.altura_m, sub.area_alagada_km2))
        cus = float(np.interp(h_max, sub.altura_m, sub.custo_total_MRS))
    else:
        vol = are = cus = np.nan

    linhas.append(dict(
        eixo=e.codigo, area_km2=e.area_km2, cota_eixo_m=e.cota_eixo_m,
        restricao=restr, potencia_restr_MW=round(pot, 1) if np.isfinite(pot) else np.nan,
        cota_restricao_m=cota_r,
        altura_max_m=round(h_max, 1) if np.isfinite(h_max) else np.nan,
        volume_max_hm3=round(vol, 1) if np.isfinite(vol) else np.nan,
        area_alagada_km2=round(are, 2) if np.isfinite(are) else np.nan,
        custo_MRS=round(cus) if np.isfinite(cus) else np.nan))

df = pd.DataFrame(linhas)
df.to_csv(os.path.join(D_TAB, "altura_maxima_admissivel.csv"),
          index=False, sep=";", decimal=",")

pd.set_option("display.width", 200)
print("=" * 118)
print("ALTURA MAXIMA ADMISSIVEL DE CADA EIXO — sem afogar aproveitamento existente a montante")
print(f"(folga adotada: {FOLGA_M:.0f} m)")
print("=" * 118)
print(df.to_string(index=False))

print("\n" + "=" * 118)
print("COMPARACAO — o que se pretendia x o que a cascata existente permite")
print("=" * 118)
ALVO = 90
for _, r in df.iterrows():
    sub = geo[geo.eixo == r.eixo].sort_values("altura_m")
    if not len(sub): continue
    v90 = float(np.interp(ALVO, sub.altura_m, sub.volume_hm3))
    if np.isfinite(r.altura_max_m) and r.altura_max_m > 0:
        perda = 100 * (1 - r.volume_max_hm3 / v90) if v90 > 0 else np.nan
        print(f"  {r.eixo}: pretendido {ALVO} m -> {v90:>7,.0f} hm3 | "
              f"admissivel {r.altura_max_m:>5.1f} m -> {r.volume_max_hm3:>7,.0f} hm3 "
              f"({perda:>5.1f}% de perda de volume)")
    else:
        print(f"  {r.eixo}: pretendido {ALVO} m -> {v90:>7,.0f} hm3 | "
              f"INVIAVEL — o eixo ja nasce afogado ou sem folga")

viaveis = df[(df.altura_max_m > 20) & df.volume_max_hm3.notna()]
print(f"\n  Eixos com pelo menos 20 m de altura admissivel: {len(viaveis)} de {len(df)}")
if len(viaveis):
    print(f"  Volume total mobilizavel respeitando a cascata: "
          f"{viaveis.volume_max_hm3.sum():,.0f} hm3")
