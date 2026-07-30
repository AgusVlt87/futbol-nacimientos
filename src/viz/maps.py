"""Fase 6 — Cartografía.

Los mapas son el centro del apartado visual, así que se cuidan tres cosas que
suelen arruinarlos:

* **Proyección.** Argentina tiene 3.700 km de norte a sur: en coordenadas
  geográficas crudas el país sale deformado y las áreas no son comparables. Los
  coropléticos van en una cónica igual-área (`viz.crs_equal_area`), que es la
  proyección honesta cuando lo que se compara es superficie.
* **Clasificación.** Los cortes se declaran en la leyenda con sus valores, no se
  esconden detrás de una barra continua.
* **Extensión.** Se excluyen del encuadre la Antártida y las Islas del
  Atlántico Sur: sin población relevante ni jugadores, solo comprimen el resto
  del país hasta hacerlo ilegible. Es una decisión de encuadre, no de datos.
"""

from __future__ import annotations

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import to_hex
from matplotlib.patches import Patch
from shapely import affinity

from src.clean.geo_units import collapse_caba
from src.common import get_logger, load_config, paths
from src.geo import read_shapefile_zip
from src.viz import style

log = get_logger("viz.maps")

# Fuera del encuadre continental (ver docstring).
FUERA_DE_ENCUADRE = {"94021", "94028"}


def departamentos(cfg) -> "gpd.GeoDataFrame":
    p = paths()
    g = read_shapefile_zip(p.raw / "ign" / "ign_departamento.zip")
    g = g[~g["IN1"].isin(FUERA_DE_ENCUADRE)].copy()
    g["dept_id"] = g["IN1"].map(collapse_caba)
    # Las 15 comunas de CABA se funden en una sola unidad, igual que en los datos.
    g = g.dissolve(by="dept_id", as_index=False)[["dept_id", "geometry"]]
    return g.to_crs(cfg["viz"]["crs_equal_area"])


def provincias(cfg) -> "gpd.GeoDataFrame":
    p = paths()
    g = read_shapefile_zip(p.raw / "ign" / "ign_provincia.zip")
    g = g[g["IN1"] != "94"].copy()  # se recorta Tierra del Fuego + Antártida del encuadre
    tdf = read_shapefile_zip(p.raw / "ign" / "ign_departamento.zip")
    tdf = tdf[tdf["IN1"].str.startswith("94") & ~tdf["IN1"].isin(FUERA_DE_ENCUADRE)]
    tdf = tdf.dissolve().assign(IN1="94", NAM="Tierra del Fuego")[["IN1", "NAM", "geometry"]]
    g = pd.concat([g[["IN1", "NAM", "geometry"]], tdf], ignore_index=True)
    return g.set_geometry("geometry").set_crs("EPSG:4326").to_crs(cfg["viz"]["crs_equal_area"]) \
            .rename(columns={"IN1": "prov_id", "NAM": "provincia"})


def _cortes_cuantiles(valores: pd.Series, k: int) -> np.ndarray:
    """Cortes por cuantiles, con el cero como clase propia.

    Muchos departamentos no produjeron ningún futbolista. Si el 0 entra al
    cálculo de cuantiles, varios cortes caen en 0, se colapsan y la escala se
    queda con la mitad de las clases. «Ninguno» además es una categoría con
    sentido propio, distinta de «pocos».
    """
    v = valores.dropna()
    positivos = v[v > 0]
    cortes = np.quantile(positivos, np.linspace(0, 1, k))
    return np.unique(np.concatenate([[0.0], cortes, [v.max()]]))


def _leyenda_clases(ax, cortes, cmap, titulo, formato="{:.0f}"):
    parches, etiquetas = [], []
    n = len(cortes) - 1
    for i in range(n):
        parches.append(Patch(facecolor=cmap((i + 0.5) / n), edgecolor="none"))
        etiquetas.append("ninguno" if cortes[i + 1] == 0 or i == 0 and cortes[1] == 0
                         else f"{formato.format(cortes[i])} – {formato.format(cortes[i + 1])}")
    parches.append(Patch(facecolor=style.SIN_DATO, edgecolor="none"))
    etiquetas.append("sin datos")
    # Abajo a la izquierda: es el hueco que deja el Atlántico y no tapa el país.
    leg = ax.legend(parches, etiquetas, title=titulo, loc="lower left",
                    bbox_to_anchor=(-0.02, 0.0), fontsize=7, title_fontsize=7,
                    handlelength=1.1, handleheight=1.1, labelspacing=0.35,
                    borderpad=0.6)
    leg.get_title().set_color(style.INK_2)
    for t in leg.get_texts():
        t.set_color(style.INK_2)


def _pintar(ax, gdf, columna, cortes, cmap):
    clases = np.clip(np.digitize(gdf[columna], cortes[1:-1]), 0, len(cortes) - 2)
    # Hex, no RGBA: geopandas explota las multipartes y una lista de tuplas
    # queda como array irregular.
    colores = [style.SIN_DATO if pd.isna(v) else to_hex(cmap((c + 0.5) / (len(cortes) - 1)))
               for v, c in zip(gdf[columna], clases)]
    gdf.plot(ax=ax, color=colores, edgecolor=style.SURFACE, linewidth=0.25)
    ax.set_axis_off()
    ax.set_aspect("equal")


def mapa_coropletico(gdf, columna, titulo, subtitulo, cortes, cmap, cfg,
                     formato="{:.0f}", leyenda="") -> plt.Figure:
    fig, ax = plt.subplots(figsize=(cfg["viz"]["figure_width_single"] * 1.35, 6.2))
    _pintar(ax, gdf, columna, cortes, cmap)
    _leyenda_clases(ax, cortes, cmap, leyenda, formato)
    style.titulo_y_bajada(ax, titulo, subtitulo, pad=8)
    return fig


def cartograma(gdf_prov, valores: pd.Series, cfg) -> plt.Figure:
    """Cartograma no contiguo: cada provincia se escala hasta que su área sea
    proporcional a los jugadores que produjo, manteniendo su forma y su lugar.

    Al lado del mapa real muestra de un vistazo cuánto se aparta la producción
    de la geografía: Santa Fe se agranda, la Patagonia casi desaparece.
    """
    g = gdf_prov.copy()
    g["valor"] = g["prov_id"].map(valores).fillna(0)
    g["area"] = g.geometry.area
    # factor tal que area_nueva / area_total_nueva == valor / valor_total
    objetivo = g["valor"] / g["valor"].sum() * g["area"].sum()
    g["factor"] = np.sqrt((objetivo / g["area"]).replace([np.inf, -np.inf], 0)).fillna(0)

    fig, axes = plt.subplots(1, 2, figsize=(cfg["viz"]["figure_width_double"], 5.6))
    for ax, modo in zip(axes, ["real", "cartograma"]):
        if modo == "real":
            g.plot(ax=ax, color="#dfe8f2", edgecolor=style.SURFACE, linewidth=0.4)
            ax.set_title("Territorio real", loc="left", pad=6)
        else:
            g.plot(ax=ax, color=style.SIN_DATO, edgecolor="none", linewidth=0)
            escaladas = g.copy()
            escaladas["geometry"] = [
                affinity.scale(geom, xfact=f, yfact=f, origin="centroid")
                for geom, f in zip(g.geometry, g["factor"])]
            escaladas.plot(ax=ax, color=style.PRIMARY, edgecolor=style.SURFACE,
                           linewidth=0.4, alpha=0.92)
            ax.set_title("Área proporcional a los futbolistas producidos", loc="left", pad=6)
        ax.set_axis_off()
        ax.set_aspect("equal")
        ax.set_xlim(*axes[0].get_xlim()) if modo == "cartograma" else None

    # etiquetas directas solo para las provincias que dominan el cartograma
    top = g.nlargest(4, "valor")
    for _, r in top.iterrows():
        c = r.geometry.centroid
        axes[1].annotate(f"{r['provincia']}\n{int(r['valor'])}", (c.x, c.y),
                         ha="center", va="center", fontsize=6.5, color="#ffffff",
                         weight="bold")
    return fig
