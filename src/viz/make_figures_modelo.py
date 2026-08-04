"""Figuras 29 a 32 — covariables, control positivo y sesgo del numerador.

    29  Coeficientes del modelo con covariables, especificación por especificación.
    30  Partición de varianza: cuánto es entre departamentos y cuánto adentro.
    31  Control positivo: el efecto de la edad relativa.
    32  Sesgo de granularidad del `P19` y su cota.

Uso:
    python -m src.viz.make_figures_modelo
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

from src.common import get_logger, load_config, paths
from src.viz import style
from src.viz.style import Figura

log = get_logger("viz.modelo")

FUENTE = ("Fuente: Wikidata (2026-07-30), DEIS (nacidos vivos 1914-2024) e INDEC "
          "(Censo 2022). Elaboración propia.")

ETIQUETA = {
    "log_pob": "Tamaño de la ciudad\n(por e-fold)",
    "log_km": "Distancia al club\nformador (por e-fold)",
    "pct_nbi": "Pobreza estructural\n(por punto de NBI)",
}


def _t(p, nombre):
    return pd.read_csv(p.tables / f"{nombre}.csv")


def fig29_coeficientes(cfg, p):
    """Lo que sobrevive a controlar por lo demás."""
    c = _t(p, "modelo_coeficientes")
    c = c[c["termino"] != "const"].copy()
    orden = ["log_pob", "log_km", "pct_nbi"]
    modelos = sorted(c["modelo"].unique())

    f = Figura(7.0, 4.6,
               "La pobreza estructural pesa más que el tamaño, y absorbe a la distancia",
               "Razón de tasas por cada covariable, según qué otras estén en el "
               "modelo.\nUn valor menor que 1 quiere decir que la producción baja "
               "cuando la variable sube",
               "Binomial negativo con offset de nacidos vivos, sobre 2.950 ciudades "
               "con las tres covariables disponibles. La distancia al club formador "
               "es significativa por sí sola y deja de serlo al entrar el NBI: era "
               "en buena medida un proxy de pobreza.\n" + FUENTE, cfg)
    # La leyenda va en su propia banda: adentro del eje tapaba la fila del NBI.
    ax_leg = f.banda_leyenda(alto_pt=30)
    ax = f.eje(izq=0.13, abajo=0.10)

    colores = {m: style.SERIES[i % len(style.SERIES)] for i, m in enumerate(modelos)}
    y_base = np.arange(len(orden))[::-1]

    # Cada término se dibuja solo con los modelos que lo contienen, repartidos
    # de forma pareja dentro de su fila. Espaciarlos por el índice global del
    # modelo dejaba huecos donde el término no estaba y las filas se leían como
    # si los puntos pertenecieran a categorías distintas.
    for i, term in enumerate(orden):
        presentes = [m for m in modelos
                     if term in set(c[c["modelo"] == m]["termino"])]
        alto = 0.66 / max(len(presentes), 1)
        for j, m in enumerate(presentes):
            r = c[(c["modelo"] == m) & (c["termino"] == term)].iloc[0]
            y = y_base[i] + (j - (len(presentes) - 1) / 2) * alto
            ax.plot([r["IRR_ic_lo"], r["IRR_ic_hi"]], [y, y],
                    color=colores[m], lw=2.0, solid_capstyle="round", zorder=4)
            ax.scatter(r["IRR"], y, s=36, color=colores[m], zorder=6,
                       edgecolors=style.SURFACE, linewidths=1.0)

    ax.axvline(1.0, color=style.INK_2, lw=1.0, ls=(0, (4, 3)), zorder=2)
    ax.text(1.0, -0.46, " sin efecto", ha="left", va="bottom",
            fontsize=6.8, color=style.INK_2)
    ax.set_yticks(y_base, [ETIQUETA[t] for t in orden])
    ax.set_xscale("log")
    ax.set_xticks([0.8, 0.9, 1.0, 1.1, 1.2], ["0,8", "0,9", "1,0", "1,1", "1,2"])
    ax.set_xlabel("Razón de tasas (IRR), escala logarítmica")
    ax.grid(True, axis="x")
    style.despine(ax, izquierda=True)
    ax.tick_params(axis="y", length=0)
    ax.set_ylim(-0.55, len(orden) - 0.45)
    leg = [Line2D([], [], marker="o", ls="-", color=colores[m], ms=6, lw=1.8,
                  label=m) for m in modelos]
    lg = ax_leg.legend(handles=leg, loc="center left", fontsize=6.6, ncols=3,
                       bbox_to_anchor=(0.0, 0.5), columnspacing=1.6,
                       handletextpad=0.6, borderpad=0.0)
    for t_ in lg.get_texts():
        t_.set_color(style.INK_2)
    f.guardar("fig29_coeficientes_covariables", p.figures)


def fig30_varianza(cfg, p):
    v = _t(p, "modelo_multinivel_varianza").iloc[0]
    entre, dentro = float(v["var_entre_departamentos"]), float(v["var_dentro_de_departamento"])
    icc = float(v["icc"])

    f = Figura(6.6, 3.4,
               "El mapa departamental resume mal el fenómeno",
               "De la variación que el modelo no explica, qué parte separa a un "
               "departamento de otro\ny qué parte separa a dos ciudades del mismo "
               "departamento",
               "Descomposición de varianza sobre los residuos de Pearson del modelo "
               "con las tres covariables. No es el ICC de un modelo mixto —no "
               "separa la varianza de muestreo de Poisson— y por eso es una cota "
               "inferior del agrupamiento departamental.\n" + FUENTE, cfg)
    ax = f.eje(izq=0.02, abajo=0.16, arriba=0.10)

    total = entre + dentro
    ax.barh([0], [100 * entre / total], height=0.42, color=style.PRIMARY, zorder=3,
            label="entre departamentos")
    ax.barh([0], [100 * dentro / total], left=[100 * entre / total], height=0.42,
            color=style.MUTED, zorder=3,
            label="entre ciudades del mismo departamento")
    ax.text(100 * entre / total / 2, 0, f"{100 * icc:.0f}%", ha="center",
            va="center", color="#ffffff", fontsize=style.PT_BASE + 1,
            fontweight="bold", zorder=6)
    ax.text(100 * entre / total + 100 * dentro / total / 2, 0,
            f"{100 * (1 - icc):.0f}%", ha="center", va="center", color="#ffffff",
            fontsize=style.PT_BASE + 1, fontweight="bold", zorder=6)

    ax.set_xlim(0, 100)
    ax.set_ylim(-0.5, 0.5)
    ax.set_yticks([])
    ax.set_xlabel("% de la variación residual")
    style.despine(ax, izquierda=True)
    ax.grid(True, axis="x")
    lg = ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.42), ncols=2,
                   fontsize=7.0)
    for t_ in lg.get_texts():
        t_.set_color(style.INK_2)
    f.guardar("fig30_particion_de_varianza", p.figures)


def fig31_edad_relativa(cfg, p):
    d = _t(p, "edad_relativa_trimestres")
    niv = _t(p, "edad_relativa_por_nivel")
    r = _t(p, "edad_relativa_resumen").iloc[0]

    f = Figura(7.0, 4.2,
               "Control positivo: el instrumento sí encuentra sesgos cuando los hay",
               "Efecto de la edad relativa. La AFA agrupa por año calendario, así "
               "que nacer en enero\nda casi un año de ventaja sobre un compañero de "
               "diciembre",
               "Es el hallazgo más replicado de la literatura sobre desarrollo "
               "deportivo. Que el corpus lo recupere limpio quiere decir que el "
               "gradiente plano por tamaño de ciudad no se explica por falta de "
               "potencia.\nEsperado proporcional a los días de cada trimestre: el "
               "DEIS no publica apertura mensual.\n" + FUENTE, cfg)
    axes = f.ejes_lado_a_lado(2, separacion=0.10, sangria_izq=0.02, abajo=0.11,
                              titulos=["Por trimestre de nacimiento",
                                       "Razón Q1/Q4 según el nivel alcanzado"])

    ax = axes[0]
    x = np.arange(len(d))
    ax.bar(x, d["pct_observado"], width=0.62, color=style.PRIMARY, zorder=3,
           label="observado")
    ax.plot(x, d["pct_esperado"], "o--", color=style.INK_2, lw=1.2, ms=5,
            zorder=6, label="esperado por los días del trimestre")
    for xi, v in zip(x, d["pct_observado"]):
        ax.text(xi, v + 0.9, f"{v:.1f}%", ha="center", va="bottom",
                fontsize=style.PT_BASE - 1.5, color=style.INK)
    ax.set_xticks(x, ["Q1\nene-mar", "Q2\nabr-jun", "Q3\njul-sep", "Q4\noct-dic"])
    ax.set_ylabel("% de los futbolistas")
    ax.set_ylim(0, max(d["pct_observado"]) * 1.22)
    ax.grid(True, axis="y")
    style.despine(ax)
    lg = ax.legend(loc="upper right", fontsize=6.6)
    for t_ in lg.get_texts():
        t_.set_color(style.INK_2)

    ax = axes[1]
    nombres = {"T1_seleccion": "Selección\nmayor", "T2_europa_top": "Europa\ntop",
               "T3_primera_ar": "Primera\nargentina", "T4_resto": "Resto"}
    niv = niv.sort_values("razon_Q1_Q4", ascending=False)
    y = np.arange(len(niv))[::-1]
    ax.barh(y, niv["razon_Q1_Q4"], height=0.6, color=style.ACCENT, zorder=3)
    for yi, (v, n) in zip(y, zip(niv["razon_Q1_Q4"], niv["n"])):
        ax.text(v + 0.05, yi, f"{v:.2f}   (n = {int(n)})", va="center", ha="left",
                fontsize=style.PT_BASE - 1.5, color=style.INK)
    ax.axvline(1.0, color=style.INK_2, lw=1.0, ls=(0, (4, 3)), zorder=2)
    ax.set_yticks(y, [nombres.get(t_, t_) for t_ in niv["tier"]])
    ax.set_xlim(0, niv["razon_Q1_Q4"].max() * 1.42)
    ax.set_xlabel("Nacidos en Q1 por cada uno nacido en Q4")
    ax.grid(True, axis="x")
    style.despine(ax, izquierda=True)
    ax.tick_params(axis="y", length=0)
    f.nota(ax, f"χ²(3) = {r['chi2']:.0f}   ·   Q1/Q4 global = {r['razon_Q1_sobre_Q4']:.2f}",
           0.03, 0.04, fontsize=6.8)
    f.guardar("fig31_edad_relativa", p.figures)


def fig32_granularidad(cfg, p):
    g = _t(p, "granularidad_por_region")
    c = _t(p, "granularidad_cota").iloc[0]
    g = g.sort_values("sobrerrepresentacion", ascending=False)

    f = Figura(7.0, 4.3,
               "A los jugadores del norte Wikidata les anota la provincia, no el pueblo",
               "Composición regional de los futbolistas según con qué precisión "
               "está cargado su lugar\nde nacimiento. Los de precisión gruesa "
               "quedan fuera del análisis de tamaño de ciudad",
               "Si la exclusión fuera aleatoria, las dos columnas coincidirían. "
               "χ²(5) = 72,9; p < 10⁻¹³.\n" + FUENTE, cfg)
    axes = f.ejes_lado_a_lado(2, separacion=0.11, sangria_izq=0.03, abajo=0.11,
                              titulos=["Composición según la precisión del P19",
                                       "Qué tan lejos puede mover el resultado"])

    ax = axes[0]
    y = np.arange(len(g))[::-1]
    ax.barh(y + 0.19, g["pct_P19_provincia"], height=0.36, color=style.ACCENT,
            zorder=3, label="P19 = provincia (excluidos)")
    ax.barh(y - 0.19, g["pct_P19_localidad"], height=0.36, color=style.PRIMARY,
            zorder=3, label="P19 = localidad (analizados)")
    for yi, (a, b_) in zip(y, zip(g["pct_P19_provincia"], g["pct_P19_localidad"])):
        ax.text(max(a, b_) + 1.2, yi, f"×{a / b_:.1f}" if b_ else "—", va="center",
                ha="left", fontsize=style.PT_BASE - 1.5, color=style.INK)
    ax.set_yticks(y, list(g["region"]))
    ax.set_xlim(0, max(g["pct_P19_localidad"].max(), g["pct_P19_provincia"].max()) * 1.28)
    ax.set_xlabel("% de los jugadores del grupo")
    ax.grid(True, axis="x")
    style.despine(ax, izquierda=True)
    ax.tick_params(axis="y", length=0)
    lg = ax.legend(loc="lower right", fontsize=6.6)
    for t_ in lg.get_texts():
        t_.set_color(style.INK_2)

    ax = axes[1]
    vals = [float(c["RR_publicado"]), float(c["RR_cota"])]
    ax.bar([0, 1], vals, width=0.5, color=[style.PRIMARY, style.MUTED], zorder=3)
    for xi, v in zip([0, 1], vals):
        ax.text(xi, v + 0.02, f"{v:.2f}", ha="center", va="bottom",
                fontsize=style.PT_BASE, color=style.INK, fontweight="bold")
    ax.axhline(1.0, color=style.INK_2, lw=1.0, ls=(0, (4, 3)), zorder=2)
    # A la izquierda del eje: contra el borde derecho se montaba sobre la
    # etiqueta de valor de la barra de la cota, que llega casi hasta 1,0.
    ax.text(-0.50, 1.005, "sin efecto", ha="left", va="bottom", fontsize=6.8,
            color=style.INK_2)
    ax.set_xticks([0, 1], ["publicado", f"cota:\ntodos los {int(c['excluidos_total'])}\nal tramo <10k"])
    ax.set_xlim(-0.55, 1.55)
    ax.set_ylim(0, 1.18)
    ax.set_ylabel("RR  <10k vs >500k")
    ax.grid(True, axis="y")
    style.despine(ax)
    f.guardar("fig32_sesgo_granularidad", p.figures)


def fig33_punto_de_quiebre(cfg, p):
    """Cuánta mala clasificación haría falta para que el hallazgo se caiga."""
    d = _t(p, "correccion_p19_curva")
    rompe = d[~d["sigue_distinguible_de_1"]]
    umbral = float(rompe["err_metropoli"].iloc[0]) if len(rompe) else None

    f = Figura(7.0, 4.3,
               "Cuánto tendría que fallar el dato para que el hallazgo se caiga",
               "RR corregido según qué proporción de los registrados en un gran "
               "aglomerado\nhubiera nacido en realidad fuera de él —el artefacto de "
               "la maternidad de cabecera",
               "Simulación sobre la muestra de validación de 300 casos; banda del "
               "95% por bootstrap. No es una estimación del error real: es la "
               "calibración de cuánto error haría falta. Medirlo es lo que queda "
               "pendiente (docs/plan-validacion-p19.md).\n" + FUENTE, cfg)
    ax = f.eje(izq=0.02, abajo=0.11)

    x = 100 * d["err_metropoli"]
    ax.fill_between(x, d["ic_lo"], d["ic_hi"], color=style.PRIMARY, alpha=0.16,
                    zorder=2, label="IC 95% del RR corregido")
    ax.plot(x, d["RR_corregido"], "-o", color=style.PRIMARY, lw=2.0, ms=5,
            markeredgecolor=style.SURFACE, markeredgewidth=1.1, zorder=6,
            label="RR corregido")
    ax.axhline(1.0, color=style.INK_2, lw=1.1, ls=(0, (4, 3)), zorder=4)
    # A la izquierda: la curva cruza el 1 cerca del extremo derecho y ahí el
    # rótulo queda encima de la línea.
    ax.text(1.0, 1.02, "sin efecto", ha="left", va="bottom", fontsize=6.9,
            color=style.INK_2)

    if umbral is not None:
        ax.axvline(100 * umbral, color=style.ACCENT, lw=1.4, zorder=5)
        ax.text(100 * umbral + 1.0, ax.get_ylim()[0] + 0.06,
                f"a partir de acá el intervalo\ntoca el 1: {100 * umbral:.0f}%",
                ha="left", va="bottom", fontsize=7.0, color=style.ACCENT,
                fontweight="bold")

    ax.set_xlabel("% de los registrados en un gran aglomerado que en realidad "
                  "nació fuera de él")
    ax.set_ylabel("RR  <10k vs >500k, corregido")
    ax.set_xlim(-1, x.max() + 1)
    ax.grid(True, axis="y")
    style.despine(ax)
    lg = ax.legend(loc="upper left", fontsize=6.9)
    for t_ in lg.get_texts():
        t_.set_color(style.INK_2)
    f.guardar("fig33_punto_de_quiebre", p.figures)


FIGURAS = [fig29_coeficientes, fig30_varianza, fig31_edad_relativa,
           fig32_granularidad, fig33_punto_de_quiebre]


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


if __name__ == "__main__":
    main()
