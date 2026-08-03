"""Fase 6 — Todas las figuras del paper, en `outputs/figures/`.

Cada figura se arma con `style.Figura`, que reserva bandas fijas para el título,
la bajada y el pie, y calcula el área de dibujo con lo que queda. Nada de
`bbox_inches="tight"`: el recorte automático era lo que rompía el espacio
reservado y hacía que los títulos se montaran sobre los gráficos.

Uso:
    python -m src.viz.make_figures
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
from matplotlib.colors import to_hex
from matplotlib.lines import Line2D

from src.analysis.stats import poisson_rate_ci
from src.common import get_logger, load_config, paths
from src.viz import maps, style
from src.viz.style import Figura, miles
from src.denominadores import cargar_ciudades

log = get_logger("viz")

FUENTE = "Fuente: Wikidata (2026-07-30), DEIS (nacidos vivos 1914-2024) e INDEC. Elaboración propia."
DENOM = ("Denominador: nacidos vivos de la misma cohorte en el mismo lugar "
         "(dato real por provincia; estimado por departamento, error mediano 9%).")
VENTANA = "Cohortes 1975-2008"


def _cargar(p, nombre):
    return pd.read_csv(p.tables / f"{nombre}.csv")


# --------------------------------------------------------------------------- #
# Mapas
# --------------------------------------------------------------------------- #
def fig01_mapa_tasa(cfg, p):
    dep = pd.read_csv(p.tables / "h2_departamentos.csv", dtype={"unidad": str})
    g = maps.departamentos(cfg).merge(dep, left_on="dept_id", right_on="unidad",
                                      how="left")
    n = int(dep["jugadores"].sum())

    f = Figura(5.4, 7.6,
               "Dónde nace un futbolista argentino",
               f"Futbolistas cada 100.000 nacidos en el mismo departamento\n"
               f"{VENTANA} · {miles(n)} jugadores",
               "Tasas contraídas hacia la media nacional (empirical Bayes "
               "gamma-Poisson): sin contraer, el mapa lo encabeza el ruido de "
               "Poisson de los departamentos chicos.\n"
               f"{DENOM}\n{FUENTE}", cfg)
    # La leyenda va en su propia banda, no dentro del mapa. Dentro competía por
    # el hueco del Pacífico, cuyo ancho depende de la relación de aspecto del
    # área de dibujo, y esa cambia cada vez que crece el pie: terminaba tapando
    # Jujuy y Salta. Es la misma lógica de bandas reservadas del título.
    ax_leg = f.banda_leyenda(alto_pt=20)
    ax = f.eje()
    # Se mapea la tasa contraída, no la cruda: el color tiene que reflejar lo
    # que el dato sostiene, no la varianza de los departamentos chicos.
    cortes = maps.cortes_cuantiles(g["tasa_eb"], cfg["viz"]["n_classes"])
    maps.pintar(ax, g, "tasa_eb", cortes, style.SEQ)
    maps.contorno_provincias(ax, cfg, lw=0.45)
    maps.leyenda_clases(ax_leg, cortes, style.SEQ, "cada 100.000 nacidos",
                        loc="upper left", anchor=(0.0, 1.55), ncol=7)
    f.guardar("fig01_mapa_departamentos_tasa", p.figures)


def fig02_mapa_conteo(cfg, p):
    dep = pd.read_csv(p.tables / "h2_departamentos.csv", dtype={"unidad": str})
    g = maps.departamentos(cfg).merge(dep, left_on="dept_id", right_on="unidad",
                                      how="left")
    f = Figura(5.4, 7.6,
               "Lo mismo, sin corregir por población",
               "Cantidad absoluta de futbolistas nacidos en cada departamento\n"
               f"{VENTANA}",
               "Este mapa dibuja sobre todo dónde vive la gente. El de la Figura 1, "
               "corregido por nacimientos, es el que muestra el patrón.\n" + FUENTE,
               cfg)
    ax_leg = f.banda_leyenda(alto_pt=20)
    ax = f.eje()
    cortes = maps.cortes_cuantiles(g["jugadores"], cfg["viz"]["n_classes"])
    maps.pintar(ax, g, "jugadores", cortes, style.SEQ)
    maps.contorno_provincias(ax, cfg, lw=0.45)
    maps.leyenda_clases(ax_leg, cortes, style.SEQ, "futbolistas",
                        loc="upper left", anchor=(0.0, 1.55), ncol=7)
    f.guardar("fig02_mapa_departamentos_conteo", p.figures)


def fig03_mapa_divergente(cfg, p):
    prov = pd.read_csv(p.tables / "h2_provincias.csv", dtype={"unidad": str})
    g = maps.provincias(cfg).merge(prov.drop(columns=["provincia"]),
                                   left_on="prov_id", right_on="unidad", how="left")
    f = Figura(5.6, 7.6,
               "Qué provincias producen más de lo que les toca",
               "Futbolistas observados ÷ esperados por sus nacimientos\n"
               f"1,0 = exactamente lo esperado · {VENTANA}",
               "Rojo: produce más futbolistas de los que le corresponderían por "
               "sus nacimientos. Azul: menos. Denominador: nacidos vivos reales "
               "por provincia (DEIS).\n" + FUENTE, cfg)
    ax = f.eje(der=0.10)
    norm = style.norma_divergente(g["obs_sobre_esp"].dropna(), centro=1.0)
    colores = [style.SIN_DATO if pd.isna(v) else to_hex(style.DIV(norm(v)))
               for v in g["obs_sobre_esp"]]
    g.plot(ax=ax, color=colores, edgecolor=style.SURFACE, linewidth=0.4)
    ax.set_axis_off()
    ax.set_aspect("equal")

    cax = f.fig.add_axes([0.86, f.piso + 0.16, 0.022, (f.tope - f.piso) * 0.45])
    import matplotlib.pyplot as plt
    cb = f.fig.colorbar(plt.cm.ScalarMappable(cmap=style.DIV, norm=norm), cax=cax)
    cb.set_label("observado / esperado", color=style.INK_2, fontsize=6.8)
    cb.ax.tick_params(labelsize=6.5, color=style.MUTED, labelcolor=style.INK_2)
    cb.outline.set_visible(False)

    for _, r in g.nlargest(3, "obs_sobre_esp").iterrows():
        corto = maps.NOMBRE_CORTO.get(r["provincia"], r["provincia"])
        etiqueta = f"{corto}\n×{r['obs_sobre_esp']:.1f}"
        # CABA es un polígono diminuto: su etiqueta va afuera con guía.
        chico = r["provincia"] in maps.NOMBRE_CORTO
        maps.etiquetar(ax, r.geometry.centroid, etiqueta,
                       dx=42 if chico else 0, dy=18 if chico else 0,
                       color=style.INK if chico else "#ffffff", guia=chico)
    f.guardar("fig03_mapa_provincias_obs_esp", p.figures)


def fig06_cartograma(cfg, p):
    from shapely import affinity
    prov = pd.read_csv(p.tables / "h2_provincias.csv", dtype={"unidad": str})
    g = maps.provincias(cfg).copy()
    g["valor"] = g["prov_id"].map(prov.set_index("unidad")["jugadores"]).fillna(0)
    g["area"] = g.geometry.area
    objetivo = g["valor"] / g["valor"].sum() * g["area"].sum()
    g["factor"] = np.sqrt((objetivo / g["area"]).replace([np.inf, -np.inf], 0)).fillna(0)

    f = Figura(7.2, 6.6,
               "La geografía del talento no es la del territorio",
               "Izquierda: superficie real. Derecha: superficie proporcional a "
               "los futbolistas producidos",
               "Cartograma no contiguo: cada provincia conserva su forma y su "
               "posición, y solo cambia de tamaño.\n" + FUENTE, cfg)
    izq, der = f.ejes_lado_a_lado(2, separacion=0.02,
                                  titulos=["Territorio real",
                                           "Futbolistas producidos"])

    g.plot(ax=izq, color="#dde6f1", edgecolor=style.SURFACE, linewidth=0.4)
    g.plot(ax=der, color=style.SIN_DATO, edgecolor="none")
    escaladas = g.copy()
    escaladas["geometry"] = [affinity.scale(geom, xfact=fa, yfact=fa, origin="centroid")
                             for geom, fa in zip(g.geometry, g["factor"])]
    escaladas.plot(ax=der, color=style.PRIMARY, edgecolor=style.SURFACE,
                   linewidth=0.4, alpha=0.92)
    for _, r in g.nlargest(3, "valor").iterrows():
        c = escaladas.loc[escaladas["prov_id"] == r["prov_id"], "geometry"].iloc[0].centroid
        corto = maps.NOMBRE_CORTO.get(r["provincia"], r["provincia"])
        maps.etiquetar(der, c, f"{corto}\n{int(r['valor'])}", color="#ffffff", size=6.5)

    for ax in (izq, der):
        ax.set_axis_off()
        ax.set_aspect("equal")
        ax.set_xlim(*izq.get_xlim())
        ax.set_ylim(*izq.get_ylim())
    f.guardar("fig06_cartograma_provincias", p.figures)


def fig08_flujos(cfg, p):
    players = pd.read_parquet(p.processed / "player_level.parquet")
    clubs = pd.read_parquet(p.interim / "clubs_resolved.parquet")
    m = players.merge(clubs[["team_qid", "club_prov_id", "club_en_argentina"]],
                      left_on="primer_club_qid", right_on="team_qid", how="left")
    m = m[m["club_en_argentina"].fillna(False).infer_objects(copy=False)
          & m["prov_id"].notna()]
    flujo = (m[m["prov_id"] != m["club_prov_id"]]
             .groupby(["prov_id", "club_prov_id"]).size().rename("n").reset_index())
    saldo = (m.groupby("club_prov_id").size().rename("llegan").to_frame()
             .join(m.groupby("prov_id").size().rename("salen"), how="outer").fillna(0))
    saldo["neto"] = saldo["llegan"] - saldo["salen"]

    g = maps.provincias(cfg).set_index("prov_id")
    cent = g.geometry.centroid

    f = Figura(5.8, 7.8,
               "El talento nace repartido y se forma concentrado",
               "Flujos entre la provincia de nacimiento y la del club formador\n"
               f"{miles(len(m))} futbolistas con club formador ubicado en Argentina",
               "Solo se dibujan los flujos ENTRE provincias. Club formador = el "
               "vínculo jugador-club más temprano con fecha en Wikidata; es un "
               "proxy y suele ser el club de debut, no el de inferiores.\n" + FUENTE,
               cfg)
    # La leyenda va en su propia banda: dentro del mapa, las curvas de flujo de
    # la Patagonia le pasaban por encima.
    ax_leg = f.banda_leyenda(alto_pt=22)
    ax = f.eje()
    g.plot(ax=ax, color="#eceae4", edgecolor=style.SURFACE, linewidth=0.5, zorder=1)

    vmax = flujo["n"].max()
    for r in flujo.sort_values("n").itertuples():
        if r.prov_id not in cent.index or r.club_prov_id not in cent.index:
            continue
        x0, y0 = cent[r.prov_id].x, cent[r.prov_id].y
        x1, y1 = cent[r.club_prov_id].x, cent[r.club_prov_id].y
        # Bezier cuadrática: el arco separa la ida de la vuelta del mismo par.
        cx = (x0 + x1) / 2 - (y1 - y0) * 0.18
        cy = (y0 + y1) / 2 + (x1 - x0) * 0.18
        t = np.linspace(0, 1, 60)[:, None]
        pts = ((1 - t) ** 2 * np.array([x0, y0]) + 2 * (1 - t) * t * np.array([cx, cy])
               + t ** 2 * np.array([x1, y1]))
        peso = r.n / vmax
        ax.plot(pts[:, 0], pts[:, 1], lw=0.35 + 3.0 * peso ** 0.65,
                color=to_hex(style.SEQ(0.35 + 0.6 * peso ** 0.5)), alpha=0.85,
                solid_capstyle="round", zorder=3)

    neto = saldo["neto"].reindex(cent.index).fillna(0)
    tam = np.abs(neto) / max(np.abs(neto).max(), 1)
    ax.scatter(cent.x, cent.y, s=16 + 560 * tam, zorder=6,
               color=[style.ACCENT if v > 0 else "#ffffff" for v in neto],
               edgecolors=style.INK_2, linewidths=0.7)
    for prov in neto.abs().nlargest(3).index:
        nombre = maps.NOMBRE_CORTO.get(g.loc[prov, "provincia"], g.loc[prov, "provincia"])
        maps.etiquetar(ax, cent[prov], f"{nombre}\n{int(neto[prov]):+d}",
                       dx=14 + 26 * float(tam[prov]) ** 0.5, dy=-2, guia=False,
                       color=style.INK, size=6.8)
    ax.set_axis_off()
    ax.set_aspect("equal")

    leg = [Line2D([], [], color=to_hex(style.SEQ(0.9)), lw=3.0,
                  label=f"flujo entre provincias (hasta {int(vmax)})"),
           Line2D([], [], marker="o", ls="", markerfacecolor=style.ACCENT,
                  markeredgecolor=style.INK_2, ms=9, label="recibe más de los que pierde"),
           Line2D([], [], marker="o", ls="", markerfacecolor="#ffffff",
                  markeredgecolor=style.INK_2, ms=9, label="pierde más de los que recibe")]
    lg = ax_leg.legend(handles=leg, loc="center left", fontsize=6.8, ncols=1,
                       bbox_to_anchor=(0.0, 0.5), handletextpad=0.7,
                       labelspacing=0.55, borderpad=0.0)
    for t_ in lg.get_texts():
        t_.set_color(style.INK_2)
    f.guardar("fig08_flujos_nacimiento_club", p.figures)


# --------------------------------------------------------------------------- #
# Barras
# --------------------------------------------------------------------------- #
def _barras(ax, etiquetas, valores, lo=None, hi=None, color=style.PRIMARY,
            sufijo="", destacar=None):
    y = np.arange(len(etiquetas))
    colores = [color] * len(etiquetas)
    if destacar is not None:
        colores = [color if i in destacar else "#bcd3ef" for i in range(len(etiquetas))]
    ax.barh(y, valores, height=0.62, color=colores, zorder=3)
    tope = float(np.max(hi if hi is not None else valores))
    if lo is not None:
        ax.errorbar(valores, y, xerr=[valores - lo, hi - valores], fmt="none",
                    ecolor=style.INK_2, elinewidth=1.0, capsize=2.0, zorder=4)
    ax.set_yticks(y, etiquetas)
    ax.invert_yaxis()
    ax.xaxis.grid(True)
    style.despine(ax, izquierda=True)
    ax.tick_params(axis="y", length=0)
    margen = tope * 0.025
    ref = hi if hi is not None else valores
    for yi, v, h in zip(y, valores, ref):
        ax.text(h + margen, yi, f"{v:,.1f}{sufijo}".replace(",", "."), va="center",
                ha="left", fontsize=7.5, color=style.INK)
    ax.set_xlim(0, tope * 1.20)


def fig04_tramos(cfg, p):
    t = _cargar(p, "h1_tramos_principal")
    f = Figura(6.4, 3.6,
               "Cuanto más grande la ciudad, más futbolistas por nacido",
               "Lo contrario de lo que predice la literatura internacional, que "
               "espera un pico en\nlas ciudades de 50.000 a 100.000 habitantes",
               "Barras de error: IC 95% exacto de Poisson. «Ciudad» = el aglomerado "
               f"urbano cuando la localidad forma parte de uno. {VENTANA}.\n"
               f"{DENOM}\n{FUENTE}", cfg)
    ax = f.eje(izq=0.06, abajo=0.09)
    _barras(ax, t["unidad"], t["tasa"].values, t["tasa_ic_lo"].values,
            t["tasa_ic_hi"].values, destacar={0, 4})
    ax.set_xlabel("Futbolistas cada 100.000 nacidos")
    ax.set_ylabel("Tamaño de la ciudad")
    f.guardar("fig04_tasa_por_tramo", p.figures)


def fig05_regiones(cfg, p):
    t = _cargar(p, "h2_regiones").sort_values("tasa", ascending=False)
    f = Figura(6.4, 3.6,
               "El AMBA y la Pampa producen tres veces más que el norte",
               f"Futbolistas cada 100.000 nacidos, por región · {VENTANA}",
               "AMBA = CABA + 24 partidos del Gran Buenos Aires. Barras de error: "
               f"IC 95% exacto de Poisson.\n{DENOM}\n{FUENTE}", cfg)
    ax = f.eje(izq=0.06, abajo=0.09)
    _barras(ax, t["unidad"], t["tasa"].values, t["tasa_ic_lo"].values,
            t["tasa_ic_hi"].values, destacar={0, 1})
    ax.set_xlabel("Futbolistas cada 100.000 nacidos")
    f.guardar("fig05_tasa_por_region", p.figures)


def fig09_migracion(cfg, p):
    t = _cargar(p, "h3_migracion_por_tamano_origen")
    f = Figura(6.6, 3.6,
               "Solo desde las ciudades grandes se llega sin mudarse",
               "Porcentaje que se forma en otra provincia, y distancia mediana "
               "hasta el club formador",
               "El corte está entre los aglomerados de más de 500.000 habitantes y "
               "todo lo demás; entre el resto de los tramos no hay gradiente. En la "
               "población general, el 13,8% vive fuera de su provincia de nacimiento "
               "(Censo 2022, variable P14).\n" + FUENTE, cfg)
    ax = f.eje(izq=0.06, abajo=0.09)
    y = np.arange(len(t))
    ax.barh(y, t["pct_cambia_provincia"], height=0.62, zorder=3,
            color=[style.PRIMARY if v < 45 else "#bcd3ef"
                   for v in t["pct_cambia_provincia"]])
    ax.set_yticks(y, t["tramo"])
    ax.invert_yaxis()
    ax.xaxis.grid(True)
    style.despine(ax, izquierda=True)
    ax.tick_params(axis="y", length=0)
    for yi, v, km in zip(y, t["pct_cambia_provincia"], t["km_mediana"]):
        ax.text(v + 1.6, yi, f"{v:.0f}%   ·   {km:.0f} km", va="center", ha="left",
                fontsize=7.5, color=style.INK)
    ax.set_xlim(0, 100)
    ax.set_xlabel("% que se forma en otra provincia")
    ax.set_ylabel("Tamaño de la ciudad de nacimiento")
    f.guardar("fig09_migracion_por_tamano", p.figures)


# --------------------------------------------------------------------------- #
def fig07_scatter(cfg, p):
    players = pd.read_parquet(p.processed / "analysis_players.parquet")
    ciudades = cargar_ciudades(p)
    conteo = players.groupby("ciudad_id").size().rename("jugadores")
    d = ciudades.set_index("ciudad_id").join(conteo).fillna({"jugadores": 0})
    d = d[(d["nacimientos_cohorte"] > 0) & (d["pob_ciudad"] > 0)].copy()
    d["tasa"] = 1e5 * d["jugadores"] / d["nacimientos_cohorte"]

    f = Figura(6.8, 4.2,
               "El tamaño de la ciudad explica el 1% de la variación",
               "Tamaño de la ciudad de nacimiento contra futbolistas cada 100.000 "
               "nacidos.\nLa tendencia sube, pero la dispersión a cada tamaño es "
               "mucho mayor que el efecto",
               "Se dibujan TODAS las ciudades del ajuste. Las que tienen menos de "
               "5.000 nacidos en la cohorte van en tono claro: con esa base un solo "
               "jugador ya da tasas de tres dígitos.\n" + FUENTE, cfg)
    ax = f.eje(izq=0.02, abajo=0.10)

    # Antes el scatter excluía las ciudades chicas y el ajuste las usaba: la nube
    # que se veía y el modelo cuya recta se le superponía no eran la misma
    # muestra. Ahora se dibujan todas y las de poca base se distinguen por tono.
    con_jugadores = d[d["jugadores"] > 0]
    chicas = con_jugadores[con_jugadores["nacimientos_cohorte"] < 5000]
    grandes = con_jugadores[con_jugadores["nacimientos_cohorte"] >= 5000]
    ax.scatter(chicas["pob_ciudad"], chicas["tasa"], s=5, color=style.MUTED,
               alpha=0.30, linewidths=0, zorder=2,
               label="ciudad con menos de 5.000 nacidos (tasa muy imprecisa)")
    ax.scatter(grandes["pob_ciudad"], grandes["tasa"],
               s=np.clip(grandes["pob_ciudad"] / 6000, 5, 70), color=style.PRIMARY,
               alpha=0.28, linewidths=0, zorder=3,
               label="una ciudad (área según su población)")

    d["decil"] = pd.qcut(np.log(d["pob_ciudad"]), 10, labels=False, duplicates="drop")
    agg = d.groupby("decil").agg(j=("jugadores", "sum"),
                                 n=("nacimientos_cohorte", "sum"),
                                 tam=("pob_ciudad", "median"))
    r, lo, hi = poisson_rate_ci(agg["j"], agg["n"])
    ax.errorbar(agg["tam"], r, yerr=[r - lo, hi - r], fmt="o", ms=5.5,
                color=style.ACCENT, ecolor=style.ACCENT, elinewidth=1.2, capsize=2.5,
                markeredgecolor=style.SURFACE, markeredgewidth=1.2, zorder=6,
                label="tasa agregada por decil de tamaño (IC 95%)")

    X = sm.add_constant(np.log(d["pob_ciudad"]))
    fam = sm.families.NegativeBinomial(alpha=1.0)
    off = np.log(d["nacimientos_cohorte"])
    fit = sm.GLM(d["jugadores"], X, family=fam, offset=off).fit()
    nulo = sm.GLM(d["jugadores"], np.ones((len(d), 1)), family=fam, offset=off).fit()
    pseudo_r2 = 1 - fit.llf / nulo.llf
    xs = np.linspace(np.log(d["pob_ciudad"].min()), np.log(d["pob_ciudad"].max()), 120)
    ax.plot(np.exp(xs), 1e5 * np.exp(fit.params.iloc[0] + fit.params.iloc[1] * xs),
            color=style.INK, lw=1.7, zorder=7, label="ajuste binomial negativo")

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_ylim(2, 400)
    fuera = int((con_jugadores["tasa"] > 400).sum())
    ax.grid(True, which="major")
    style.despine(ax)
    ax.set_xlabel("Población de la ciudad de nacimiento (escala logarítmica)")
    ax.set_ylabel("Futbolistas cada 100.000 nacidos")
    # El tamaño de efecto va en la figura: la pendiente es real y es chica, y sin
    # este número la recta negra sugiere una capacidad predictiva que no tiene.
    f.nota(ax, f"pseudo-R² de McFadden = {pseudo_r2:.3f}\n"
               f"IRR por e-fold de tamaño = {np.exp(fit.params.iloc[1]):.3f}\n"
               f"{fuera} ciudades quedan arriba del eje",
           0.015, 0.045, fontsize=6.8)
    lg = ax.legend(loc="lower right", fontsize=6.8, borderpad=0.6)
    for t_ in lg.get_texts():
        t_.set_color(style.INK_2)
    f.guardar("fig07_scatter_tamano_tasa", p.figures)


# --------------------------------------------------------------------------- #
# Fútbol
# --------------------------------------------------------------------------- #
def fig10_clubes(cfg, p):
    t = _cargar(p, "futbol_clubes_formadores").head(14).copy()
    # Nombres de hincha: los oficiales no entran en el eje.
    CORTOS = {
        "Club Estudiantes de La Plata": "Estudiantes",
        "Club Atlético San Lorenzo de Almagro": "San Lorenzo",
        "Club de Gimnasia y Esgrima La Plata": "Gimnasia (LP)",
        "Club Atlético Newell's Old Boys": "Newell's",
        "Club Atlético Newell’s Old Boys": "Newell's",
        "Club Atlético Vélez Sarsfield": "Vélez",
        "Asociación Atlética Argentinos Juniors": "Argentinos",
        "Club Atlético Rosario Central": "Rosario Central",
        "Club Atlético River Plate": "River Plate",
        "Club Atlético Independiente": "Independiente",
        "Club Atlético Banfield": "Banfield",
        "Club Atlético Lanús": "Lanús",
        "Club Atlético Huracán": "Huracán",
        "Racing Club": "Racing",
    }
    t["nombre"] = t["primer_club"].map(
        lambda s_: CORTOS.get(s_, s_.replace("Club Atlético ", "")
                              .replace("Asociación Atlética ", "")
                              .replace("Club ", "")))

    f = Figura(7.2, 5.0,
               "Los que forman en el barrio y los que traen de todo el país",
               "Jugadores formados por club y distancia mediana entre su lugar de "
               "nacimiento y el club",
               "Solo clubes argentinos con al menos 10 jugadores formados. Club "
               "formador = el vínculo jugador-club más temprano con fecha en "
               "Wikidata.\n" + FUENTE, cfg)
    izq, der = f.ejes_lado_a_lado(
        2, separacion=0.10, sangria_izq=0.12, abajo=0.06,
        titulos=["Jugadores formados", "Distancia mediana al nacimiento"])

    y = np.arange(len(t))
    izq.barh(y, t["formados"], height=0.62, color=style.PRIMARY, zorder=3)
    izq.set_yticks(y, t["nombre"])
    izq.invert_yaxis()
    izq.xaxis.grid(True)
    style.despine(izq, izquierda=True)
    izq.tick_params(axis="y", length=0)
    for yi, v in zip(y, t["formados"]):
        izq.text(v + 3, yi, f"{int(v)}", va="center", ha="left", fontsize=7.5,
                 color=style.INK)
    izq.set_xlim(0, t["formados"].max() * 1.18)
    der.barh(y, t["km_mediana"], height=0.62, zorder=3,
             color=[style.ACCENT if v > 100 else "#f3c0aa" for v in t["km_mediana"]])
    der.set_yticks(y, [""] * len(t))
    der.invert_yaxis()
    der.xaxis.grid(True)
    style.despine(der, izquierda=True)
    der.tick_params(axis="y", length=0)
    for yi, v, pct in zip(y, t["km_mediana"], t["pct_de_otra_provincia"]):
        der.text(v + t["km_mediana"].max() * 0.03, yi,
                 f"{v:.0f} km · {pct:.0f}% de otra prov.", va="center", ha="left",
                 fontsize=7, color=style.INK)
    der.set_xlim(0, t["km_mediana"].max() * 1.75)
    f.guardar("fig10_clubes_formadores", p.figures)


def fig11_cunas(cfg, p):
    t = _cargar(p, "futbol_cunas_ciudades").head(15)
    f = Figura(6.8, 4.6,
               "Las cunas: dónde nacen más futbolistas por nacido",
               "Ciudades con al menos 30 futbolistas en la muestra, ordenadas por "
               f"tasa · {VENTANA}",
               "Se excluyen las ciudades con menos de 30 futbolistas: con tres "
               "jugadores nacidos en un pueblo chico la tasa encabeza cualquier "
               f"ranking sin significar nada.\n{DENOM}\n{FUENTE}", cfg)
    # Sangría amplia: "San Nicolás de los Arroyos" mide más de una pulgada y
    # los rótulos del eje y se dibujan por fuera de la caja del eje.
    ax = f.eje(izq=0.20, abajo=0.08)
    etiquetas = [str(r.ciudad_nombre).replace("Santiago del Estero - La Banda",
                                              "Sgo. del Estero")
                 for r in t.itertuples()]
    _barras(ax, etiquetas, t["tasa"].values, t["tasa_ic_lo"].values,
            t["tasa_ic_hi"].values, destacar={0, 1, 2})
    ax.set_xlabel("Futbolistas cada 100.000 nacidos")
    f.guardar("fig11_cunas_ciudades", p.figures)


def fig12_censura(cfg, p):
    t = _cargar(p, "diagnostico_censura_cohortes")
    f = Figura(6.6, 3.6,
               "Qué se puede leer de cada cohorte, y qué no",
               "Futbolistas cada 100.000 nacidos, por quinquenio de nacimiento",
               "La caída de las dos últimas cohortes no es un fenómeno: quien nació "
               "en 2005 tenía 17 años en 2022 y en su mayoría todavía no debutó. "
               "La caída de la primera es cobertura: Wikidata registra peor a los "
               "jugadores más viejos.\n" + FUENTE, cfg)
    ax = f.eje(izq=0.02, abajo=0.09)
    x = np.arange(len(t))
    censurada = t["quinquenio"] > cfg["cohorts"]["career_complete_max"] - 5
    ax.bar(x, t["tasa"], width=0.66, zorder=3,
           color=[style.SIN_DATO if c else style.PRIMARY for c in censurada])
    ax.errorbar(x, t["tasa"], yerr=[t["tasa"] - t["tasa_ic_lo"],
                                    t["tasa_ic_hi"] - t["tasa"]],
                fmt="none", ecolor=style.INK_2, elinewidth=1.0, capsize=2.0, zorder=4)
    ax.set_xticks(x, [f"{int(q)}–{int(q)+4}" for q in t["quinquenio"]])
    ax.yaxis.grid(True)
    style.despine(ax)
    ax.set_ylabel("Futbolistas cada 100.000 nacidos")
    for xi, v, c in zip(x, t["tasa"], censurada):
        ax.text(xi, v + 1.2, f"{v:.0f}", ha="center", va="bottom", fontsize=7.5,
                color=style.MUTED if c else style.INK)
    ax.set_ylim(0, t["tasa_ic_hi"].max() * 1.18)
    lg = ax.legend(handles=[
        Line2D([], [], marker="s", ls="", markerfacecolor=style.PRIMARY,
               markeredgecolor="none", ms=8, label="carrera plausiblemente iniciada"),
        Line2D([], [], marker="s", ls="", markerfacecolor=style.SIN_DATO,
               markeredgecolor=style.AXIS, ms=8, label="censurada por edad")],
        loc="upper left", fontsize=6.8)
    for t_ in lg.get_texts():
        t_.set_color(style.INK_2)
    f.guardar("fig12_censura_por_cohorte", p.figures)


def fig13_seleccion(cfg, p):
    tramo = _cargar(p, "futbol_seleccion_por_tramo")
    region = _cargar(p, "futbol_seleccion_por_region")
    f = Figura(7.2, 4.0,
               "El mismo patrón entre los que llegan a la selección",
               "Jugadores de la selección mayor por cada millón de nacidos. Es el "
               "control del sesgo de\ncobertura: de la selección, Wikidata tiene "
               "registro prácticamente completo",
               "Si el patrón geográfico fuera un artefacto de qué jugadores tienen "
               "artículo en Wikidata, aquí no debería aparecer.\n"
               f"{DENOM}\n{FUENTE}", cfg)
    izq, der = f.ejes_lado_a_lado(
        2, separacion=0.13, sangria_izq=0.07, abajo=0.14,
        titulos=["Por tamaño de la ciudad", "Por región"])

    for ax, t, etiqueta in (
            (izq, tramo, "tramo"),
            (der, region.sort_values("por_millon", ascending=False), "region")):
        y = np.arange(len(t))
        ax.barh(y, t["por_millon"], height=0.6, color=style.PRIMARY, zorder=3)
        ax.errorbar(t["por_millon"], y,
                    xerr=[t["por_millon"] - t["ic_lo"], t["ic_hi"] - t["por_millon"]],
                    fmt="none", ecolor=style.INK_2, elinewidth=1.0, capsize=2.0,
                    zorder=4)
        ax.set_yticks(y, t[etiqueta])
        ax.invert_yaxis()
        ax.xaxis.grid(True)
        style.despine(ax, izquierda=True)
        ax.tick_params(axis="y", length=0)
        for yi, v, h in zip(y, t["por_millon"], t["ic_hi"]):
            ax.text(h + t["ic_hi"].max() * 0.03, yi, f"{v:.0f}", va="center",
                    ha="left", fontsize=7.5, color=style.INK)
        ax.set_xlim(0, t["ic_hi"].max() * 1.25)
        ax.set_xlabel("por millón de nacidos")
    f.guardar("fig13_seleccion", p.figures)


# --------------------------------------------------------------------------- #
def main() -> None:
    cfg = load_config()
    p = paths()
    style.apply_style(cfg)

    for fn in (fig01_mapa_tasa, fig02_mapa_conteo, fig03_mapa_divergente,
               fig04_tramos, fig05_regiones, fig06_cartograma, fig07_scatter,
               fig08_flujos, fig09_migracion, fig10_clubes, fig11_cunas,
               fig12_censura, fig13_seleccion):
        fn(cfg, p)
        log.info("  %s", fn.__name__)

    log.info("listo: %d figuras", len(sorted(p.figures.glob("*.pdf"))))


if __name__ == "__main__":
    main()
