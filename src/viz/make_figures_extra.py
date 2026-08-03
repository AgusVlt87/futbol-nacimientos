"""Fase 9 — Figuras nuevas: selección, robustez y diagnóstico.

Complementa `make_figures.py` (figuras 1 a 13) con trece figuras más, en cuatro
bloques:

    14–18  Selección argentina. Incluye el resultado que NO depende del
           denominador poblacional: la conversión juvenil → Mayor.
    19–22  Robustez y diagnóstico. Lo que el estudio tiene que mostrar para que
           no le entren balas: el sesgo del denominador, el ruido de los
           números chicos, la ausencia de gradiente por debajo de 10.000
           habitantes y la estabilidad del efecto por cohorte.
    23–24  Provincias: ranking con intervalos y sensibilidad al denominador.
    25–26  Formación: matriz de flujo entre regiones y retención.

Mismas reglas que el módulo hermano: `style.Figura` reserva las bandas, no se
usa `bbox_inches="tight"`, y la leyenda de los mapas va en su propia banda.

Uso:
    python -m src.viz.make_figures_extra
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

from src.analysis.stats import poisson_rate_ci
from src.common import get_logger, load_config, paths
from src.viz import maps, style
from src.viz.style import Figura, miles
from src.denominadores import cargar_ciudades

log = get_logger("viz.extra")

FUENTE = "Fuente: Wikidata (2026-07-30), DEIS (nacidos vivos 1914-2024) e INDEC. Elaboración propia."
DENOM = ("Denominador: nacidos vivos de la misma cohorte en el mismo lugar "
         "(dato real por provincia; estimado por departamento, error mediano 9%).")
ORDEN_TRAMOS = ["<10k", "10–50k", "50–100k", "100–500k", ">500k"]


def _t(p, nombre):
    return pd.read_csv(p.tables / f"{nombre}.csv")


def _barras_h(ax, etiquetas, valores, lo=None, hi=None, color=style.PRIMARY,
              formato="{:.1f}", destacar=None, unidad=""):
    """Barras horizontales con IC y etiqueta directa en la punta.

    La etiqueta directa es obligatoria y no decorativa: tres de las ranuras
    categóricas de la paleta quedan por debajo de 3:1 contra la superficie, y la
    regla de la paleta es que en ese caso el valor va escrito.
    """
    y = np.arange(len(etiquetas))[::-1]
    colores = [color if (destacar is None or e in destacar) else style.MUTED
               for e in etiquetas]
    ax.barh(y, valores, height=0.62, color=colores, zorder=3)
    if lo is not None:
        ax.errorbar(valores, y, xerr=[np.array(valores) - np.array(lo),
                                      np.array(hi) - np.array(valores)],
                    fmt="none", ecolor=style.INK_2, elinewidth=1.0, capsize=2.5,
                    zorder=5)
    tope = max(hi) if hi is not None else max(valores)
    for yi, v in zip(y, valores):
        ax.text(tope * 1.03, yi, formato.format(v) + unidad, va="center",
                ha="left", fontsize=style.PT_BASE - 1, color=style.INK)
    ax.set_yticks(y, etiquetas)
    ax.set_xlim(0, tope * 1.22)
    ax.grid(True, axis="x")
    style.despine(ax, izquierda=True)
    ax.tick_params(axis="y", length=0)
    return y


# --------------------------------------------------------------------------- #
# Bloque selección
# --------------------------------------------------------------------------- #
def fig14_conversion_tramo(cfg, p):
    """EL resultado robusto: no usa denominador poblacional."""
    d = _t(p, "seleccion_conversion_por_tramo")
    d["tramo"] = pd.Categorical(d["tramo"], ORDEN_TRAMOS, ordered=True)
    d = d.sort_values("tramo")
    t = _t(p, "seleccion_conversion_tests").iloc[0]

    f = Figura(6.8, 4.3,
               "Al pibe del interior le cuesta más entrar, pero el que entra rinde más",
               "De los futbolistas que llegaron a un juvenil de la selección, qué "
               "porcentaje\nllegó después a la Mayor, según el tamaño de su ciudad de "
               "nacimiento",
               "Este análisis NO usa denominador poblacional: el denominador son los "
               "juveniles observados. Por eso no lo afectan ni el reparto de "
               "nacimientos por departamento, ni el registro del parto en la ciudad "
               "cabecera, ni la cobertura de Wikidata.\n"
               "Intervalos binomiales exactos (Clopper-Pearson). " + FUENTE, cfg)
    ax = f.eje(izq=0.045, abajo=0.09)

    _barras_h(ax, list(d["tramo"].astype(str)), list(d["pct_conversion"]),
              list(d["ic_lo"]), list(d["ic_hi"]),
              formato="{:.0f}", unidad="%")
    for yi, llegan, juveniles in zip(np.arange(len(d))[::-1],
                                     d["llegan_a_mayor"], d["juveniles"]):
        ax.text(1.5, yi, f"{int(llegan)} de {int(juveniles)}", va="center",
                ha="left", fontsize=style.PT_BASE - 2, color="#ffffff", zorder=6)
    ax.set_xlabel("% de los juveniles que llegan a la Selección Mayor")

    f.nota(ax, f"Fuera de un gran aglomerado: {t['fuera_metro_pct']:.1f}%   ·   "
               f"en uno: {t['metro_pct']:.1f}%\n"
               f"OR = {t['OR']:.2f} (IC 95% {t['OR_ic_lo']:.2f}–{t['OR_ic_hi']:.2f}), "
               f"p = {t['p_fisher_exacto']:.3f}\n"
               f"ajustado por cohorte de nacimiento: OR = "
               f"{t['OR_ajustado_por_cohorte']:.2f}, p = {t['p_ajustado']:.3f}",
           0.42, 0.06, fontsize=6.9)
    f.guardar("fig14_conversion_juvenil_mayor", p.figures)


def fig15_conversion_region(cfg, p):
    d = _t(p, "seleccion_conversion_por_region").sort_values("pct_conversion",
                                                             ascending=False)
    f = Figura(6.8, 3.9,
               "La conversión a la Mayor por región de nacimiento",
               "De los que llegaron a un juvenil de la selección, qué porcentaje "
               "llegó a la Mayor",
               "Cuyo, NOA, NEA y Patagonia tienen entre 9 y 13 juveniles cada uno: "
               "las diferencias entre ellos no son interpretables. Lo interpretable "
               "es el contraste AMBA (144 juveniles) contra el resto del país.\n"
               + FUENTE, cfg)
    ax = f.eje(izq=0.035, abajo=0.10)
    _barras_h(ax, list(d["region"]), list(d["pct_conversion"]), formato="{:.0f}",
              unidad="%", destacar=["AMBA"])
    for yi, juveniles, llegan in zip(np.arange(len(d))[::-1],
                                     d["juveniles"], d["llegan_a_mayor"]):
        ax.text(1.5, yi, f"{int(llegan)} de {int(juveniles)}", va="center",
                ha="left", fontsize=style.PT_BASE - 2, color="#ffffff", zorder=6)
    ax.set_xlabel("% de los juveniles que llegan a la Selección Mayor")
    f.guardar("fig15_conversion_por_region", p.figures)


def fig16_embudo(cfg, p):
    """El embudo completo: de nacer a la Mayor, por origen."""
    tasas = _t(p, "seleccion_tasas_por_tramo")
    h1 = _t(p, "h1_tramos_principal")
    conv = _t(p, "seleccion_conversion_por_tramo")

    prof = h1.set_index("unidad")["tasa"]
    juv = tasas[tasas["grupo"] == "Juveniles (sub-17 / sub-20)"].set_index("tramo")["por_millon"]
    may = tasas[tasas["grupo"] == "Selección Mayor"].set_index("tramo")["por_millon"]
    cv = conv.set_index("tramo")["pct_conversion"]

    f = Figura(7.2, 4.4,
               "Dónde se angosta el embudo",
               "Tres escalones desde el nacimiento. Los dos primeros dependen del "
               "denominador\npoblacional; el tercero no, y es el único donde el "
               "interior gana",
               "Los dos primeros paneles son tasas por nacido y comparten las "
               "limitaciones del denominador. El tercero es una proporción dentro "
               "de un grupo observado.\n" + DENOM + " " + FUENTE, cfg)
    # La separación tiene que alojar DOS cosas en el mismo hueco: la etiqueta de
    # valor del panel de la izquierda, que se dibuja adentro contra su borde
    # derecho, y los rótulos del eje y del panel de la derecha, que se dibujan
    # afuera contra su borde izquierdo. Con 0,055 se pisaban.
    axes = f.ejes_lado_a_lado(3, separacion=0.10, sangria_izq=0.02, abajo=0.10,
                              titulos=["1. Llegar a profesional",
                                       "2. Llegar a un juvenil",
                                       "3. Del juvenil a la Mayor"])
    series = [(prof, "cada 100.000 nacidos", "{:.0f}"),
              (juv, "cada millón de nacidos", "{:.1f}"),
              (cv, "% de los juveniles", "{:.0f}")]
    for ax, (s, etiqueta, fmt) in zip(axes, series):
        vals = [float(s.get(t_, np.nan)) for t_ in ORDEN_TRAMOS]
        _barras_h(ax, ORDEN_TRAMOS, vals, formato=fmt,
                  destacar=None if s is cv else [">500k"],
                  color=style.ACCENT if s is cv else style.PRIMARY)
        ax.set_xlabel(etiqueta, fontsize=style.PT_BASE - 1.5)
    f.guardar("fig16_embudo_por_origen", p.figures)


def fig17_seleccion_clubes(cfg, p):
    d = _t(p, "seleccion_clubes_formadores").head(14)
    f = Figura(6.8, 4.6,
               "De qué clubes salen los seleccionados",
               "Clubes formadores de los futbolistas que llegaron a la selección "
               "argentina\n(Mayor o juvenil), cohortes 1975-2008",
               "Club formador = el vínculo jugador-club más temprano con fecha en "
               "Wikidata. Es un proxy y suele ser el club de debut, no el de "
               "inferiores; en jugadores de selección la cobertura es del 97%, la "
               "más alta de la muestra.\n" + FUENTE, cfg)
    ax = f.eje(izq=0.13, abajo=0.09)
    nombres = [maps.nombre_club(c) for c in d["primer_club"]]
    y = np.arange(len(d))[::-1]
    ax.barh(y, d["seleccionados"], height=0.62, color=style.PRIMARY, zorder=3,
            label="llegaron a un juvenil")
    ax.barh(y, d["de_los_cuales_mayor"], height=0.62, color=style.SERIES[6],
            zorder=4, label="de esos, llegaron a la Mayor")
    for yi, (tot, may) in zip(y, zip(d["seleccionados"], d["de_los_cuales_mayor"])):
        ax.text(tot + 1.2, yi, f"{int(tot)}  ({int(may)} a la Mayor)", va="center",
                ha="left", fontsize=style.PT_BASE - 1.5, color=style.INK)
    ax.set_yticks(y, nombres)
    ax.set_xlim(0, d["seleccionados"].max() * 1.42)
    ax.grid(True, axis="x")
    style.despine(ax, izquierda=True)
    ax.tick_params(axis="y", length=0)
    ax.set_xlabel("Futbolistas de selección formados en el club")
    lg = ax.legend(loc="lower right", fontsize=6.9)
    for t_ in lg.get_texts():
        t_.set_color(style.INK_2)
    f.guardar("fig17_clubes_de_seleccionados", p.figures)


def fig18_seleccion_migracion(cfg, p):
    d = _t(p, "seleccion_migracion_por_tramo")
    d["tramo"] = pd.Categorical(d["tramo"], ORDEN_TRAMOS, ordered=True)
    d = d.sort_values("tramo")
    f = Figura(6.8, 4.0,
               "Cuánto se tiene que mover un seleccionado según dónde nació",
               "Distancia entre la ciudad de nacimiento y el club formador, "
               "mediana por tramo",
               "Distancia entre centroides: dentro de un mismo aglomerado da cerca "
               "de cero. Solo jugadores que llegaron a la selección (Mayor o "
               "juvenil) y tienen club formador ubicado.\n" + FUENTE, cfg)
    ax = f.eje(izq=0.045, abajo=0.10)
    _barras_h(ax, list(d["tramo"].astype(str)), list(d["km_mediana"]),
              formato="{:.0f}", unidad=" km", destacar=[">500k"])
    for yi, n in zip(np.arange(len(d))[::-1], d["seleccionados"]):
        ax.text(6, yi, f"n = {int(n)}", va="center", ha="left",
                fontsize=style.PT_BASE - 2, color="#ffffff", zorder=6)
    ax.set_xlabel("Kilómetros entre el lugar de nacimiento y el club formador (mediana)")
    f.guardar("fig18_migracion_seleccionados", p.figures)


# --------------------------------------------------------------------------- #
# Bloque robustez y diagnóstico
# --------------------------------------------------------------------------- #
def fig19_sesgo_denominador(cfg, p):
    """El diagnóstico más importante: el error del denominador tiene pendiente."""
    d = pd.read_csv(p.tables / "qa_validacion_denominador_detalle.csv")
    d = d[(d["nacimientos_reales"] > 0) & d["nacimientos_cohorte"].notna()].copy()
    d["ratio"] = d["nacimientos_cohorte"] / d["nacimientos_reales"]
    d["decil"] = pd.qcut(d["nacimientos_reales"], 10, labels=False, duplicates="drop")
    g = d.groupby("decil").agg(med=("nacimientos_reales", "median"),
                               ratio=("ratio", "median"))

    f = Figura(6.8, 4.1,
               "El denominador estimado le sobra nacimientos a los departamentos chicos",
               "Nacimientos estimados dividido nacimientos reales, por decil de "
               "tamaño del departamento.\nUn valor mayor que 1 infla el "
               "denominador y por lo tanto deprime la tasa de ese lugar",
               "Validación contra los nacimientos departamentales reales del RENAPER "
               "(2012-2022). El sesgo empuja en la misma dirección que el hallazgo "
               "principal: hay que declararlo y acotarlo, no promediarlo.\n" + FUENTE,
               cfg)
    ax = f.eje(izq=0.02, abajo=0.10)
    ax.scatter(d["nacimientos_reales"], d["ratio"], s=7, color=style.PRIMARY,
               alpha=0.22, linewidths=0, zorder=2, label="un departamento")
    ax.plot(g["med"], g["ratio"], "o-", color=style.ACCENT, lw=1.8, ms=6,
            markeredgecolor=style.SURFACE, markeredgewidth=1.2, zorder=6,
            label="mediana por decil de tamaño")
    ax.axhline(1.0, color=style.INK_2, lw=1.0, ls=(0, (4, 3)), zorder=4)
    # Encima de la línea, no sobre ella: con va="center" el trazo punteado
    # cruzaba el texto por la mitad.
    ax.text(d["nacimientos_reales"].max(), 1.015, "sin sesgo", va="bottom",
            ha="right", fontsize=6.8, color=style.INK_2)
    ax.set_xscale("log")
    ax.set_ylim(0.3, 2.4)
    ax.grid(True, axis="y")
    style.despine(ax)
    ax.set_xlabel("Nacimientos reales del departamento, 2012-2022 (escala logarítmica)")
    ax.set_ylabel("Estimado / real")
    f.nota(ax, f"decil más chico: +{100 * (g['ratio'].iloc[0] - 1):.0f}% de denominador\n"
               f"decil más grande: {100 * (g['ratio'].iloc[-1] - 1):+.0f}%",
           0.02, 0.87, fontsize=6.9)
    lg = ax.legend(loc="lower right", fontsize=6.9)
    for t_ in lg.get_texts():
        t_.set_color(style.INK_2)
    f.guardar("fig19_sesgo_del_denominador", p.figures)


def fig20_deciles_sin_gradiente(cfg, p):
    """Lo que el binning de cinco tramos esconde."""
    players = pd.read_parquet(p.processed / "analysis_players.parquet")
    ciudades = cargar_ciudades(p)
    conteo = players.groupby("ciudad_id").size().rename("jugadores")
    d = ciudades.set_index("ciudad_id").join(conteo).fillna({"jugadores": 0})
    d = d[(d["nacimientos_cohorte"] > 0) & (d["pob_ciudad"] > 0)].copy()
    d["decil"] = pd.qcut(d["pob_ciudad"], 10, labels=False, duplicates="drop")
    g = d.groupby("decil").agg(j=("jugadores", "sum"), n=("nacimientos_cohorte", "sum"),
                               tam=("pob_ciudad", "median"))
    r, lo, hi = poisson_rate_ci(g["j"], g["n"])

    f = Figura(6.8, 4.2,
               "El «gradiente» es un escalón, y está todo en el decil más grande",
               "Tasa por decil de tamaño de ciudad. Entre los nueve deciles de abajo "
               "no hay tendencia:\nsuben y bajan sin orden, y juntos son el 9% de "
               "los futbolistas",
               "Con los cinco tramos del diseño el patrón parece monótono porque "
               "esos nueve deciles quedan fusionados en cuatro categorías anchas. "
               "La forma real del efecto —un escalón único— es también la que "
               "produciría el registro del parto en la ciudad cabecera.\n" + FUENTE,
               cfg)
    ax = f.eje(izq=0.02, abajo=0.10)
    x = np.arange(len(g))
    colores = [style.MUTED] * (len(g) - 1) + [style.PRIMARY]
    ax.bar(x, r, width=0.68, color=colores, zorder=3)
    ax.errorbar(x, r, yerr=[r - lo, hi - r], fmt="none", ecolor=style.INK_2,
                elinewidth=1.0, capsize=2.5, zorder=5)
    for xi, (v, t_) in enumerate(zip(r, g["tam"])):
        ax.text(xi, hi[xi] + 0.9, f"{v:.0f}", ha="center", va="bottom",
                fontsize=style.PT_BASE - 1.5, color=style.INK)
    ax.set_xticks(x, [miles(t_) for t_ in g["tam"]], rotation=45, ha="right")
    ax.set_xlabel("Población mediana de las ciudades del decil")
    ax.set_ylabel("Futbolistas cada 100.000 nacidos")
    ax.grid(True, axis="y")
    style.despine(ax)
    ax.set_ylim(0, max(hi) * 1.16)
    sin_señal = int(g["j"].iloc[:-1].sum())
    # A la izquierda la nota chocaba con la etiqueta del primer decil, cuyo
    # intervalo llega casi al tope del eje. Va donde el gráfico está vacío.
    f.nota(ax, f"deciles 1 a 9: {miles(sin_señal)} futbolistas "
               f"({100 * sin_señal / g['j'].sum():.0f}% del total), sin tendencia\n"
               f"decil 10: {miles(int(g['j'].iloc[-1]))} futbolistas",
           0.42, 0.93, fontsize=6.9)
    f.guardar("fig20_deciles_sin_gradiente", p.figures)


def fig21_funnel(cfg, p):
    """Funnel plot: separa la señal del ruido de Poisson."""
    d = _t(p, "h2_departamentos")
    # Por debajo de 1.000 nacimientos en 34 años el embudo se abre tanto que la
    # banda ocupa toda la figura y no informa nada; además ahí caen las pocas
    # unidades cuyo denominador no se pudo estimar. Se excluyen y se declara.
    d = d[d["nacimientos"] >= 1000].copy()
    media = 1e5 * d["jugadores"].sum() / d["nacimientos"].sum()

    f = Figura(6.8, 4.3,
               "Qué departamentos se salen de verdad y cuáles son ruido",
               "Cada punto es un departamento. Las curvas son los límites del "
               "95% esperado\npor puro azar dado el tamaño del departamento",
               "Un departamento con dos jugadores encabeza cualquier ranking per "
               "cápita sin que eso signifique nada: adentro del embudo, la tasa es "
               "compatible con la media nacional. Solo los puntos de afuera son "
               "candidatos a hallazgo. Se excluyen los departamentos con menos de "
               "1.000 nacimientos en la ventana.\n" + DENOM + " " + FUENTE, cfg)
    ax = f.eje(izq=0.02, abajo=0.10)

    n = np.logspace(np.log10(max(d["nacimientos"].min(), 100)),
                    np.log10(d["nacimientos"].max()), 200)
    lam = media * n / 1e5
    lo = 1e5 * (lam - 1.96 * np.sqrt(lam)) / n
    hi = 1e5 * (lam + 1.96 * np.sqrt(lam)) / n
    ax.fill_between(n, np.clip(lo, 0, None), hi, color=style.PRIMARY, alpha=0.10,
                    zorder=1, label="banda del 95% esperado por azar")
    ax.plot(n, np.full_like(n, media), color=style.INK_2, lw=1.1, zorder=4,
            label=f"media nacional ({media:.0f} cada 100.000)")

    afuera = (d["tasa"] > np.interp(d["nacimientos"], n, hi)) | \
             (d["tasa"] < np.interp(d["nacimientos"], n, np.clip(lo, 0, None)))
    ax.scatter(d.loc[~afuera, "nacimientos"], d.loc[~afuera, "tasa"], s=10,
               color=style.MUTED, alpha=0.45, linewidths=0, zorder=3,
               label="compatible con la media")
    ax.scatter(d.loc[afuera, "nacimientos"], d.loc[afuera, "tasa"], s=16,
               color=style.ACCENT, alpha=0.85, linewidths=0, zorder=5,
               label="fuera de la banda")
    # Las etiquetas van a la IZQUIERDA del punto: los departamentos más grandes
    # están contra el borde derecho del eje y hacia afuera quedaban cortados.
    for r_ in d[afuera].nlargest(5, "jugadores").itertuples():
        nombre = maps.NOMBRE_CORTO.get(r_.departamento, r_.departamento)
        ax.annotate(nombre, (r_.nacimientos, r_.tasa), xytext=(-9, 0),
                    textcoords="offset points", ha="right", va="center",
                    fontsize=6.5, color=style.INK, fontweight="bold", zorder=8)
    ax.set_xscale("log")
    ax.set_ylim(0, 130)
    ax.grid(True, axis="y")
    style.despine(ax)
    ax.set_xlabel("Nacimientos del departamento en la ventana (escala logarítmica)")
    ax.set_ylabel("Futbolistas cada 100.000 nacidos")
    lg = ax.legend(loc="upper right", fontsize=6.8)
    for t_ in lg.get_texts():
        t_.set_color(style.INK_2)
    f.guardar("fig21_funnel_departamentos", p.figures)


def fig22_efecto_por_cohorte(cfg, p):
    """¿El efecto se profundiza con el tiempo? La prueba del mecanismo."""
    players = pd.read_parquet(p.processed / "analysis_players.parquet")
    den = (pd.read_parquet(p.processed / "denom_cohorte_ciudad.parquet")
           .merge(pd.read_parquet(p.processed / "denom_ciudad_unica.parquet")
                  [["ciudad_id", "tramo"]], on="ciudad_id"))
    prov = pd.read_parquet(p.processed / "nacimientos_provincia_anio.parquet")
    tot = prov.groupby("anio")["nacimientos"].sum()
    c = cfg["cohorts"]
    pl = players.dropna(subset=["tramo"])
    base = den.groupby("tramo", observed=True)["nacimientos_cohorte"].sum()

    filas = []
    for dec, sub in pl.groupby("decada"):
        años = [y for y in range(int(dec), int(dec) + 10)
                if c["analysis_min_year"] <= y <= c["analysis_max_year"]]
        if not años:
            continue
        frac = tot.loc[años].sum() / tot.loc[c["analysis_min_year"]:c["analysis_max_year"]].sum()
        obs = sub.groupby("tramo", observed=True).size()
        k1, n1 = obs.get("<10k", 0), base["<10k"] * frac
        k2, n2 = obs.get(">500k", 0), base[">500k"] * frac
        rr = (k1 / n1) / (k2 / n2)
        se = np.sqrt(1 / max(k1, 1) + 1 / max(k2, 1))
        filas.append({"decada": int(dec), "rr": rr, "lo": rr * np.exp(-1.96 * se),
                      "hi": rr * np.exp(1.96 * se), "n": int(obs.sum()),
                      "censurada": int(dec) >= 2000})
    g = pd.DataFrame(filas)

    f = Figura(6.8, 4.1,
               "El efecto no se profundiza con el tiempo",
               "Razón de tasas entre nacer en una localidad de menos de 10.000 "
               "habitantes\ny nacer en un aglomerado de más de 500.000, por década "
               "de nacimiento",
               "Si la causa fuera la centralización creciente de las inferiores, "
               "esta línea debería BAJAR: la brecha tendría que ensancharse. Está "
               "plana. La década de 2000 está censurada (muchos todavía no "
               "debutaron).\n" + FUENTE, cfg)
    ax = f.eje(izq=0.02, abajo=0.10)
    x = np.arange(len(g))
    color = [style.PRIMARY if not cen else style.MUTED for cen in g["censurada"]]
    ax.errorbar(x, g["rr"], yerr=[g["rr"] - g["lo"], g["hi"] - g["rr"]],
                fmt="none", ecolor=style.INK_2, elinewidth=1.1, capsize=3, zorder=4)
    ax.scatter(x, g["rr"], s=70, c=color, zorder=6, edgecolors=style.SURFACE,
               linewidths=1.4)
    for xi, r_ in zip(x, g.itertuples()):
        ax.text(xi, r_.hi + 0.035, f"{r_.rr:.2f}", ha="center", va="bottom",
                fontsize=style.PT_BASE - 1.5, color=style.INK)
    # El 1,0 tiene que entrar en la escala: es la referencia que da sentido al
    # eje («sin diferencia entre pueblo y ciudad»), y con el eje cortado en 0,83
    # la línea caía fuera y su rótulo terminaba flotando sobre el encabezado.
    ax.axhline(1.0, color=style.INK_2, lw=1.0, ls=(0, (4, 3)), zorder=2)
    ax.text(-0.42, 1.0, "sin diferencia entre pueblo y ciudad", va="bottom",
            ha="left", fontsize=6.8, color=style.INK_2)
    ax.set_xticks(x, [f"{d_}s\nn = {miles(n_)}" for d_, n_ in zip(g["decada"], g["n"])])
    ax.set_xlim(-0.5, len(g) - 0.15)
    ax.set_ylim(0, 1.14)
    ax.set_ylabel("Razón de tasas  (<10k / >500k)")
    ax.grid(True, axis="y")
    style.despine(ax)
    leg = [Line2D([], [], marker="o", ls="", color=style.PRIMARY, ms=8,
                  label="cohorte con carrera plausiblemente iniciada"),
           Line2D([], [], marker="o", ls="", color=style.MUTED, ms=8,
                  label="cohorte censurada")]
    # Abajo a la derecha: arriba a la izquierda se apilaba con la línea del 1,0
    # y su rótulo. Todas las razones de tasas están entre 0,25 y 0,72, así que
    # la mitad inferior del eje está vacía.
    lg = ax.legend(handles=leg, loc="lower right", fontsize=6.8)
    for t_ in lg.get_texts():
        t_.set_color(style.INK_2)
    f.guardar("fig22_efecto_por_cohorte", p.figures)


# --------------------------------------------------------------------------- #
# Bloque provincias
# --------------------------------------------------------------------------- #
def fig23_ranking_provincias(cfg, p):
    d = _t(p, "h2_provincias").sort_values("tasa", ascending=False)
    f = Figura(6.4, 6.6,
               "Las 24 jurisdicciones, ordenadas",
               "Futbolistas cada 100.000 nacidos vivos de la misma cohorte, con "
               "intervalo del 95%",
               "A nivel provincial el denominador es dato real del DEIS, sin "
               "estimación: es el nivel más sólido de todo el estudio.\n" + FUENTE,
               cfg)
    ax = f.eje(izq=0.11, abajo=0.055)
    y = np.arange(len(d))[::-1]
    ax.hlines(y, d["tasa_ic_lo"], d["tasa_ic_hi"], color=style.AXIS, lw=1.6, zorder=3)
    ax.scatter(d["tasa"], y, s=46, color=style.PRIMARY, zorder=5,
               edgecolors=style.SURFACE, linewidths=1.2)
    media = 1e5 * d["jugadores"].sum() / d["nacimientos"].sum()
    ax.axvline(media, color=style.INK_2, lw=1.0, ls=(0, (4, 3)), zorder=2)
    ax.text(media, len(d) - 0.2, f" media nacional {media:.0f}", ha="left",
            va="top", fontsize=6.8, color=style.INK_2)
    for yi, r_ in zip(y, d.itertuples()):
        ax.text(d["tasa_ic_hi"].max() * 1.02, yi, f"{r_.tasa:.0f}", va="center",
                ha="left", fontsize=style.PT_BASE - 1.5, color=style.INK)
    # `unidad` es el código INDEC de la provincia; el nombre está en `provincia`.
    ax.set_yticks(y, [maps.NOMBRE_CORTO.get(v, v) for v in d["provincia"]])
    ax.set_xlim(0, d["tasa_ic_hi"].max() * 1.10)
    ax.set_xlabel("Futbolistas cada 100.000 nacidos")
    ax.grid(True, axis="x")
    style.despine(ax, izquierda=True)
    ax.tick_params(axis="y", length=0)
    f.guardar("fig23_ranking_provincias", p.figures)


def fig24_sensibilidad_denominador(cfg, p):
    """¿Cambia el orden si cambia el denominador? La respuesta a «elegiste el que te servía»."""
    fuentes = {
        "Nacidos vivos (DEIS)": "h2_provincias",
        "Censo 1991": "h2_provincias_censo_1991",
        "Censo 2001": "h2_provincias_censo_2001",
        "Censo 2010": "h2_provincias_censo_2010",
        "Censo 2022": "h2_provincias_censo_2022",
        "Nacidos según censo (P14)": "h2_provincias_baseline_censo_p14",
    }
    series = {}
    for nombre, tabla in fuentes.items():
        try:
            t = _t(p, tabla)
        except FileNotFoundError:
            continue
        # Se indexa por NOMBRE, no por `unidad`: esa columna es el código INDEC.
        series[nombre] = t.set_index("provincia")["obs_sobre_esp"]
    m = pd.DataFrame(series)
    orden = m["Nacidos vivos (DEIS)"].sort_values(ascending=False).index
    m = m.loc[orden]

    f = Figura(6.8, 6.4,
               "El orden no depende del denominador que elijas",
               "Producción observada dividido la esperada por su población, con "
               "seis denominadores distintos.\nCada línea es una jurisdicción; si "
               "el resultado dependiera del baseline, se cruzarían",
               "1,0 significa «produce exactamente lo que le tocaría». Los seis "
               "denominadores incluyen el que el estudio usa y los cinco "
               "alternativos.\n" + FUENTE, cfg)
    ax = f.eje(izq=0.10, abajo=0.10)
    y = np.arange(len(m))[::-1]
    for j, col in enumerate(m.columns):
        ax.scatter(m[col], y, s=26, color=style.SERIES[j % len(style.SERIES)],
                   alpha=0.85, zorder=4, label=col, linewidths=0)
    ax.hlines(y, m.min(axis=1), m.max(axis=1), color=style.AXIS, lw=1.0, zorder=2)
    ax.axvline(1.0, color=style.INK_2, lw=1.0, ls=(0, (4, 3)), zorder=3)
    ax.set_yticks(y, [maps.NOMBRE_CORTO.get(v, v) for v in m.index])
    ax.set_xscale("log")
    ax.set_xticks([0.1, 0.25, 0.5, 1, 2, 4], ["0,1", "0,25", "0,5", "1", "2", "4"])
    ax.set_xlabel("Observado / esperado (escala logarítmica)")
    ax.grid(True, axis="x")
    style.despine(ax, izquierda=True)
    ax.tick_params(axis="y", length=0)
    # Arriba a la izquierda: las jurisdicciones que encabezan están a la derecha
    # del eje, así que ese rincón es el único que queda vacío.
    lg = ax.legend(loc="upper left", fontsize=6.6, ncols=2)
    for t_ in lg.get_texts():
        t_.set_color(style.INK_2)
    f.guardar("fig24_sensibilidad_denominador", p.figures)


# --------------------------------------------------------------------------- #
# Bloque formación
# --------------------------------------------------------------------------- #
def fig25_matriz_flujo(cfg, p):
    m = _t(p, "h3_matriz_flujo_regiones_pct")
    idx = m.columns[0]
    m = m.set_index(idx)
    orden = [r for r in ["AMBA", "Pampeana", "Cuyo", "NOA", "NEA", "Patagonia"]
             if r in m.index and r in m.columns]
    m = m.loc[orden, orden]

    f = Figura(6.2, 5.0,
               "Adónde se va a formar cada región",
               "De los nacidos en cada región (filas), qué porcentaje se formó en "
               "cada región (columnas).\nLa diagonal es la retención",
               "Club formador = vínculo jugador-club más temprano con fecha en "
               "Wikidata. La cobertura de ese dato es muy desigual por nivel (97% "
               "en selección, 12% en el resto), así que estos porcentajes son orden "
               "de magnitud.\n" + FUENTE, cfg)
    ax = f.eje(izq=0.075, abajo=0.045, arriba=0.02)
    v = m.values.astype(float)
    ax.imshow(v, cmap=style.SEQ, vmin=0, vmax=100, aspect="auto")
    for i in range(v.shape[0]):
        for j in range(v.shape[1]):
            ax.text(j, i, f"{v[i, j]:.0f}", ha="center", va="center",
                    fontsize=style.PT_BASE - 0.5,
                    color="#ffffff" if v[i, j] > 45 else style.INK,
                    fontweight="bold" if i == j else "normal")
    ax.set_xticks(range(len(orden)), orden)
    ax.set_yticks(range(len(orden)), orden)
    ax.set_xlabel("Región del club formador")
    ax.set_ylabel("Región de nacimiento")
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    f.guardar("fig25_matriz_flujo_regiones", p.figures)


def fig26_retencion(cfg, p):
    d = _t(p, "h3_migracion_por_region_origen")
    col = "pct_se_forma_en_su_region" if "pct_se_forma_en_su_region" in d.columns \
        else [c for c in d.columns if "reten" in c.lower() or "pct" in c.lower()][0]
    d = d.sort_values(col, ascending=False)
    f = Figura(6.8, 3.9,
               "Qué región se queda con los futbolistas que nacen en ella",
               "Porcentaje de los nacidos en cada región que se formó en un club "
               "de esa misma región",
               "El AMBA retiene casi a todos los suyos y además recibe. El NEA "
               "retiene a uno de cada doce. Mismo proxy de club formador y mismas "
               "limitaciones de cobertura.\n" + FUENTE, cfg)
    ax = f.eje(izq=0.035, abajo=0.10)
    _barras_h(ax, list(d["region"]), list(d[col]), formato="{:.0f}", unidad="%",
              destacar=["AMBA"])
    ax.set_xlabel("% que se forma en su región de nacimiento")
    f.guardar("fig26_retencion_por_region", p.figures)


def fig27_criterio_del_registro(cfg, p):
    """La prueba de que ninguna de las dos puntas registra el lugar del parto.

    Es la figura que contesta la pregunta de la que dependía todo el trabajo, y
    que el paper declaraba sin resolver.
    """
    prov = pd.read_csv(p.tables / "criterio_denominador_provincias.csv",
                       dtype={"prov_id": str})
    tam = pd.read_csv(p.tables / "criterio_p19_por_tamano_localidad.csv")

    f = Figura(7.2, 4.0,
               "Ni el denominador ni el numerador registran dónde ocurrió el parto",
               "Las dos pruebas que descartan el artefacto de las maternidades, "
               "que era la amenaza principal\ncontra todo el trabajo",
               "Izquierda: la serie histórica del DEIS se publica como «nacimientos "
               "ocurridos», pero coincide con la tabulación por residencia de la madre "
               "en las 432 celdas provincia×año de su solapamiento (2005–2022), con "
               "diferencia máxima cero. Si contara partos, CABA —cuyas maternidades "
               "atienden al conurbano— caería muy por encima de la diagonal.\n"
               "Derecha: si el P19 de Wikidata registrara el parto, las localidades sin "
               "maternidad tendrían cero futbolistas. Hay 76 en localidades de menos de "
               "2.000 habitantes, repartidos en 63 localidades distintas.\n" + FUENTE,
               cfg)
    izq, der = f.ejes_lado_a_lado(2, separacion=0.085, sangria_izq=0.012, abajo=0.11,
                                 titulos=["Denominador: ¿ocurrencia o residencia?",
                                          "Numerador: ¿el parto o el pueblo?"])

    # --- panel izquierdo: las dos series, provincia por provincia ------------
    x, y = prov["por_residencia"], prov["serie_historica"]
    lim = [x.min() * 0.7, x.max() * 1.4]
    izq.plot(lim, lim, color=style.INK_2, lw=1.0, ls="--", zorder=2)
    izq.scatter(x, y, s=34, color=style.PRIMARY, zorder=4,
                edgecolor="white", linewidth=0.6)
    caba = prov[prov["prov_id"] == "02"].iloc[0]
    izq.annotate("CABA", (caba["por_residencia"], caba["serie_historica"]),
                 textcoords="offset points", xytext=(14, -20),
                 fontsize=style.PT_BASE - 1.5, color=style.INK,
                 arrowprops=dict(arrowstyle="-", color=style.INK_2, lw=0.8,
                                 shrinkA=0, shrinkB=3))
    izq.set_xscale("log"); izq.set_yscale("log")
    izq.set_xlim(lim); izq.set_ylim(lim)
    izq.set_xlabel("Nacimientos por residencia de la madre")
    izq.set_ylabel("Serie histórica («ocurridos»)")
    f.nota(izq, "las 24 jurisdicciones\nsobre la diagonal", 0.05, 0.80)
    style.despine(izq)

    # --- panel derecho: tasa por tamaño de localidad -------------------------
    orden = ["<500", "500–1k", "1–2k", "2–5k", "5–10k", "10–20k", "20–50k", ">50k"]
    t = tam.set_index("tamano_localidad").loc[orden]
    xs = np.arange(len(t))
    sin_maternidad = [c in {"<500", "500–1k", "1–2k"} for c in orden]
    colores = [style.ACCENT if s else style.MUTED for s in sin_maternidad]
    colores[-1] = style.PRIMARY
    der.bar(xs, t["tasa"], width=0.7, color=colores, zorder=3)
    for xi, (v, n) in enumerate(zip(t["tasa"], t["futbolistas"])):
        der.text(xi, v + 0.7, f"{int(n)}", ha="center", va="bottom",
                 fontsize=style.PT_BASE - 2, color=style.INK)
    der.axhline(0, color=style.AXIS, lw=0.8)
    der.set_xticks(xs); der.set_xticklabels(orden, rotation=45, ha="right")
    der.set_ylabel("Futbolistas cada 100.000 nacidos")
    der.set_xlabel("Habitantes de la localidad de nacimiento")
    der.set_ylim(0, float(t["tasa"].max()) * 1.28)
    f.nota(der, "naranja = sin maternidad posible.\nLa hipótesis del parto predice "
                "cero acá,\ny predice un escalón, no una pendiente.", 0.04, 0.80)
    style.despine(der)
    f.guardar("fig27_criterio_del_registro", p.figures)


FIGURAS = [fig14_conversion_tramo, fig15_conversion_region, fig16_embudo,
           fig17_seleccion_clubes, fig18_seleccion_migracion,
           fig19_sesgo_denominador, fig20_deciles_sin_gradiente, fig21_funnel,
           fig22_efecto_por_cohorte, fig23_ranking_provincias,
           fig24_sensibilidad_denominador, fig25_matriz_flujo, fig26_retencion,
           fig27_criterio_del_registro]


def main() -> None:
    cfg = load_config()
    p = paths()
    style.apply_style(cfg)
    for fn in FIGURAS:
        try:
            fn(cfg, p)
            log.info("  ok  %s", fn.__name__)
        except Exception as exc:                     # noqa: BLE001
            log.error("  FALLA %s: %s: %s", fn.__name__, type(exc).__name__, exc)
    log.info("figuras en %s", p.figures)


if __name__ == "__main__":
    main()
