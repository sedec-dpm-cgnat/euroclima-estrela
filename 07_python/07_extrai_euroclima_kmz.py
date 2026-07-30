# -*- coding: utf-8 -*-
"""Extrai todas as feicoes do EUROCLIMA.kmz para GeoPackage e inventaria."""
import os, re, zipfile, warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon, MultiPolygon

KMZ = os.environ["KMZ"]
DEST = os.path.join(os.environ["EURO"], "05_MODELAGEM", "01_dados", "gis_derivado")
os.makedirs(DEST, exist_ok=True)
UTM22 = 31982

z = zipfile.ZipFile(os.path.join(KMZ, "EUROCLIMA.kmz"))
kml = [n for n in z.namelist() if n.lower().endswith(".kml")][0]
txt = z.read(kml).decode("utf-8", "ignore")


def coords(bloco):
    m = re.search(r"<coordinates>(.*?)</coordinates>", bloco, re.S)
    if not m:
        return []
    out = []
    for tok in m.group(1).split():
        p = tok.split(",")
        if len(p) >= 2:
            out.append((float(p[0]), float(p[1])))
    return out


regs = []
for pm in re.findall(r"<Placemark>(.*?)</Placemark>", txt, re.S):
    n = re.search(r"<name>(.*?)</name>", pm, re.S)
    nome = n.group(1).strip() if n else None
    if "<Polygon>" in pm:
        anel = re.search(r"<outerBoundaryIs>(.*?)</outerBoundaryIs>", pm, re.S)
        c = coords(anel.group(1) if anel else pm)
        if len(c) >= 4:
            regs.append(dict(nome=nome, tipo="Polygon", geometry=Polygon(c)))
    elif "<LineString>" in pm:
        c = coords(pm)
        if len(c) >= 2:
            regs.append(dict(nome=nome, tipo="LineString", geometry=LineString(c)))
    elif "<Point>" in pm:
        c = coords(pm)
        if c:
            regs.append(dict(nome=nome, tipo="Point", geometry=Point(c[0])))

g = gpd.GeoDataFrame(regs, crs=4326)
gm = g.to_crs(UTM22)
g["area_km2"] = np.where(gm.geom_type == "Polygon", gm.area / 1e6, np.nan)
g["compr_km"] = np.where(gm.geom_type == "LineString", gm.length / 1e3, np.nan)

print("=" * 90)
print("FEICOES NOMEADAS")
print("=" * 90)
nm = g[g.nome.notna()].copy()
print(nm[["nome", "tipo", "area_km2", "compr_km"]].to_string(index=False))

anon = g[g.nome.isna() & (g.tipo == "Polygon")].copy()
print("\n" + "=" * 90)
print(f"POLIGONOS SEM NOME: {len(anon)}")
print("=" * 90)
am = anon.to_crs(UTM22)
print(f"  area total ............ {am.area.sum()/1e6:10.3f} km2")
print(f"  area media ............ {am.area.mean():10.1f} m2")
print(f"  area mediana .......... {am.area.median():10.1f} m2")
print(f"  area minima ........... {am.area.min():10.1f} m2")
print(f"  area maxima ........... {am.area.max():10.1f} m2")
print(f"  n. vertices medio ..... {np.mean([len(p.exterior.coords) for p in anon.geometry]):10.1f}")
b = anon.total_bounds
print(f"  extensao .............. {b[0]:.4f},{b[1]:.4f} -> {b[2]:.4f},{b[3]:.4f}")
cen = anon.geometry.centroid
print(f"  centroide medio ....... {cen.y.mean():.5f}, {cen.x.mean():.5f}")

# provavel natureza: edificacoes?
print("\n  -> areas compativeis com EDIFICACOES" if am.area.median() < 2000
      else "\n  -> areas grandes: talvez lotes/quadras/manchas")

for nome, sub in [("todas", g)]:
    sub.to_file(os.path.join(DEST, "euroclima_kmz.gpkg"), layer="feicoes", driver="GPKG")
nm.to_file(os.path.join(DEST, "euroclima_kmz.gpkg"), layer="nomeadas", driver="GPKG")
anon.to_file(os.path.join(DEST, "euroclima_kmz.gpkg"), layer="poligonos_sem_nome", driver="GPKG")
print(f"\ngravado: {os.path.join(DEST, 'euroclima_kmz.gpkg')}")
