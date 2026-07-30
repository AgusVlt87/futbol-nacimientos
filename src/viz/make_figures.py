"""Fase 6 — Genera todas las figuras del paper en `outputs/figures/`.

Uso:
    python -m src.viz.make_figures
"""

from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.colors import to_hex
import numpy as np
import pandas as pd
import statsmodels.api as sm

from src.analysis.stats import poisson_rate_ci
from src.common import get_logger, load_config, paths
from src.viz import maps, style

log = get_logger("viz")

FUENTE_BASE = ("Fuente: Wikidata (snapshot 2026-07-30) e INDEC, Censo Nacional 2022. "
               "Elaboración propia.")


def _pie(fig, texto: str) -> None:
    """Nota al pie. Va bien por debajo del eje: con `bbox_inches='tight'` el
    recorte la incluye, pero si se pega al borde se monta sobre el rótulo del
    eje x."""
    fig.text(0.01, -0.06, texto, ha="left", va="top", fontsize=6.5, color=style.MUTED,
             wrap=True)


# --------------------------------------------------------------------------- #
# Mapas
# --------------------------------------------------------------------------- #
def fig_mapas_departamento(cfg, p):
    dep = pd.read_csv(p.tables / "h2_departamentos.csv", dtype={"unidad": str})
    g = maps.departamentos(cfg).merge(dep, left_on="dept_id", right_on="unidad", how="left")
    k = cfg["viz"]["n_classes"]

    cortes = maps._cortes_cuantiles(g["tasa"], k)
    fig = maps.mapa_coropletico(
        g, "tasa",
        "Dónde nacen los futbolistas argentinos, corregido por población",
        f"Futbolistas por cada 100.000 habitantes de la misma cohorte · "
        f"{int(dep['jugadores'].sum()):,} nacidos 1970–2000".replace(",", "."),
        cortes, style.SEQ, cfg, "{:.0f}", "por 100.000 hab.")
    _pie(fig, "Denominador: población de 22 a 52 años en cada departamento (Censo 2022), "
              "la cohorte que corresponde a los nacidos entre 1970 y 2000.\n" + FUENTE_BASE)
    style.guardar(fig, "fig01_mapa_departamentos_tasa", cfg, p.figures)

    cortes = maps._cortes_cuantiles(g[g["jugadores"] > 0]["jugadores"], k)
    fig = maps.mapa_coropletico(
        g, "jugadores",
        "Dónde nacen los futbolistas argentinos, en números absolutos",
        "Cantidad de futbolistas nacidos en cada departamento · cohortes 1970–2000",
        cortes, style.SEQ, cfg, "{:.0f}", "futbolistas")
    _pie(fig, "Este mapa dibuja sobre todo dónde vive la gente. El mapa corregido por "
              "población (Figura 1) es el que muestra el patrón real.\n" + FUENTE_BASE)
    style.guardar(fig, "fig02_mapa_departamentos_conteo", cfg, p.figures)
    log.info("mapas por departamento listos")


def fig_mapa_provincias(cfg, p):
    prov = pd.read_csv(p.tables / "h2_provincias.csv", dtype={"unidad": str})
    # El nombre de provincia se toma de la capa del IGN; se descarta el de la
    # tabla para no terminar con provincia_x / provincia_y.
    g = maps.provincias(cfg).merge(prov.drop(columns=["provincia"]),
                                   left_on="prov_id", right_on="unidad", how="left")

    fig, ax = plt.subplots(figsize=(cfg["viz"]["figure_width_single"] * 1.35, 6.2))
    norm = style.norma_divergente(g["obs_sobre_esp"].dropna(), centro=1.0)
    colores = [style.SIN_DATO if pd.isna(v) else to_hex(style.DIV(norm(v)))
               for v in g["obs_sobre_esp"]]
    g.plot(ax=ax, color=colores, edgecolor=style.SURFACE, linewidth=0.4)
    ax.set_axis_off()
    ax.set_aspect("equal")
    style.titulo_y_bajada(
        ax, "Cuánto se aparta cada provincia de lo esperado por su población",
        "Futbolistas observados ÷ esperados · 1,0 = exactamente lo esperado", pad=8)

    sm_ = plt.cm.ScalarMappable(cmap=style.DIV, norm=norm)
    cb = fig.colorbar(sm_, ax=ax, fraction=0.03, pad=0.01, aspect=26)
    cb.set_label("observado / esperado", color=style.INK_2, fontsize=7)
    cb.ax.tick_params(labelsize=7, color=style.MUTED, labelcolor=style.INK_2)
    cb.outline.set_visible(False)

    for _, r in g.nlargest(3, "obs_sobre_esp").iterrows():
        c = r.geometry.centroid
        ax.annotate(f"{r['provincia']}\n×{r['obs_sobre_esp']:.1f}", (c.x, c.y),
                    ha="center", va="center", fontsize=6.5, color="#ffffff", weight="bold")
    _pie(fig, "Azul: produce menos futbolistas de los que le tocarían por población. "
              "Rojo: produce más.\n" + FUENTE_BASE)
    style.guardar(fig, "fig03_mapa_provincias_obs_esp", cfg, p.figures)
    log.info("mapa por provincia listo")


def fig_cartograma(cfg, p):
    prov = pd.read_csv(p.tables / "h2_provincias.csv", dtype={"unidad": str})
    fig = maps.cartograma(maps.provincias(cfg),
                          prov.set_index("unidad")["jugadores"], cfg)
    fig.suptitle("La geografía del talento no es la geografía del territorio",
                 x=0.01, ha="left", fontsize=10, fontweight="bold", color=style.INK)
    _pie(fig, "Cartograma no contiguo: cada provincia conserva su forma y su posición, "
              "pero su área es proporcional a los futbolistas que produjo.\n" + FUENTE_BASE)
    style.guardar(fig, "fig06_cartograma_provincias", cfg, p.figures)
    log.info("cartograma listo")


# --------------------------------------------------------------------------- #
# Gráficos
# --------------------------------------------------------------------------- #
def _barras_con_ic(ax, etiquetas, tasas, lo, hi, color=style.PRIMARY):
    y = np.arange(len(etiquetas))
    ax.barh(y, tasas, height=0.45, color=color, zorder=3)
    ax.errorbar(tasas, y, xerr=[tasas - lo, hi - tasas], fmt="none",
                ecolor=style.INK_2, elinewidth=1.0, capsize=2.0, zorder=4)
    ax.set_yticks(y, etiquetas)
    ax.invert_yaxis()
    ax.xaxis.grid(True)
    ax.yaxis.grid(False)
    style.despine(ax, left=True)
    # La etiqueta va después del extremo del IC, no encima de la barra: si no,
    # el número se monta sobre el bigote y no se lee ninguno de los dos.
    margen = hi.max() * 0.03
    for yi, t, h in zip(y, tasas, hi):
        ax.text(h + margen, yi, f"{t:.1f}", va="center", ha="left",
                fontsize=7.5, color=style.INK)
    ax.set_xlim(0, hi.max() * 1.16)


def fig_tramos(cfg, p):
    t = pd.read_csv(p.tables / "h1_tramos_principal.csv")
    fig, ax = plt.subplots(figsize=(cfg["viz"]["figure_width_double"] * 0.72, 3.0))
    _barras_con_ic(ax, t["unidad"], t["tasa"].values, t["tasa_ic_lo"].values,
                   t["tasa_ic_hi"].values)
    ax.set_xlabel("Futbolistas por 100.000 habitantes de la cohorte")
    ax.set_ylabel("Tamaño de la ciudad de nacimiento")
    style.titulo_y_bajada(ax, "Cuanto más grande la ciudad, más futbolistas per cápita",
                          "Lo contrario de lo que predice la literatura internacional")
    _pie(fig, "Barras de error: IC 95% exacto de Poisson. La «ciudad» es el aglomerado "
              "urbano cuando la localidad forma parte de uno.\n" + FUENTE_BASE)
    style.guardar(fig, "fig04_tasa_por_tramo", cfg, p.figures)


def fig_regiones(cfg, p):
    t = pd.read_csv(p.tables / "h2_regiones.csv").sort_values("tasa", ascending=False)
    fig, ax = plt.subplots(figsize=(cfg["viz"]["figure_width_double"] * 0.72, 3.0))
    _barras_con_ic(ax, t["unidad"], t["tasa"].values, t["tasa_ic_lo"].values,
                   t["tasa_ic_hi"].values)
    ax.set_xlabel("Futbolistas por 100.000 habitantes de la cohorte")
    style.titulo_y_bajada(ax, "La región pampeana produce tres veces más que el NOA",
                          "Tasa per cápita por región, cohortes 1970–2000")
    _pie(fig, "AMBA = CABA + 24 partidos del Gran Buenos Aires. "
              "Barras de error: IC 95% exacto de Poisson.\n" + FUENTE_BASE)
    style.guardar(fig, "fig05_tasa_por_region", cfg, p.figures)


def fig_scatter_tamano(cfg, p):
    """Tamaño de ciudad vs tasa, con la curva del birthplace effect.

    Dos decisiones de lectura, ambas declaradas al pie:

    * El **ajuste y los deciles usan todas las ciudades**; el scatter muestra
      solo las de más de 5.000 habitantes de la cohorte. En un pueblo de 300, un
      único futbolista da una tasa de 333 por 100.000: esos puntos no son señal,
      son la resolución del cociente, y dibujan franjas diagonales (1/N, 2/N…)
      que no significan nada.
    * La tasa agregada por decil de tamaño, con su IC, es la serie que se lee.
      El scatter es contexto.
    """
    players = pd.read_parquet(p.processed / "analysis_players.parquet")
    ciudades = pd.read_parquet(p.processed / "denom_ciudad_unica.parquet")
    conteo = players.groupby("ciudad_id").size().rename("jugadores")
    d = ciudades.set_index("ciudad_id").join(conteo).fillna({"jugadores": 0})
    d = d[(d["pob_cohorte_ciudad"] > 0) & (d["pob_ciudad"] > 0)].copy()
    d["tasa"] = 1e5 * d["jugadores"] / d["pob_cohorte_ciudad"]

    fig, ax = plt.subplots(figsize=(cfg["viz"]["figure_width_double"] * 0.82, 3.6))

    legibles = d[(d["pob_cohorte_ciudad"] >= 5000) & (d["jugadores"] > 0)]
    ax.scatter(legibles["pob_ciudad"], legibles["tasa"],
               s=np.clip(legibles["pob_ciudad"] / 6000, 5, 70),
               color=style.PRIMARY, alpha=0.30, linewidths=0, zorder=3,
               label="una ciudad de más de 5.000 hab. en la cohorte")

    d["decil"] = pd.qcut(np.log(d["pob_ciudad"]), 10, labels=False, duplicates="drop")
    agg = d.groupby("decil").agg(jug=("jugadores", "sum"),
                                 pob=("pob_cohorte_ciudad", "sum"),
                                 tam=("pob_ciudad", "median"))
    r, lo, hi = poisson_rate_ci(agg["jug"], agg["pob"])
    ax.errorbar(agg["tam"], r, yerr=[r - lo, hi - r], fmt="o", ms=5.5,
                color=style.ACCENT, ecolor=style.ACCENT, elinewidth=1.2, capsize=2.5,
                markeredgecolor=style.SURFACE, markeredgewidth=1.2, zorder=6,
                label="tasa agregada por decil de tamaño (IC 95%)")

    X = sm.add_constant(np.log(d["pob_ciudad"]))
    fit = sm.GLM(d["jugadores"], X, family=sm.families.NegativeBinomial(alpha=1.0),
                 offset=np.log(d["pob_cohorte_ciudad"])).fit()
    xs = np.linspace(np.log(d["pob_ciudad"].min()), np.log(d["pob_ciudad"].max()), 120)
    ys = 1e5 * np.exp(fit.params.iloc[0] + fit.params.iloc[1] * xs)
    ax.plot(np.exp(xs), ys, color=style.INK, lw=1.6, zorder=7,
            label="ajuste binomial negativo (todas las ciudades)")

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_ylim(2, 400)
    ax.set_xlabel("Población de la ciudad de nacimiento (escala logarítmica)")
    ax.set_ylabel("Futbolistas por 100.000 hab.")
    style.titulo_y_bajada(ax, "No hay pico en las ciudades medianas",
                          "La curva sube de forma monótona: el patrón clásico del "
                          "birthplace effect no aparece")
    style.despine(ax)
    leg = ax.legend(loc="lower right", fontsize=6.8, borderpad=0.6)
    for t_ in leg.get_texts():
        t_.set_color(style.INK_2)
    fuera = int((legibles["tasa"] > 400).sum())
    _pie(fig, f"n = {int(d['jugadores'].sum()):,} futbolistas en {len(d):,} ciudades. "
              f"IRR por cada e-fold de tamaño = {np.exp(fit.params.iloc[1]):.3f} "
              f"(IC 95% {np.exp(fit.conf_int().iloc[1, 0]):.3f}–"
              f"{np.exp(fit.conf_int().iloc[1, 1]):.3f}). "
              f"El scatter excluye las ciudades con menos de 5.000 habitantes en la "
              f"cohorte, donde un solo jugador ya da tasas de tres dígitos"
              .replace(",", ".") + (f"; {fuera} puntos quedan sobre el tope del eje.\n"
                                    if fuera else ".\n") + FUENTE_BASE)
    style.guardar(fig, "fig07_scatter_tamano_tasa", cfg, p.figures)


def main() -> None:
    cfg = load_config()
    p = paths()
    style.apply_style(cfg)

    fig_mapas_departamento(cfg, p)
    fig_mapa_provincias(cfg, p)
    fig_cartograma(cfg, p)
    fig_tramos(cfg, p)
    fig_regiones(cfg, p)
    fig_scatter_tamano(cfg, p)

    salidas = sorted(f.name for f in p.figures.glob("*.pdf"))
    log.info("figuras generadas: %s", salidas)


if __name__ == "__main__":
    main()
