"""Fase 6 — Cartografía.

Tres cuidados que suelen faltar en los mapas coropléticos:

* **Proyección.** Argentina mide 3.700 km de norte a sur; en coordenadas
  geográficas crudas las áreas no son comparables. Todo va en una cónica
  igual-área (`viz.crs_equal_area`).
* **Clasificación.** Los cortes se declaran con sus valores en la leyenda. El
  cero tiene clase propia: «ningún futbolista» no es lo mismo que «pocos», y
  si entra al cálculo de cuantiles colapsa la mitad de las clases.
* **Encuadre.** La Antártida y las Islas del Atlántico Sur quedan fuera: sin
  población relevante ni jugadores, solo comprimen el resto del país hasta
  hacerlo ilegible. Es una decisión de encuadre, no de datos.
"""

from __future__ import annotations

import geopandas as gpd
import numpy as np
import pandas as pd
from matplotlib.colors import to_hex
from matplotlib.patches import Patch

from src.clean.geo_units import collapse_caba
from src.common import get_logger, paths
from src.geo import read_shapefile_zip
from src.viz import style

log = get_logger("viz.maps")

FUERA_DE_ENCUADRE = {"94021", "94028"}
NOMBRE_CORTO = {
    "Ciudad Autónoma de Buenos Aires": "CABA",
    # 52 caracteres: sin abreviar se sale del margen en cualquier eje vertical.
    "Tierra del Fuego, Antártida e Islas del Atlántico Sur": "Tierra del Fuego",
}

# Wikidata guarda la razón social completa («Club Atlético San Lorenzo de
# Almagro»). En un eje vertical eso son 36 caracteres de los cuales los primeros
# 14 no distinguen nada: todos los clubes empiezan igual. Se recortan los
# prefijos institucionales, de más largo a más corto para que no se pisen.
PREFIJOS_CLUB = ("Asociación Atlética ", "Club Atlético ", "Club Social y Deportivo ",
                 "Club Deportivo ", "Club de Gimnasia y Esgrima ", "Club de Fútbol ",
                 "Club Sportivo ", "Asociación ", "Club ")
CLUB_ESPECIAL = {
    "Club de Gimnasia y Esgrima La Plata": "Gimnasia (La Plata)",
    "Club Estudiantes de La Plata": "Estudiantes (La Plata)",
    "Racing Club": "Racing",
}


def nombre_club(nombre: str) -> str:
    """Nombre de club en la forma en que lo diría un hincha."""
    if nombre in CLUB_ESPECIAL:
        return CLUB_ESPECIAL[nombre]
    for prefijo in PREFIJOS_CLUB:
        if nombre.startswith(prefijo):
            return nombre[len(prefijo):]
    return nombre


def departamentos(cfg) -> gpd.GeoDataFrame:
    p = paths()
    g = read_shapefile_zip(p.raw / "ign" / "ign_departamento.zip")
    g = g[~g["IN1"].isin(FUERA_DE_ENCUADRE)].copy()
    g["dept_id"] = g["IN1"].map(collapse_caba)
    # Las 15 comunas de CABA se funden en una unidad, igual que en los datos.
    g = g.dissolve(by="dept_id", as_index=False)[["dept_id", "geometry"]]
    return g.to_crs(cfg["viz"]["crs_equal_area"])


def provincias(cfg) -> gpd.GeoDataFrame:
    p = paths()
    g = read_shapefile_zip(p.raw / "ign" / "ign_provincia.zip")
    g = g[g["IN1"] != "94"].copy()
    tdf = read_shapefile_zip(p.raw / "ign" / "ign_departamento.zip")
    tdf = tdf[tdf["IN1"].str.startswith("94") & ~tdf["IN1"].isin(FUERA_DE_ENCUADRE)]
    tdf = tdf.dissolve().assign(IN1="94", NAM="Tierra del Fuego")[["IN1", "NAM", "geometry"]]
    g = pd.concat([g[["IN1", "NAM", "geometry"]], tdf], ignore_index=True)
    return (g.set_geometry("geometry").set_crs("EPSG:4326")
             .to_crs(cfg["viz"]["crs_equal_area"])
             .rename(columns={"IN1": "prov_id", "NAM": "provincia"}))


def cortes_cuantiles(valores: pd.Series, k: int) -> np.ndarray:
    """Cortes por cuantiles con el cero como clase propia."""
    v = pd.Series(valores).dropna()
    positivos = v[v > 0]
    if positivos.empty:
        return np.array([0.0, 1.0])
    cortes = np.quantile(positivos, np.linspace(0, 1, k))
    return np.unique(np.concatenate([[0.0], cortes, [v.max()]]))


def pintar(ax, gdf, columna, cortes, cmap, borde=style.SURFACE, lw=0.25):
    clases = np.clip(np.digitize(gdf[columna], cortes[1:-1]), 0, len(cortes) - 2)
    # Hex, no RGBA: geopandas explota las multipartes y una lista de tuplas
    # queda como array irregular.
    colores = [style.SIN_DATO if pd.isna(v) else to_hex(cmap((c + 0.5) / (len(cortes) - 1)))
               for v, c in zip(gdf[columna], clases)]
    gdf.plot(ax=ax, color=colores, edgecolor=borde, linewidth=lw)
    ax.set_axis_off()
    ax.set_aspect("equal")


def contorno_provincias(ax, cfg, lw=0.5, color="#ffffff"):
    """Límites provinciales encima del relleno departamental: dan referencia."""
    provincias(cfg).boundary.plot(ax=ax, color=color, linewidth=lw, zorder=5)


def leyenda_clases(ax, cortes, cmap, titulo, formato="{:.0f}", loc="lower left",
                   anchor=(-0.02, 0.02), sin_dato=True):
    parches, etiquetas = [], []
    n = len(cortes) - 1
    for i in range(n):
        parches.append(Patch(facecolor=to_hex(cmap((i + 0.5) / n)), edgecolor="none"))
        etiquetas.append("ninguno" if cortes[i + 1] == 0
                         else f"{formato.format(cortes[i])} – {formato.format(cortes[i + 1])}")
    if sin_dato:
        parches.append(Patch(facecolor=style.SIN_DATO, edgecolor="none"))
        etiquetas.append("sin datos")
    leg = ax.legend(parches, etiquetas, title=titulo, loc=loc, bbox_to_anchor=anchor,
                    fontsize=6.8, title_fontsize=6.8, handlelength=1.1,
                    handleheight=1.1, labelspacing=0.35, borderpad=0.5)
    leg.get_title().set_color(style.INK_2)
    leg._legend_box.align = "left"
    for t in leg.get_texts():
        t.set_color(style.INK_2)
    return leg


def etiquetar(ax, punto, texto, dx=0, dy=0, color=style.INK, guia=False, size=6.8):
    """Etiqueta sobre el mapa. Con guía cuando el polígono es demasiado chico."""
    kw = dict(fontsize=size, color=color, fontweight="bold", linespacing=1.2,
              zorder=8)
    if guia:
        ax.annotate(texto, (punto.x, punto.y), xytext=(dx, dy),
                    textcoords="offset points", ha="left", va="center",
                    arrowprops=dict(arrowstyle="-", lw=0.6, color=style.INK_2), **kw)
    else:
        ax.annotate(texto, (punto.x, punto.y), xytext=(dx, dy),
                    textcoords="offset points", ha="center", va="center", **kw)
