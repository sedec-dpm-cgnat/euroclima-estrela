# -*- coding: utf-8 -*-
"""
EUROCLIMA / Estrela-RS — INTERFERENCIA COMO CUSTO ENERGETICO, nao como veto.

MOTIVO
------
Ate aqui a interferencia de um eixo proposto sobre um aproveitamento existente
foi tratada como PROIBICAO: a altura admissivel era aquela que nao "afogava" a
usina de montante. Esse enquadramento e' binario demais e nao e' o que o
Manual de Inventario prescreve.

O item 4.6.1 diz que o nivel de agua normal a jusante (NAjn) de um
aproveitamento e' "o nivel de agua natural no local OU o NAmxn do reservatorio
imediatamente a jusante, SE ESTE FOR MAIS ELEVADO". Ou seja: quando um novo
reservatorio eleva o nivel no canal de fuga da usina de montante, o efeito nao
e' impedir a obra — e' REDUZIR A QUEDA daquela usina, e portanto a sua energia.
Isso e' um CUSTO, quantificavel, que deve entrar na comparacao de alternativas.

O veto so se justifica quando o remanso atinge a cota minima operacional da
usina de montante, aí sim comprometendo a operacao.

DADOS
-----
Curvas cota-area-volume OFICIAIS do SNIRH obtidas pela outra trilha
(`01_dados/cav_snirh/`), com cotas normal, maximorum e minima operacional, e
vazoes medias de longo termo (Qmlt) das tres usinas do rio das Antas.

Isso permite duas coisas que ate agora nao eram possiveis:
  (a) CALIBRAR a vazao especifica da bacia com dado oficial, substituindo o
      valor arbitrado de 0,020 m3/s/km2;
  (b) QUANTIFICAR a perda de energia da usina de montante em funcao da
      elevacao do seu canal de fuga.

Saidas (06_resultados/CLAUDE/):
  claude_vazao_especifica_calibrada.csv
  claude_interferencia_energetica.csv
  claude_balanco_energetico_liquido.csv
"""
import os, time, warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd

DEST = os.path.join(os.environ["EURO"], "05_MODELAGEM")
D_CAV = os.path.join(DEST, "01_dados", "cav")
D_SNIRH = os.path.join(DEST, "01_dados", "cav_snirh")
D_TAB = os.path.join(DEST, "06_resultados", "tabelas")
D_OUT = os.path.join(DEST, "06_resultados", "CLAUDE")
os.makedirs(D_OUT, exist_ok=True)

t0 = time.time()
def log(*a): print(f"[{time.time()-t0:6.1f}s]", *a, flush=True)

K_EF = 0.0088          # eq. 4.6.1.01
PERDA_CARGA = 0.02

# =============================================================================
# 1. CALIBRACAO DA VAZAO ESPECIFICA com dado oficial
# =============================================================================
fic = pd.read_csv(os.path.join(D_SNIRH, "cav_snirh_ficha_tecnica.csv"),
                  sep=";", decimal=",", encoding="utf-8-sig")
fic["q_espec"] = fic.qmlt_m3_s / fic.area_drenagem_km2

print("=" * 104)
print("1. CALIBRACAO DA VAZAO ESPECIFICA — dado oficial SNIRH")
print("=" * 104)
print(fic[["usina", "potencia_mw", "area_drenagem_km2", "qmlt_m3_s",
           "q_espec"]].to_string(index=False))

# regressao Qmlt = a * A^b  (relacao regional classica)
A = fic.area_drenagem_km2.values
Q = fic.qmlt_m3_s.values
b, la = np.polyfit(np.log(A), np.log(Q), 1)
a = np.exp(la)
q_esp_med = float(np.average(fic.q_espec, weights=fic.area_drenagem_km2))

print(f"\n  vazao especifica media ponderada por area: {q_esp_med:.4f} m3/s/km2")
print(f"  regressao potencial ajustada: Qmlt = {a:.4f} * A^{b:.3f}")
print(f"  ATENCAO: expoente {b:.2f} e' fisicamente implausivel (esperado 0,8 a 1,0).")
print("  Com apenas 3 pontos, todos entre 7.700 e 12.800 km2, a regressao NAO")
print("  suporta extrapolacao. Adota-se a VAZAO ESPECIFICA MEDIA como estimador.")
print(f"  valor ANTES arbitrado no SINV: 0,0200 m3/s/km2")
print(f"  -> a energia firme calculada estava SUBESTIMADA em {100*(q_esp_med/0.020-1):.0f}%")

cal = pd.DataFrame([dict(
    q_especifica_media_ponderada=round(q_esp_med, 5),
    coef_a=round(a, 5), expoente_b=round(b, 4),
    n_usinas=len(fic), fonte="SNIRH — fichas técnicas CAV",
    valor_anterior_arbitrado=0.020,
    fator_correcao=round(q_esp_med / 0.020, 3))])
cal.to_csv(os.path.join(D_OUT, "claude_vazao_especifica_calibrada.csv"),
           index=False, sep=";", decimal=",")

def qmlt(area_km2):
    """Vazao media de longo termo.

    Usa a vazao especifica media ponderada, e NAO a regressao potencial: com
    tres pontos concentrados entre 7.700 e 12.800 km2, o expoente ajustado
    (1,32) e' implausivel e extrapolaria mal para as areas menores (E01, E02,
    E03). O estimador simples e' mais defensavel nesta faixa.
    """
    return q_esp_med * area_km2

# =============================================================================
# 2. INTERFERENCIA: elevacao do canal de fuga e perda de energia
# =============================================================================
# Para cada usina existente com CAV oficial, a cota do CANAL DE FUGA e'
# aproximada pela base da curva CAV (leito no eixo do barramento). Um novo
# reservatorio a jusante que eleve o NA acima dessa cota reduz a queda bruta
# da usina de montante na mesma medida.
curvas = pd.read_csv(os.path.join(D_SNIRH, "curvas", "cav_snirh_consolidada.csv"),
                     sep=";", decimal=",", encoding="utf-8-sig")
base = curvas.groupby("usina").cota_sl_m.min().rename("cota_leito_m")
fic = fic.merge(base, on="usina", how="left")
fic["queda_bruta_atual_m"] = fic.cota_normal_sl_m - fic.cota_leito_m

print("\n" + "=" * 104)
print("2. QUEDA DAS USINAS EXISTENTES E COTA DO CANAL DE FUGA")
print("=" * 104)
print(fic[["usina", "cota_leito_m", "cota_normal_sl_m", "cota_maximorum_sl_m",
           "cota_minima_operacional_sl_m", "queda_bruta_atual_m",
           "qmlt_m3_s", "potencia_mw"]].to_string(index=False))

# energia firme atual aproximada de cada usina existente
# A eq. 4.6.1.01 usa a vazao do PERIODO CRITICO, nao a Qmlt. Aplicar a Qmlt
# direto produz energia firme ACIMA da potencia instalada, o que e' impossivel.
# Adota-se Qn(critico)/Qmlt = 0,55 e limita-se pela potencia instalada.
RAZAO_CRIT = 0.55
fic["Ef_atual_MWmed"] = np.minimum(
    K_EF * fic.queda_bruta_atual_m * (1 - PERDA_CARGA) * fic.qmlt_m3_s * RAZAO_CRIT,
    fic.potencia_mw)
print("\n  energia firme aproximada (eq. 4.6.1.01 com Qn do periodo critico,")
print("  limitada pela potencia instalada):")
for _, r in fic.iterrows():
    print(f"    {r.usina:<14} queda {r.queda_bruta_atual_m:>6.1f} m  "
          f"Qmlt {r.qmlt_m3_s:>6.1f} m3/s  ->  {r.Ef_atual_MWmed:>6.1f} MW medios "
          f"(potencia instalada {r.potencia_mw:.0f} MW)")

# =============================================================================
# 3. PERDA DE ENERGIA POR ELEVACAO DO CANAL DE FUGA
# =============================================================================
rev = pd.read_csv(os.path.join(D_OUT, "claude_altura_admissivel_revisada.csv"),
                  sep=";", decimal=",")
geo = pd.read_csv(os.path.join(D_CAV, "geometria_todos.csv"), sep=";", decimal=",")

# nome canonico da usina restritiva
def canon(s):
    s = str(s).lower()
    for k in ["14 de julho", "castro alves", "monte claro"]:
        if k in s: return k.title().replace("14 De Julho", "14 de Julho")
    return None

rev["usina_montante"] = rev.restricao.apply(canon)
alvo = rev[rev.usina_montante.notna()].copy()
log(f"{len(alvo)} eixos com usina de montante entre as tres com CAV oficial")

ALTURAS = [10, 20, 30, 40, 50, 60, 80, 100, 120]
regs = []
for _, e in alvo.iterrows():
    u = fic[fic.usina == e.usina_montante].iloc[0]
    sub = geo[geo.eixo == e.eixo].sort_values("altura_m")
    if not len(sub): continue
    for H in ALTURAS:
        NA_novo = e.cota_eixo_m + H
        # elevacao imposta ao canal de fuga da usina de montante
        dh = max(NA_novo - u.cota_leito_m, 0.0)
        # a queda so pode ser reduzida ate zero
        dh_efetivo = min(dh, u.queda_bruta_atual_m)
        perda = (K_EF * dh_efetivo * (1 - PERDA_CARGA)
                 * u.qmlt_m3_s * RAZAO_CRIT)                      # MW medios
        # veto: remanso atinge a cota minima operacional
        veto = NA_novo >= u.cota_minima_operacional_sl_m
        vol = float(np.interp(H, sub.altura_m, sub.volume_hm3))
        regs.append(dict(
            eixo=e.eixo, altura_m=H, cota_eixo_m=e.cota_eixo_m,
            NA_novo_m=round(NA_novo, 1), usina_montante=e.usina_montante,
            cota_leito_montante_m=round(u.cota_leito_m, 1),
            cota_min_operacional_m=round(u.cota_minima_operacional_sl_m, 1),
            elevacao_canal_fuga_m=round(dh_efetivo, 1),
            perda_Ef_montante_MWmed=round(perda, 2),
            perda_pct_da_usina=round(100 * perda / u.Ef_atual_MWmed, 1)
            if u.Ef_atual_MWmed > 0 else np.nan,
            volume_novo_hm3=round(vol, 1),
            VETO_atinge_min_operacional=bool(veto)))

itf = pd.DataFrame(regs)
itf.to_csv(os.path.join(D_OUT, "claude_interferencia_energetica.csv"),
           index=False, sep=";", decimal=",")

pd.set_option("display.width", 220)
print("\n" + "=" * 118)
print("3. INTERFERENCIA COMO CUSTO — elevacao do canal de fuga e perda de energia")
print("=" * 118)
print(itf.to_string(index=False))

# =============================================================================
# 4. BALANCO LIQUIDO — energia do novo eixo menos perda no de montante
# =============================================================================
FK = 0.55
bal = []
for _, r in itf.iterrows():
    sub = geo[geo.eixo == r.eixo].sort_values("altura_m")
    # queda do novo aproveitamento: NA novo menos o leito no proprio eixo
    Hl = (r.NA_novo_m - r.cota_eixo_m) * (1 - PERDA_CARGA)
    Q_novo = qmlt(float(rev[rev.eixo == r.eixo].area_km2.iloc[0])) * RAZAO_CRIT
    Ef_novo = K_EF * Hl * Q_novo
    liq = Ef_novo - r.perda_Ef_montante_MWmed
    bal.append(dict(
        eixo=r.eixo, altura_m=r.altura_m, usina_montante=r.usina_montante,
        Ef_novo_MWmed=round(Ef_novo, 1),
        perda_montante_MWmed=r.perda_Ef_montante_MWmed,
        Ef_liquido_MWmed=round(liq, 1),
        razao_perda_ganho=round(r.perda_Ef_montante_MWmed / Ef_novo, 3)
        if Ef_novo > 0 else np.nan,
        volume_hm3=r.volume_novo_hm3,
        VETO=r.VETO_atinge_min_operacional))
bd = pd.DataFrame(bal)
bd.to_csv(os.path.join(D_OUT, "claude_balanco_energetico_liquido.csv"),
          index=False, sep=";", decimal=",")

print("\n" + "=" * 118)
print("4. BALANCO LIQUIDO — ganho no novo eixo menos perda na usina de montante")
print("=" * 118)
print(bd.to_string(index=False))

print("\n" + "-" * 118)
print("LEITURA")
print("-" * 118)
neg = bd[bd.Ef_liquido_MWmed < 0]
if len(neg):
    print(f"  {len(neg)} combinacoes com balanco NEGATIVO — o eixo tira mais energia")
    print("  da usina de montante do que gera:")
    for _, r in neg.iterrows():
        print(f"    {r.eixo} a {r.altura_m:>3.0f} m: gera {r.Ef_novo_MWmed:.1f}, "
              f"tira {r.perda_montante_MWmed:.1f} -> liquido {r.Ef_liquido_MWmed:+.1f} MW medios")
else:
    print("  nenhuma combinacao com balanco negativo")

vet = bd[bd.VETO]
print(f"\n  {len(vet)} combinacoes com VETO (remanso atinge a cota minima")
print("  operacional da usina de montante — inviabiliza a operacao dela).")
log("FIM")
