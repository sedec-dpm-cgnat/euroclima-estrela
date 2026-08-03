# -*- coding: utf-8 -*-
"""
Inventário da topologia de eixos para roteamento conjunto com comportas.

O arquivo EUROCLIMA-rev.kmz já foi processado por 10_eixos_cascata.py e os
12 eixos foram convertidos em E01--E12. Este script não simula ainda a
hidráulica: transforma a relação de bacias aninhadas em uma rede de conexões
imediatas e registra os arranjos que devem entrar no roteamento em cascata.

Esta é uma rede geomorfológica de triagem. A conexão hidráulica final, os
tempos de viagem, os trechos entre barragens e a operação coordenada devem ser
conferidos no HEC-RAS 1D e em dados de campo.
"""

from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
D_CAV = ROOT / "01_dados" / "cav"
D_RES = ROOT / "06_resultados"
D_TAB = D_RES / "tabelas"
D_TAB.mkdir(parents=True, exist_ok=True)


def read_csv(name: str) -> pd.DataFrame:
    return pd.read_csv(D_CAV / name, sep=";", decimal=",")


topo = read_csv("topologia_eixos.csv")
eixos = read_csv("eixos_todos.csv")
area = eixos.set_index("codigo")["area_km2"].to_dict()
cota = eixos.set_index("codigo")["cota_eixo_m"].to_dict()

# Para cada eixo de montante, escolhe-se o menor eixo que contém sua bacia.
# Relações adicionais continuam no arquivo original de topologia.
imediatas = []
for montante in sorted(topo["montante"].unique()):
    candidatos = topo[topo["montante"].eq(montante)].copy()
    candidatos["area_jusante_km2"] = candidatos["eixo"].map(area)
    candidatos = candidatos.sort_values(["area_jusante_km2", "eixo"])
    if candidatos.empty:
        continue
    r = candidatos.iloc[0]
    jusante = r["eixo"]
    imediatas.append(
        {
            "montante": montante,
            "jusante_imediato": jusante,
            "area_montante_km2": area.get(montante),
            "area_jusante_km2": area.get(jusante),
            "area_incremental_entre_eixos_km2": area.get(jusante, 0)
            - area.get(montante, 0),
            "cota_montante_m": cota.get(montante),
            "cota_jusante_m": cota.get(jusante),
            "observacao": "conexão imediata derivada da topologia D8/BHO",
        }
    )

rede = pd.DataFrame(imediatas).sort_values(["jusante_imediato", "montante"])
rede.to_csv(
    D_TAB / "rede_imediata_cascatas_comportas.csv",
    sep=";",
    decimal=",",
    index=False,
)

jusantes = set(rede["jusante_imediato"])
raizes = sorted(set(eixos["codigo"]) - jusantes)
adj = {}
for _, r in rede.iterrows():
    adj.setdefault(r["montante"], []).append(r["jusante_imediato"])


def caminhos(no, caminho):
    proximos = adj.get(no, [])
    if not proximos:
        return [caminho]
    saida = []
    for prox in proximos:
        if prox in caminho:
            saida.append(caminho + [f"{prox}(ciclo?)"])
        else:
            saida.extend(caminhos(prox, caminho + [prox]))
    return saida


caminhos_rede = []
for raiz in raizes:
    caminhos_rede.extend(caminhos(raiz, [raiz]))

candidatas = [
    {
        "id": "C01",
        "nome": "prioritarios",
        "eixos": "E02+E04",
        "tipo": "ramos_convergentes",
        "objetivo": "testar a operação coordenada dos dois eixos prioritários",
        "status": "primeiro cenário conjunto",
    },
    {
        "id": "C02",
        "nome": "prioritarios_com_cobertura",
        "eixos": "E02+E04+E12",
        "tipo": "ramos_convergentes_com_eixo_jusante",
        "objetivo": "testar o ganho de cobertura com E12, condicionado à 14 de Julho",
        "status": "cenário de cobertura",
    },
    {
        "id": "C03",
        "nome": "intermediaria",
        "eixos": "E02+E04+E08",
        "tipo": "ramos_convergentes_com_eixo_intermediario",
        "objetivo": "testar cobertura intermediária sem incluir toda a cascata inferior",
        "status": "cenário intermediário; E08 condicionado a Castro Alves",
    },
    {
        "id": "C04",
        "nome": "cascata_antas",
        "eixos": "E09+E10+E11+E12",
        "tipo": "serie_principal",
        "objetivo": "testar barragens com comportas em série e a interação com a cascata existente",
        "status": "cenário crítico; E09/E10/E11/E12 condicionados",
    },
    {
        "id": "C05",
        "nome": "cascata_ramificada_completa",
        "eixos": "E01+E02+E04+E08+E09+E10+E11+E12",
        "tipo": "rede_ramificada",
        "objetivo": "avaliar a coordenação de ramos e reservatórios em série",
        "status": "sensibilidade; depende de validar todos os eixos",
    },
]

pd.DataFrame(candidatas).to_csv(
    D_TAB / "cascatas_candidatas_comportas.csv",
    sep=";",
    decimal=",",
    index=False,
)

linhas = [
    "# Inventário de cascatas para comportas",
    "",
    "**Fonte geométrica:** `Documentos EUROCLIMA+/Espanha/kmz/EUROCLIMA-rev.kmz`.",
    "O KMZ contém 12 geometrias lineares de eixos; o pipeline `10_eixos_cascata.py` as converteu em E01–E12 e gerou a relação de bacias aninhadas.",
    "",
    "## Como ler",
    "",
    "A rede abaixo é uma aproximação de conexão imediata: cada eixo de montante é ligado ao menor eixo jusante que contém sua bacia. Ela serve para ordenar o roteamento e evitar somar hidrogramas de forma independente. Não substitui a confirmação do talvegue, do trecho de rio, do tempo de viagem e do remanso.",
    "",
    "## Conexões imediatas",
    "",
    "| Montante | Jusante imediato | Área montante (km²) | Área jusante (km²) | Incremental entre eixos (km²) |",
    "|---|---|---:|---:|---:|",
]
for _, r in rede.sort_values(["montante", "jusante_imediato"]).iterrows():
    fmt = lambda x: f"{x:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")
    linhas.append(
        f"| {r.montante} | {r.jusante_imediato} | {fmt(r.area_montante_km2)} | {fmt(r.area_jusante_km2)} | {fmt(r.area_incremental_entre_eixos_km2)} |"
    )

linhas += ["", "## Caminhos geomorfológicos", ""]
for path in caminhos_rede:
    linhas.append("- " + " → ".join(path))

linhas += [
    "",
    "## Arranjos a simular",
    "",
    "| ID | Arranjo | Tipo | Finalidade | Situação |",
    "|---|---|---|---|---|",
]
for c in candidatas:
    linhas.append(
        f"| {c['id']} | {c['eixos']} | {c['tipo']} | {c['objetivo']} | {c['status']} |"
    )

linhas += [
    "",
    "## Regra de roteamento a implementar",
    "",
    "A cada passo de tempo, o reservatório recebe a vazão incremental de sua sub-bacia e as vazões efluentes dos reservatórios imediatamente a montante, após o tempo de viagem do trecho. A comporta deve ser modulada por uma regra coordenada, com limites de abertura, capacidade máxima de descarga, volume mínimo de segurança, nível máximo e condição de saturação. Quando um reservatório atingir o nível máximo, ele deixa de amortecer e a vazão de saída deve se aproximar da afluência, sem criar artificialmente vazão maior que a entrada.",
    "",
    "O resultado deve reportar, para cada reservatório e para Estrela: pico afluente, pico efluente, volume armazenado, nível máximo, abertura de comportas, saturação, galgamento, energia e perdas de queda. Os cenários devem incluir operação independente, operação coordenada, previsão com 24/48/72 h e falha ou atraso de acionamento.",
    "",
    "## Limitação",
    "",
    "A topologia foi derivada da grade D8/BHO e as CAVs dos eixos novos são de classe B, derivadas do MDE natural. O HEC-RAS 1D continua sendo necessário para confirmar remanso, níveis, seção de controle, pontes, confluências e tempos de propagação.",
]

(D_RES / "CASCATAS_COMPORTAS_METODOLOGIA.md").write_text(
    "\n".join(linhas) + "\n", encoding="utf-8"
)

print(f"Rede imediata: {len(rede)} conexões")
print(f"Raízes: {', '.join(raizes)}")
print(f"Caminhos: {len(caminhos_rede)}")
print(f"Saída: {D_RES / 'CASCATAS_COMPORTAS_METODOLOGIA.md'}")
