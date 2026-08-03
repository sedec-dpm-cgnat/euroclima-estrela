# -*- coding: utf-8 -*-
"""
EUROCLIMA / Estrela-RS — AUDITORIA das CAVs interpoladas dos eixos novos.

Audita a saida de `27_ajusta_cav_eixos_novos.py`:

  1. FIDELIDADE DA PCHIP — a curva monotonica reproduz exatamente os 23 pontos
     originais de cada eixo? (deve reproduzir: PCHIP e' interpoladora)
  2. POLINOMIOS — RMSE, erro maximo, erro RELATIVO por faixa de altura,
     monotonicidade e comportamento nos extremos
  3. COERENCIA COM AS ALTURAS ADMISSIVEIS revisadas
  4. TABELA FINAL consolidada com nivel de confiabilidade

Nao sobrescreve `cav_todos.csv`, `geometria_todos.csv` nem
`prioridade_eixos_revisada.csv`. Saidas com prefixo claude_ em
`06_resultados/CLAUDE/`.
"""
import os, json, time, warnings
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

RD = dict(sep=";", decimal=",", encoding="utf-8-sig")

orig = pd.read_csv(os.path.join(D_CAV, "cav_todos.csv"), **RD)
dens = pd.read_csv(os.path.join(D_TAB, "cav_eixos_novos_interpolada_1m.csv"), **RD)
fits = pd.read_csv(os.path.join(D_TAB, "cav_eixos_novos_ajustes_polinomiais.csv"), **RD)
with open(os.path.join(D_TAB, "cav_eixos_novos_modelos.json"), encoding="utf-8") as f:
    modelos = json.load(f)
rev = pd.read_csv(os.path.join(D_OUT, "claude_altura_admissivel_revisada.csv"), **RD)

log(f"originais {len(orig)} | interpolados {len(dens)} | ajustes {len(fits)}")

# =============================================================================
# 1. FIDELIDADE DA INTERPOLACAO MONOTONICA NOS PONTOS ORIGINAIS
# =============================================================================
print("=" * 112)
print("1. FIDELIDADE DA PCHIP — reproducao dos pontos originais")
print("=" * 112)

m = orig.merge(dens, on=["eixo", "altura_m"], suffixes=("_orig", "_pchip"))
m["erro_area"] = m.area_alagada_km2_pchip - m.area_alagada_km2_orig
m["erro_volume"] = m.volume_hm3_pchip - m.volume_hm3_orig

fid = m.groupby("eixo").agg(
    n_pontos=("altura_m", "count"),
    erro_max_area=("erro_area", lambda s: float(np.max(np.abs(s)))),
    erro_max_volume=("erro_volume", lambda s: float(np.max(np.abs(s))))).reset_index()

print(fid.to_string(index=False))
tol = 1e-6
ok = bool((fid.erro_max_area < tol).all() and (fid.erro_max_volume < tol).all())
print(f"\n  pontos originais conferidos: {len(m)} de {len(orig)}")
print(f"  reproducao exata (tolerancia {tol:g}): {'SIM' if ok else 'NAO'}")
if not ok:
    print("  ATENCAO: a PCHIP deveria passar exatamente pelos nos. Verificar.")
else:
    print("  A PCHIP e' interpoladora e passa pelos nos, como esperado.")

# =============================================================================
# 2. AVALIACAO DOS POLINOMIOS
# =============================================================================
print("\n" + "=" * 112)
print("2. POLINOMIOS — erro absoluto, erro RELATIVO e monotonicidade")
print("=" * 112)

def polyval_scaled(coefs, centro, meia, x):
    u = (np.asarray(x, float) - centro) / meia
    return np.polynomial.polynomial.polyval(u, coefs)

linhas = []
for eixo, mod in modelos.items():
    o = orig[orig.eixo == eixo].sort_values("altura_m")
    x = o.altura_m.to_numpy(float)
    for var, col in [("area", "area_alagada_km2"), ("volume", "volume_hm3")]:
        y = o[col].to_numpy(float)
        for grau in (2, 3, 4):
            mm = mod["modelos"][f"{var}_grau_{grau}"]
            pred = polyval_scaled(mm["coeficientes_potencia_crescente"],
                                  mm["centro_m"], mm["meia_amplitude_m"], x)
            err = pred - y
            # erro relativo por faixa de altura
            baixa = x <= 40
            alta = x >= 80
            rel = np.abs(err) / np.maximum(np.abs(y), 1e-9)
            # negatividade: o polinomio produz valores negativos?
            dens_x = np.linspace(x.min(), x.max(), 501)
            dp = polyval_scaled(mm["coeficientes_potencia_crescente"],
                                mm["centro_m"], mm["meia_amplitude_m"], dens_x)
            linhas.append(dict(
                eixo=eixo, variavel=var, grau=grau,
                rmse=round(float(np.sqrt(np.mean(err ** 2))), 4),
                erro_max=round(float(np.max(np.abs(err))), 4),
                erro_rel_medio_pct=round(100 * float(np.mean(rel)), 2),
                erro_rel_max_pct=round(100 * float(np.max(rel)), 2),
                erro_rel_alturas_ate_40m_pct=round(100 * float(np.max(rel[baixa])), 2),
                erro_rel_alturas_acima_80m_pct=round(100 * float(np.max(rel[alta])), 2),
                monotono=bool(mm["monotono_no_intervalo"]),
                produz_negativo=bool(np.any(dp < -1e-9)),
                valor_min_no_intervalo=round(float(dp.min()), 3)))

pol = pd.DataFrame(linhas)
pol.to_csv(os.path.join(D_OUT, "claude_auditoria_polinomios_cav.csv"),
           index=False, sep=";", decimal=",")

pd.set_option("display.width", 230)
print("\n--- grau 3 (cubico), que e' o recomendado como forma compacta ---")
print(pol[pol.grau == 3][[
    "eixo", "variavel", "rmse", "erro_max", "erro_rel_medio_pct",
    "erro_rel_alturas_ate_40m_pct", "erro_rel_alturas_acima_80m_pct",
    "monotono", "produz_negativo", "valor_min_no_intervalo"]].to_string(index=False))

print("\n--- problemas por grau ---")
for g in (2, 3, 4):
    s = pol[pol.grau == g]
    nm = int((~s.monotono).sum()); ng = int(s.produz_negativo.sum())
    pior = s.erro_rel_alturas_ate_40m_pct.max()
    print(f"  grau {g}: {nm} nao-monotonicos, {ng} produzem valor negativo, "
          f"pior erro relativo ate 40 m = {pior:.0f}%")

print("\n  LEITURA")
print("  O erro ABSOLUTO do polinomio e' pequeno frente ao volume nas alturas")
print("  altas, mas a mesma magnitude de erro nas alturas BAIXAS representa")
print("  fracao enorme do volume, porque a curva cota-volume e' fortemente")
print("  convexa. Por isso o polinomio nao serve como modelo operacional.")

# =============================================================================
# 3. COERENCIA COM AS ALTURAS ADMISSIVEIS REVISADAS
# =============================================================================
print("\n" + "=" * 112)
print("3. COERENCIA — volume interpolado nas alturas admissiveis revisadas")
print("=" * 112)

chk = []
for _, r in rev.iterrows():
    d = dens[dens.eixo == r.eixo].sort_values("altura_m")
    if not len(d) or not np.isfinite(r.altura_max_m):
        continue
    H = float(r.altura_max_m)
    dentro = d.altura_m.min() <= H <= d.altura_m.max()
    v_pchip = float(np.interp(H, d.altura_m, d.volume_hm3))
    a_pchip = float(np.interp(H, d.altura_m, d.area_alagada_km2))
    # comparacao com o valor que a tabela revisada carrega (interp linear 5 m)
    dif = v_pchip - float(r.volume_max_hm3) if np.isfinite(r.volume_max_hm3) else np.nan
    chk.append(dict(
        eixo=r.eixo, altura_adm_m=round(H, 1),
        dentro_do_intervalo=bool(dentro),
        volume_linear_5m_hm3=r.volume_max_hm3,
        volume_pchip_hm3=round(v_pchip, 1),
        diferenca_hm3=round(dif, 1) if np.isfinite(dif) else np.nan,
        diferenca_pct=round(100 * dif / r.volume_max_hm3, 2)
        if np.isfinite(dif) and r.volume_max_hm3 else np.nan,
        area_pchip_km2=round(a_pchip, 2),
        restricao=r.restricao, limitante=r.limitante))
cd = pd.DataFrame(chk)
print(cd.to_string(index=False))
fora = cd[~cd.dentro_do_intervalo]
if len(fora):
    print(f"\n  ATENCAO: {len(fora)} altura(s) fora do intervalo interpolado "
          f"(10 a 120 m) — nao ha' extrapolacao, o valor foi truncado.")
else:
    print("\n  todas as alturas admissiveis caem dentro do intervalo interpolado")

# =============================================================================
# 4. TABELA FINAL CONSOLIDADA
# =============================================================================
# Volume util e volume de espera seguem os criterios SINV:
#   - deplecao maxima = 1/3 da queda bruta maxima (item 4.6.1)
#   - volume de espera adotado como fracao do volume maximo (parametro)
FRAC_ESPERA = 0.50
DEPLEC_MAX = 1 / 3

print("\n" + "=" * 112)
print(f"4. TABELA FINAL — volume util e de espera (espera = {FRAC_ESPERA:.0%} do maximo)")
print("=" * 112)

fin = []
for _, r in rev.iterrows():
    d = dens[dens.eixo == r.eixo].sort_values("altura_m")
    if not len(d) or not np.isfinite(r.altura_max_m) or r.altura_max_m <= 0:
        continue
    H = float(r.altura_max_m)
    f_v = lambda h: float(np.interp(h, d.altura_m, d.volume_hm3))
    f_a = lambda h: float(np.interp(h, d.altura_m, d.area_alagada_km2))

    V_max = f_v(H)
    V_esp = V_max * FRAC_ESPERA
    V_mxn = V_max - V_esp                                   # NA maximo normal
    h_mxn = float(np.interp(V_mxn, d.volume_hm3, d.altura_m))
    # deplecao maxima limitada a 1/3 da queda bruta
    d_max = DEPLEC_MAX * h_mxn
    h_min = max(h_mxn - d_max, float(d.altura_m.min()))
    V_util = max(V_mxn - f_v(h_min), 0.0)

    fin.append(dict(
        eixo=r.eixo,
        altura_m=round(H, 1),
        cota_eixo_m=r.cota_eixo_m,
        cota_NA_maximorum_m=round(r.cota_eixo_m + H, 1),
        cota_NA_normal_m=round(r.cota_eixo_m + h_mxn, 1),
        cota_NA_minimo_m=round(r.cota_eixo_m + h_min, 1),
        area_inundada_km2=round(f_a(H), 2),
        volume_acumulado_hm3=round(V_max, 1),
        volume_util_hm3=round(V_util, 1),
        volume_espera_hm3=round(V_esp, 1),
        restricao_montante=r.restricao,
        limitante=r.limitante,
        confiabilidade="B — CAV do MDE natural, eixo sem reservatorio",
        metodo_curva="PCHIP monotonica em passos de 1 m"))

ft = pd.DataFrame(fin).sort_values("volume_acumulado_hm3", ascending=False)
ft.to_csv(os.path.join(D_OUT, "claude_cav_eixos_consolidada.csv"),
          index=False, sep=";", decimal=",")
print(ft[["eixo", "altura_m", "cota_NA_normal_m", "cota_NA_maximorum_m",
          "area_inundada_km2", "volume_acumulado_hm3", "volume_util_hm3",
          "volume_espera_hm3", "restricao_montante", "confiabilidade"]].to_string(index=False))

print(f"\n  volume acumulado total nas alturas admissiveis: "
      f"{ft.volume_acumulado_hm3.sum():,.0f} hm3")
print(f"  volume de espera correspondente: {ft.volume_espera_hm3.sum():,.0f} hm3")
log("FIM")
