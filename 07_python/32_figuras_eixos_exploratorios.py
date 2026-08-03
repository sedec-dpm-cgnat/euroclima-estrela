# -*- coding: utf-8 -*-
"""Gera hidrogramas comparativos, pontos exploratórios e KMZ de conferência.

Os pontos são uma triagem geométrica baseada no perfil longitudinal. Não são
eixos de engenharia e não substituem reconhecimento de campo, batimetria,
geologia, licenciamento ou verificação de remanso.
"""
from __future__ import annotations

import html
import os
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
import xml.etree.ElementTree as ET

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import geopandas as gpd
from pyproj import Transformer
from shapely.geometry import LineString, Point

MODEL = Path(__file__).resolve().parents[1]
ROOT = Path(os.environ["EURO"]) if os.environ.get("EURO") else MODEL.parent
if os.environ.get("EURO"):
    MODEL = ROOT / "05_MODELAGEM"
RES = MODEL / "06_resultados"
TAB = RES / "tabelas"
FIG = RES / "figuras"
GIS = RES / "GIS"
FIG.mkdir(parents=True, exist_ok=True)
GIS.mkdir(parents=True, exist_ok=True)


def num(s):
    return pd.to_numeric(s.astype(str).str.replace(",", ".", regex=False), errors="coerce")


# ---------------------------------------------------------------------------
# 1. Hidrogramas: referência sem reservatório versus cascatas com comportas.
h = pd.read_csv(TAB / "hidrogramas_cascatas_comportas_triagem.csv", sep=";", decimal=",")
h["tempo_h"] = num(h["tempo_h"])
for c in ["Q_natural_Estrela_m3s", "Q_resultante_Estrela_m3s"]:
    h[c] = num(h[c])
h = h.sort_values(["cenario", "tempo_h"])
natural = h[h.cenario == h.cenario.iloc[0]].copy()

fig, axes = plt.subplots(2, 1, figsize=(13, 10), sharex=True, constrained_layout=True)
cores = {"C01": "#2c7fb8", "C02": "#d95f02", "C03": "#1b9e77", "C04": "#7570b3", "C05": "#e7298a"}
for ax, cenarios, titulo in zip(
    axes,
    [["C01", "C02", "C03"], ["C04", "C05"]],
    ["Ramos prioritários e cobertura com E12", "Cascata das Antas e rede ramificada"],
):
    ax.plot(natural.tempo_h, natural.Q_natural_Estrela_m3s, color="#222222", lw=2.4, label="sem barragem")
    for c in cenarios:
        sub = h[h.cenario == c]
        if len(sub):
            ax.plot(sub.tempo_h, sub.Q_resultante_Estrela_m3s, lw=2.0, color=cores[c], label=f"{c} — com comportas")
    ax.axhline(4000, color="#666666", ls="--", lw=1, alpha=.8, label="referência 4.000 m³/s" if ax is axes[0] else None)
    ax.set_title(titulo, loc="left", weight="bold")
    ax.set_ylabel("vazão em Estrela (m³/s)")
    ax.grid(color="#e5e5e5")
    ax.legend(ncol=2, fontsize=9)
axes[-1].set_xlabel("tempo (h)")
fig.suptitle("Hidrogramas sem barragem e com operação preliminar em cascata", fontsize=16, weight="bold")
fig.savefig(FIG / "14_hidrogramas_natural_vs_cascatas.png", dpi=180, bbox_inches="tight")
plt.close(fig)

c02 = h[h.cenario == "C02"]
fig, ax = plt.subplots(figsize=(13, 6.5), constrained_layout=True)
ax.plot(natural.tempo_h, natural.Q_natural_Estrela_m3s, color="#8c1d2c", lw=2.8, label="sem barragem")
if len(c02):
    ax.plot(c02.tempo_h, c02.Q_resultante_Estrela_m3s, color="#2166ac", lw=2.8, label="C02 — E02 + E04 + E12")
    ax.fill_between(c02.tempo_h, c02.Q_resultante_Estrela_m3s, natural.Q_natural_Estrela_m3s, color="#2166ac", alpha=.12)
ax.axhline(4000, color="#555555", ls="--", lw=1.2, label="referência 4.000 m³/s")
ax.set_title("C02 em comparação com o evento sem barragem", fontsize=16, weight="bold", loc="left")
ax.set_xlabel("tempo (h)"); ax.set_ylabel("vazão em Estrela (m³/s)")
ax.grid(color="#e5e5e5"); ax.legend()
fig.savefig(FIG / "15_hidrograma_natural_vs_C02.png", dpi=180, bbox_inches="tight")
plt.close(fig)

# Rodada calibrada C1-C4 do Claude: mantém a figura sintética anterior para
# rastreabilidade e produz uma figura separada com o evento recalibrado.
c4_file = RES / "CLAUDE" / "claude_c4_hidrogramas_calibrado.csv"
if c4_file.exists():
    c4h = pd.read_csv(c4_file, sep=";", decimal=",", encoding="utf-8-sig")
    for c in ["t_h", "Q_natural", "Q_com_alternativa"]:
        c4h[c] = num(c4h[c])
    c4h = c4h.sort_values("t_h")
    fig, ax = plt.subplots(figsize=(13, 6.5), constrained_layout=True)
    ax.plot(c4h.t_h, c4h.Q_natural, color="#8c1d2c", lw=2.8, label="evento calibrado sem barragem")
    ax.plot(c4h.t_h, c4h.Q_com_alternativa, color="#2166ac", lw=2.8,
            label="carteira completa — ALT-J, barragem seca")
    ax.fill_between(c4h.t_h, c4h.Q_com_alternativa, c4h.Q_natural,
                    color="#2166ac", alpha=.12)
    ax.axhline(4000, color="#555555", ls="--", lw=1.2, label="referência preliminar 4.000 m³/s")
    ax.set_title("Rodada calibrada C1–C4 — carteira completa versus evento natural", fontsize=16, weight="bold", loc="left")
    ax.set_xlabel("tempo (h)"); ax.set_ylabel("vazão em Estrela (m³/s)")
    ax.grid(color="#e5e5e5"); ax.legend()
    fig.savefig(FIG / "16_hidrograma_calibrado_ALTJ.png", dpi=190, bbox_inches="tight")
    plt.close(fig)

# ---------------------------------------------------------------------------
# 2. Pontos exploratórios: máximos locais de queda suavizada no perfil.
perfil = pd.read_csv(RES / "CLAUDE" / "claude_perfil_principal.csv", sep=";", decimal=",")
for c in ["dist_km", "cota_m", "x_utm", "y_utm"]:
    perfil[c] = pd.to_numeric(perfil[c], errors="coerce")
perfil = perfil.dropna(subset=["dist_km", "cota_m", "x_utm", "y_utm"]).sort_values("dist_km")
grid = np.arange(240.0, 381.0, 0.25)
z_raw = np.interp(grid, perfil.dist_km, perfil.cota_m)
z_smooth = pd.Series(z_raw).rolling(21, center=True, min_periods=1).median().to_numpy()

# CA2, 14J2 e EST1 são pontos de triagem derivados do perfil. MC2 usa a
# geometria real anexada pelo usuário, quando o arquivo estiver disponível.
mc2_file = ROOT / "Documentos EUROCLIMA+" / "Espanha" / "kmz" / "EIXO-MONTECLARO2.kmz"
mc2_coords = None
mc2_xy = None
mc2_dist = 275.0
if mc2_file.exists():
    with ZipFile(mc2_file) as z:
        kml_name = next(n for n in z.namelist() if n.lower().endswith(".kml"))
        kroot = ET.fromstring(z.read(kml_name))
    kns = {"k": "http://www.opengis.net/kml/2.2"}
    kpm = kroot.find(".//k:Placemark", kns)
    raw = (kpm.findtext(".//k:coordinates", default="", namespaces=kns) if kpm is not None else "")
    mc2_coords = [tuple(map(float, q.split(",")[:2])) for q in raw.split()]
    if len(mc2_coords) >= 2:
        mc2_line = gpd.GeoSeries([LineString(mc2_coords)], crs=4326).to_crs(31982).iloc[0]
        mc2_mid = mc2_line.interpolate(0.5, normalized=True)
        mc2_xy = (float(mc2_mid.x), float(mc2_mid.y))
        dmid = ((perfil[["x_utm", "y_utm"]].to_numpy() - np.array(mc2_xy)) ** 2).sum(axis=1)
        mc2_dist = float(perfil.iloc[int(dmid.argmin())].dist_km)

sites = [
    dict(codigo="CA2-PROPOSTO", nome="Castro Alves 2", dist=255.0,
         classe="queda concentrada / energia e cheias",
         criterio="remanescente de queda a jusante de Castro Alves; validar conflito hidráulico"),
    dict(codigo="MC2-PROPOSTO", nome="Monte Claro 2", dist=mc2_dist, custom_xy=mc2_xy,
         classe="exploratório / energia e cheias",
         criterio="geometria fornecida pelo usuário; validar CAV, remanso, energia e interferência com a cascata"),
    dict(codigo="14J2-PROPOSTO", nome="14 de Julho 2", dist=330.25,
         classe="queda concentrada / controle de cheias",
         criterio="máximo local de queda no trecho a jusante de 14 de Julho; verificar remanso e sedimentos"),
    dict(codigo="EST1-PROPOSTO", nome="Estrela Norte", dist=360.0,
         classe="controle de cheias / baixa energia",
         criterio="ponto próximo ao trecho de interesse; queda pequena, potencialmente útil apenas para controle"),
]

to_ll = Transformer.from_crs(31982, 4674, always_xy=True)
to_utm = Transformer.from_crs(4674, 31982, always_xy=True)
usinas = pd.read_csv(TAB / "aproveitamentos_existentes.csv", sep=";", decimal=",")
usinas["pot_MW"] = num(usinas["potencia_kW"]) / 1000
usinas = usinas[(usinas.situacao == "operacao") & (usinas.pot_MW >= 15)].copy()
ux, uy = to_utm.transform(usinas.lon.to_numpy(), usinas.lat.to_numpy())
u_xy = np.c_[ux, uy]

rows = []
for s in sites:
    if s.get("custom_xy") is not None:
        xutm, yutm = map(float, s["custom_xy"])
    else:
        xutm = float(np.interp(s["dist"], perfil.dist_km, perfil.x_utm))
        yutm = float(np.interp(s["dist"], perfil.dist_km, perfil.y_utm))
    lon, lat = to_ll.transform(xutm, yutm)
    cota = float(np.interp(s["dist"], grid, z_smooth))
    zmont = float(np.interp(s["dist"] - 5, grid, z_smooth))
    zjus = float(np.interp(s["dist"] + 5, grid, z_smooth))
    head10 = zmont - zjus
    du = np.sqrt((u_xy[:, 0] - xutm) ** 2 + (u_xy[:, 1] - yutm) ** 2)
    j = int(np.argmin(du))
    rows.append({
        "codigo": s["codigo"], "nome": s["nome"], "classe": s["classe"],
        "dist_perfil_km": round(s["dist"], 2), "lat": round(lat, 7), "lon": round(lon, 7),
        "x_utm": round(xutm, 1), "y_utm": round(yutm, 1), "cota_perfil_suavizada_m": round(cota, 1),
        "queda_10km_m": round(head10, 1), "declividade_media_m_por_km": round(head10 / 10, 2),
        "usina_proxima": usinas.iloc[j]["nome"], "dist_usina_m": round(float(du[j]), 1),
        "criterio": s["criterio"],
        "fonte_geometria": "EIXO-MONTECLARO2.kmz (ponto médio da linha)" if s["codigo"] == "MC2-PROPOSTO" and mc2_coords else "perfil longitudinal (ponto de triagem)",
        "status": "ponto exploratório — não é eixo selecionado",
    })
out = pd.DataFrame(rows)

# Eixos de tributário no Forqueta: entram na base de pontos exploratórios, mas
# não são projetados na estaca do perfil principal, pois pertencem a outro
# curso d'água. A CAV vem da rodada isolada `cav_forqueta`.
fq_file = MODEL / "01_dados" / "cav_forqueta" / "eixos_todos.csv"
if fq_file.exists():
    fq = pd.read_csv(fq_file, sep=";", decimal=",", encoding="utf-8-sig")
    fq_rows = []
    for _, r in fq.iterrows():
        rot = str(r.get("rotulo_kmz", r.get("eixo", "")))
        if "FQ1" not in rot and "FQ2" not in rot:
            continue
        codigo = "FQ1-PROPOSTO" if "FQ1" in rot else "FQ2-PROPOSTO"
        lon, lat = float(r["lon"]), float(r["lat"])
        xutm, yutm = to_utm.transform(lon, lat)
        du = np.sqrt((u_xy[:, 0] - xutm) ** 2 + (u_xy[:, 1] - yutm) ** 2)
        j = int(np.argmin(du))
        fq_rows.append({
            "codigo": codigo,
            "nome": "Forqueta inferior" if codigo.startswith("FQ1") else "Forqueta intermediário",
            "classe": "controle de cheias / retenção de tributário",
            "dist_perfil_km": np.nan,
            "lat": round(float(lat), 7), "lon": round(float(lon), 7),
            "x_utm": round(xutm, 1), "y_utm": round(yutm, 1),
            "cota_perfil_suavizada_m": round(float(r["cota_eixo_m"]), 1),
            "queda_10km_m": np.nan, "declividade_media_m_por_km": np.nan,
            "usina_proxima": usinas.iloc[j]["nome"], "dist_usina_m": round(float(du[j]), 1),
            "criterio": f"BHO: {float(r['area_km2']):.1f} km² a montante; testar retenção e defasagem do Forqueta",
            "fonte_geometria": "BHO Drenagem_Bacia_Taquari; eixo normal ao talvegue",
            "status": "candidato tributário — não é eixo selecionado",
        })
    if fq_rows:
        out = pd.concat([out, pd.DataFrame(fq_rows)], ignore_index=True)
out.to_csv(TAB / "eixos_exploratorios_propostos.csv", sep=";", decimal=",", index=False, encoding="utf-8-sig")
gdf = gpd.GeoDataFrame(out.copy(), geometry=[Point(x, y) for x, y in zip(out.lon, out.lat)], crs=4674)
gdf.to_file(GIS / "eixos_exploratorios_propostos.gpkg", layer="pontos_exploratorios", driver="GPKG")
shpdir = GIS / "SHP"
shpdir.mkdir(parents=True, exist_ok=True)
gdf.to_file(shpdir / "eixos_exploratorios_propostos.shp", driver="ESRI Shapefile", encoding="UTF-8")

# KMZ de conferência. As usinas principais são incluídas para orientação.
styles = """
<Style id="exploratorio"><IconStyle><scale>1.25</scale><Icon><href>http://maps.google.com/mapfiles/kml/pushpin/red-pushpin.png</href></Icon></IconStyle></Style>
<Style id="usina"><IconStyle><scale>1.1</scale><Icon><href>http://maps.google.com/mapfiles/kml/pushpin/ylw-pushpin.png</href></Icon></IconStyle></Style>
<Style id="eixo_mc2"><LineStyle><color>ff00a5ff</color><width>5</width></LineStyle></Style>
"""
def placemark(name, lon, lat, style, description):
    return f"""<Placemark><name>{html.escape(str(name))}</name><styleUrl>#{style}</styleUrl><description><![CDATA[{description}]]></description><Point><coordinates>{lon:.7f},{lat:.7f},0</coordinates></Point></Placemark>"""

parts = ["<?xml version=\"1.0\" encoding=\"UTF-8\"?><kml xmlns=\"http://www.opengis.net/kml/2.2\"><Document><name>EUROCLIMA — pontos exploratórios</name>", styles, "<Folder><name>Pontos exploratórios derivados do perfil</name>"]
for _, r in out.dropna(subset=["dist_perfil_km"]).iterrows():
    desc = "<b>Triagem de perfil</b><br/>" + "<br/>".join(f"{html.escape(str(k))}: {html.escape(str(v))}" for k, v in r.items())
    parts.append(placemark(r["codigo"] + " — " + r["nome"], float(r.lon), float(r.lat), "exploratorio", desc))
parts.append("</Folder><Folder><name>Usinas existentes de referência</name>")
for _, r in usinas[usinas.nome.str.contains("Castro Alves|Monte Claro|14 de Julho", case=False, na=False)].iterrows():
    parts.append(placemark(r["nome"], float(r.lon), float(r.lat), "usina", f"Potência: {r.pot_MW:.1f} MW"))
parts.append("</Folder>")
if mc2_coords and len(mc2_coords) >= 2:
    coord_text = " ".join(f"{lon:.7f},{lat:.7f},0" for lon, lat in mc2_coords)
    parts.append(f"<Folder><name>Geometria recebida do usuário</name><Placemark><name>EIXO-MONTECLARO2 — geometria original</name><styleUrl>#eixo_mc2</styleUrl><description><![CDATA[Geometria original do arquivo EIXO-MONTECLARO2.kmz. A linha deve ser confirmada no QGIS/Google Earth antes de entrar no pipeline oficial.]]></description><LineString><tessellate>1</tessellate><coordinates>{coord_text}</coordinates></LineString></Placemark></Folder>")
parts.append("</Document></kml>")
kml = "".join(parts)
(GIS / "eixos_exploratorios_propostos.kml").write_text(kml, encoding="utf-8")
with ZipFile(GIS / "eixos_exploratorios_propostos.kmz", "w", ZIP_DEFLATED) as z:
    z.writestr("doc.kml", kml.encode("utf-8"))

# Figura longitudinal para leitura no relatório.
fig, ax = plt.subplots(figsize=(16, 8), constrained_layout=True)
mask = (grid >= 230) & (grid <= 380)
ax.plot(grid[mask], z_raw[mask], color="#b59b78", lw=.8, alpha=.45, label="MDE/profile bruto")
ax.plot(grid[mask], z_smooth[mask], color="#4a3522", lw=2.3, label="perfil suavizado")
for _, r in out.dropna(subset=["dist_perfil_km"]).iterrows():
    ax.scatter(r.dist_perfil_km, r.cota_perfil_suavizada_m, s=85, color="#c0392b", zorder=5)
    ax.annotate(r.codigo.replace("-PROPOSTO", ""), (r.dist_perfil_km, r.cota_perfil_suavizada_m),
                xytext=(0, 12), textcoords="offset points", ha="center", weight="bold", color="#9d2739")
# Recalcula posições das usinas diretamente pelo perfil para marcar o desenho.
for _, r in usinas[usinas.nome.str.contains("Castro Alves|Monte Claro|14 de Julho", case=False, na=False)].iterrows():
    x0, y0 = to_utm.transform(float(r.lon), float(r.lat))
    j = int(np.argmin((perfil.x_utm.to_numpy()-x0)**2 + (perfil.y_utm.to_numpy()-y0)**2))
    ax.scatter(perfil.iloc[j].dist_km, perfil.iloc[j].cota_m, marker="s", s=65, color="#2166ac", zorder=5)
    ax.annotate(r.nome, (perfil.iloc[j].dist_km, perfil.iloc[j].cota_m), xytext=(0, -16), textcoords="offset points", ha="center", fontsize=9, color="#2166ac")
ax.set_xlim(230, 380); ax.set_xlabel("distância ao longo do perfil (km), montante → jusante")
ax.set_ylabel("cota do talvegue/profile (m)")
ax.set_title("Perfil longitudinal e pontos exploratórios para conferência", fontsize=16, weight="bold", loc="left")
ax.grid(axis="y", color="#e5e5e5"); ax.legend()
fig.savefig(RES / "VALIDACAO" / "PERFIL_EIXOS_EXPLORATORIOS.png", dpi=190, bbox_inches="tight")
plt.close(fig)

# Figura específica do tributário, pois suas estacas não pertencem ao perfil
# longitudinal do rio das Antas/Taquari.
fq_rede = GIS / "forqueta_rede_principal.gpkg"
fq_axes = GIS / "eixos_forqueta_propostos.gpkg"
if fq_rede.exists() and fq_axes.exists():
    rede_g = gpd.read_file(fq_rede, layer="forqueta_principal").to_crs(4326)
    axes_g = gpd.read_file(fq_axes, layer="eixos_forqueta").to_crs(4326)
    fig, ax = plt.subplots(figsize=(10, 8), constrained_layout=True)
    rede_g.plot(ax=ax, color="#5087a8", linewidth=0.8, alpha=0.75, label="rede BHO do Forqueta")
    axes_g.plot(ax=ax, color="#d7301f", linewidth=2.5, label="eixos de triagem")
    for _, r in axes_g.iterrows():
        p = r.geometry.interpolate(0.5, normalized=True)
        ax.scatter(p.x, p.y, s=35, color="#111111", zorder=5)
        # O índice da camada preserva a ordem FQ1/FQ2 gerada pelo script 35.
        label = "FQ1" if _ == 0 else "FQ2"
        ax.annotate(label, (p.x, p.y), xytext=(5, 5), textcoords="offset points", weight="bold")
    ax.set_title("Eixos exploratórios de retenção no rio Forqueta", fontsize=15, weight="bold", loc="left")
    ax.set_xlabel("longitude"); ax.set_ylabel("latitude")
    ax.grid(color="#e5e5e5"); ax.legend(loc="best")
    fig.savefig(RES / "VALIDACAO" / "MAPA_EIXOS_FORQUETA.png", dpi=190, bbox_inches="tight")
    plt.close(fig)

# ---------------------------------------------------------------------------
# 3. Desenho comparativo das alternativas no perfil.
eix = pd.read_csv(MODEL / "01_dados" / "cav" / "eixos_todos.csv", sep=";", decimal=",")
rev = pd.read_csv(RES / "CLAUDE" / "claude_altura_admissivel_revisada.csv", sep=";", decimal=",")
for c in ["lat", "lon"]:
    eix[c] = pd.to_numeric(eix[c], errors="coerce")
for c in ["altura_max_m", "cota_eixo_m"]:
    rev[c] = pd.to_numeric(rev[c], errors="coerce")
ex, ey = to_utm.transform(eix.lon.to_numpy(), eix.lat.to_numpy())
pos = []
for x0, y0 in zip(ex, ey):
    j = int(np.argmin((perfil.x_utm.to_numpy()-x0)**2 + (perfil.y_utm.to_numpy()-y0)**2))
    pos.append((perfil.iloc[j].dist_km, perfil.iloc[j].cota_m))
eix["dist_km"], eix["talveg_m"] = zip(*pos)
eix = eix.merge(rev[["eixo", "altura_max_m"]], left_on="codigo", right_on="eixo", how="left")
eix["crista_m"] = eix["cota_eixo_m"] + eix["altura_max_m"] + 3
configs = [
    ("ALT-A — E02 + E04", ["E02", "E04"]),
    ("ALT-D — E02 + E04 + E08", ["E02", "E04", "E08"]),
    ("ALT-E/C02 — E02 + E04 + E12", ["E02", "E04", "E12"]),
    ("ALT-I — E02 + E04 + E01 + E05 + E08", ["E02", "E04", "E01", "E05", "E08"]),
    ("C04 — E09 + E10 + E11 + E12", ["E09", "E10", "E11", "E12"]),
    ("Exploratórios — CA2, MC2, 14J2, EST1", list(out.codigo)),
]
fig, axes = plt.subplots(2, 3, figsize=(19, 10), sharex=True, sharey=True, constrained_layout=True)
for ax, (titulo, selecionados) in zip(axes.ravel(), configs):
    ax.plot(grid, z_smooth, color="#5b4a34", lw=1.3)
    if titulo.startswith("Exploratórios"):
        for _, r in out.dropna(subset=["dist_perfil_km"]).iterrows():
            ax.scatter(r.dist_perfil_km, r.cota_perfil_suavizada_m, color="#c0392b", s=35, zorder=5)
            ax.annotate(r.codigo.replace("-PROPOSTO", ""), (r.dist_perfil_km, r.cota_perfil_suavizada_m), xytext=(0, 7), textcoords="offset points", ha="center", fontsize=7, color="#9d2739")
    else:
        sub = eix[eix.codigo.isin(selecionados)]
        for _, r in sub.iterrows():
            ax.plot([r.dist_km, r.dist_km], [r.talveg_m, r.crista_m], color="#238b45", lw=3.0)
            ax.scatter(r.dist_km, r.crista_m, color="#238b45", s=22, zorder=5)
            ax.annotate(r.codigo, (r.dist_km, r.crista_m), xytext=(0, 6), textcoords="offset points", ha="center", fontsize=7, color="#238b45", weight="bold")
    ax.set_title(titulo, fontsize=10, weight="bold", loc="left")
    ax.grid(axis="y", color="#eeeeee")
    ax.set_xlim(0, 380); ax.set_ylim(0, 820)
for ax in axes[-1]: ax.set_xlabel("distância no perfil (km)")
for ax in axes[:, 0]: ax.set_ylabel("cota (m)")
fig.suptitle("Divisão de quedas — alternativas e pontos exploratórios", fontsize=16, weight="bold")
fig.savefig(RES / "VALIDACAO" / "DIVISAO_QUEDAS_ALTERNATIVAS.png", dpi=180, bbox_inches="tight")
plt.close(fig)

# ---------------------------------------------------------------------------
# 4. Matriz explícita: quais barragens entram em cada alternativa/cenário.
# A figura de perfil mostra posição e altura; esta matriz evita que a leitura
# de uma linha sobreposta seja confundida com seleção de todos os eixos.
matrix_configs = [
    ("ALT-A", ["E02", "E04"], "alternativa"),
    ("ALT-B", ["E02", "E04", "E01"], "alternativa"),
    ("ALT-C", ["E02", "E04", "E05"], "alternativa"),
    ("ALT-D", ["E02", "E04", "E08"], "alternativa"),
    ("ALT-E", ["E02", "E04", "E12"], "alternativa"),
    ("ALT-F", ["E02"], "alternativa"),
    ("ALT-G", ["E04"], "alternativa"),
    ("ALT-H", ["E12"], "alternativa"),
    ("ALT-I", ["E02", "E04", "E01", "E05", "E08"], "alternativa"),
    ("C01", ["E02", "E04"], "comportas"),
    ("C02", ["E02", "E04", "E12"], "comportas"),
    ("C03", ["E02", "E04", "E08"], "comportas"),
    ("C04", ["E09", "E10", "E11", "E12"], "comportas"),
    ("C05", ["E01", "E02", "E04", "E08", "E09", "E10", "E11", "E12"], "comportas"),
]
volumes = {}
alt_file = RES / "CLAUDE" / "claude_alternativas_finais.csv"
if alt_file.exists():
    alt_df = pd.read_csv(alt_file, sep=";", decimal=",", encoding="utf-8-sig")
    for _, rr in alt_df.iterrows():
        code = str(rr["alternativa"]).split()[0]
        volumes[code] = float(rr["volume_espera_hm3"])
axes_codes = [f"E{i:02d}" for i in range(1, 13)]
row_labels = [
    f"{code} ({volumes[code]:.0f} hm³)" if code in volumes else code
    for code, _, _ in matrix_configs
]
fig, ax = plt.subplots(figsize=(16, 9), constrained_layout=True)
for i, (code, selected, kind) in enumerate(matrix_configs):
    color = "#238b45" if kind == "alternativa" else "#7950a4"
    for j, eje in enumerate(axes_codes):
        face = color if eje in selected else "#f1f3f5"
        edge = color if eje in selected else "#d8dde3"
        ax.add_patch(plt.Rectangle((j - 0.43, i - 0.37), 0.86, 0.74,
                                   facecolor=face, edgecolor=edge, linewidth=0.8))
        if eje in selected:
            ax.text(j, i, "●", ha="center", va="center", color="white", fontsize=13, weight="bold")
ax.set_xlim(-0.5, len(axes_codes) - 0.5)
ax.set_ylim(-0.5, len(matrix_configs) - 0.5)
ax.invert_yaxis()
ax.set_xticks(range(len(axes_codes)), axes_codes)
ax.set_yticks(range(len(row_labels)), row_labels)
ax.tick_params(axis="both", labelsize=9)
ax.set_xlabel("eixos de barragem considerados")
ax.set_title("Matriz de eixos por alternativa e cenário de comportas", fontsize=16, weight="bold", loc="left")
ax.text(0, -0.085, "verde: alternativas ALT-A–ALT-I; roxo: cenários C01–C05; volume entre parênteses = volume de espera nominal da rodada SINV", transform=ax.transAxes, fontsize=9, color="#555555")
ax.grid(False)
fig.savefig(RES / "VALIDACAO" / "MATRIZ_ALTERNATIVAS_EIXOS.png", dpi=190, bbox_inches="tight")
plt.close(fig)

# Matriz separada para não esconder os tributários numa figura com eixo apenas
# do canal principal.
fq_configs = [
    ("ALT-J", ["E01", "E02", "E04", "E05", "E08", "E12"], "carteira"),
    ("ALT-J + FQ1", ["E01", "E02", "E04", "E05", "E08", "E12", "FQ1"], "combinada"),
    ("ALT-J + FQ2", ["E01", "E02", "E04", "E05", "E08", "E12", "FQ2"], "combinada"),
    ("ALT-J + FQ1 + FQ2", ["E01", "E02", "E04", "E05", "E08", "E12", "FQ1", "FQ2"], "combinada"),
    ("FQ1 isolado", ["FQ1"], "tributário"),
    ("FQ2 isolado", ["FQ2"], "tributário"),
]
fq_codes = axes_codes + ["FQ1", "FQ2"]
fig, ax = plt.subplots(figsize=(16, 5.8), constrained_layout=True)
for i, (code, selected, kind) in enumerate(fq_configs):
    color = {"carteira": "#238b45", "combinada": "#d95f02", "tributário": "#277da1"}[kind]
    for j, eixo in enumerate(fq_codes):
        face = color if eixo in selected else "#f1f3f5"
        edge = color if eixo in selected else "#d8dde3"
        ax.add_patch(plt.Rectangle((j - 0.43, i - 0.37), 0.86, 0.74,
                                   facecolor=face, edgecolor=edge, linewidth=0.8))
        if eixo in selected:
            ax.text(j, i, "●", ha="center", va="center", color="white", fontsize=13, weight="bold")
ax.set_xlim(-0.5, len(fq_codes) - 0.5)
ax.set_ylim(-0.5, len(fq_configs) - 0.5)
ax.invert_yaxis()
ax.set_xticks(range(len(fq_codes)), fq_codes)
ax.set_yticks(range(len(fq_configs)), [x[0] for x in fq_configs])
ax.tick_params(axis="both", labelsize=9)
ax.set_xlabel("eixos do canal principal e do tributário")
ax.set_title("Cenários de integração do Forqueta à carteira ALT-J", fontsize=15, weight="bold", loc="left")
ax.text(0, -0.12, "verde: ALT-J; laranja: combinação com Forqueta; azul: eixo tributário isolado", transform=ax.transAxes, fontsize=9, color="#555555")
ax.grid(False)
fig.savefig(RES / "VALIDACAO" / "MATRIZ_ALTERNATIVAS_FORQUETA.png", dpi=190, bbox_inches="tight")
plt.close(fig)

print("Saídas:")
for p in [TAB / "eixos_exploratorios_propostos.csv", GIS / "eixos_exploratorios_propostos.kmz", GIS / "eixos_exploratorios_propostos.gpkg", RES / "VALIDACAO" / "PERFIL_EIXOS_EXPLORATORIOS.png", RES / "VALIDACAO" / "MAPA_EIXOS_FORQUETA.png", RES / "VALIDACAO" / "DIVISAO_QUEDAS_ALTERNATIVAS.png", RES / "VALIDACAO" / "MATRIZ_ALTERNATIVAS_EIXOS.png", RES / "VALIDACAO" / "MATRIZ_ALTERNATIVAS_FORQUETA.png", FIG / "14_hidrogramas_natural_vs_cascatas.png", FIG / "15_hidrograma_natural_vs_C02.png", FIG / "16_hidrograma_calibrado_ALTJ.png"]:
    print(" -", p)
