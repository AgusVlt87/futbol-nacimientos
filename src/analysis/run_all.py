"""Fase 5 — Análisis completo. Exporta todas las tablas a `outputs/tables/`.

El denominador es el número de **nacidos vivos** de cada cohorte en cada lugar,
así que la tasa se lee directo: de cada 100.000 bebés nacidos en Santa Fe entre
1970 y 2008, tantos llegaron a futbolistas profesionales.

Cada hipótesis se responde con conteo observado, esperado por la distribución
real de nacimientos, tasa con IC exacto de Poisson, razón de tasas contra una
referencia declarada y un test de bondad de ajuste con su tamaño de efecto.
Nunca un p-valor solo.

Uso:
    python -m src.analysis.run_all
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats as st

from src.analysis.stats import (
    add_rate_columns,
    chi2_gof,
    empirical_bayes_poisson,
    fdr_bh,
    odds_ratio_ci,
    rate_ratio_ci,
    standardized_residuals,
)
from src.clean.geo_units import city_size_series
from src.common import get_logger, load_config, paths
from src.denominadores import cargar_ciudades

log = get_logger("analysis")

PER = 100_000


def _tabla(obs: pd.Series, pob: pd.Series, referencia: str | None,
           level: float) -> pd.DataFrame:
    """Tabla estándar: observado, esperado, tasa+IC y RR contra la referencia.

    La columna de la unidad de análisis siempre sale como `unidad`, para que
    todas las tablas tengan la misma forma y las figuras y el paper puedan
    consumirlas sin casos especiales.
    """
    obs = obs.rename_axis("unidad")
    pob = pob.rename_axis("unidad")
    t = pd.concat([obs.rename("jugadores"), pob.rename("nacimientos")], axis=1).fillna(0)
    t = t[t["nacimientos"] > 0]
    t["pct_jugadores"] = 100 * t["jugadores"] / t["jugadores"].sum()
    t["pct_nacimientos"] = 100 * t["nacimientos"] / t["nacimientos"].sum()
    t["esperado"] = t["jugadores"].sum() * t["nacimientos"] / t["nacimientos"].sum()
    t["obs_sobre_esp"] = t["jugadores"] / t["esperado"]
    t["residuo_estand"] = standardized_residuals(t["jugadores"].values,
                                                 t["nacimientos"].values)
    t = add_rate_columns(t, "jugadores", "nacimientos", per=PER, level=level)

    if referencia is not None and referencia in t.index:
        rk, rn = t.loc[referencia, "jugadores"], t.loc[referencia, "nacimientos"]
        rr = [rate_ratio_ci(k, n, rk, rn, level) for k, n in
              zip(t["jugadores"], t["nacimientos"])]
        t["RR"], t["RR_ic_lo"], t["RR_ic_hi"] = zip(*rr)
        t["RR_referencia"] = referencia
    return t.reset_index()


def _gof(hipotesis: str, variante: str, t: pd.DataFrame) -> dict:
    g = chi2_gof(t["jugadores"].values, t["nacimientos"].values)
    return {"hipotesis": hipotesis, "variante": variante, **g.as_dict()}


# --------------------------------------------------------------------------- #
# Diagnóstico de censura: cuánto se puede leer de cada cohorte
# --------------------------------------------------------------------------- #
def censura_por_cohorte(cfg, players, nac_prov) -> pd.DataFrame:
    """Futbolistas por cada 100.000 nacidos, por quinquenio de nacimiento.

    Es el diagnóstico que hay que mirar antes que nada: la tasa de las cohortes
    más jóvenes no cae porque nazcan menos futbolistas, sino porque todavía no
    debutaron. Sin esta tabla, incluir 2003–2008 en el análisis sería trampa.
    """
    quinquenio = (players["birth_year"] // 5) * 5
    obs = players.groupby(quinquenio).size().rename("jugadores")
    obs.index.name = "quinquenio"
    nac = (nac_prov.assign(quinquenio=lambda d: (d["anio"] // 5) * 5)
           .groupby("quinquenio")["nacimientos"].sum())
    t = pd.concat([obs, nac], axis=1).dropna(subset=["jugadores"])
    t = add_rate_columns(t, "jugadores", "nacimientos", per=PER,
                         level=cfg["stats"]["ci_level"]).reset_index()
    t["pct_del_pico"] = (100 * t["tasa"] / t["tasa"].max()).round(1)
    t["edad_en_2022"] = 2022 - t["quinquenio"] - 4
    t["lectura"] = np.where(
        t["quinquenio"] > cfg["cohorts"]["career_complete_max"] - 5,
        "censurada: muchos todavía no debutaron", "carrera plausiblemente iniciada")
    return t


# --------------------------------------------------------------------------- #
# H1 — tamaño de ciudad
# --------------------------------------------------------------------------- #
def h1_tamano_ciudad(cfg, players, ciudades, tests: list) -> dict[str, pd.DataFrame]:
    level = cfg["stats"]["ci_level"]
    salidas = {}

    for nombre, esquema in cfg["city_size"]["schemes"].items():
        col = f"tramo_{nombre}"
        t = _tabla(players.groupby(col, observed=False).size(),
                   ciudades.groupby(col, observed=False)["nacimientos_cohorte"].sum(),
                   esquema["reference_label"], level)
        t.insert(0, "esquema", nombre)
        salidas[f"h1_tramos_{nombre}"] = t
        tests.append(_gof("H1", f"esquema {nombre}", t))

    # Robustez 1: la localidad aislada en vez del aglomerado urbano. Cambia qué
    # se entiende por "ciudad", que es donde la literatura suele ser ambigua.
    esquema = cfg["city_size"]["schemes"][cfg["city_size"]["default_scheme"]]
    loc = pd.read_parquet(paths().processed / "denom_cohorte_localidad.parquet")
    loc["tramo_loc"] = city_size_series(loc["pob_localidad"], esquema)
    pl = players.copy()
    pl["tramo_loc"] = city_size_series(pl["pob_localidad"], esquema)
    t = _tabla(pl.groupby("tramo_loc", observed=False).size(),
               loc.groupby("tramo_loc", observed=False)["nacimientos_cohorte"].sum(),
               esquema["reference_label"], level)
    salidas["h1_robustez_localidad_sola"] = t
    tests.append(_gof("H1", "unidad = localidad censal (no aglomerado)", t))

    # Robustez 2: solo cohortes con carrera plausiblemente iniciada. Al recortar
    # cohortes hay que recortar el denominador en la misma proporción; si no, la
    # tasa se hunde por construcción y el recorte parece un hallazgo.
    col = f"tramo_{cfg['city_size']['default_scheme']}"
    tope = cfg["cohorts"]["career_complete_max"]
    sub = players[players["birth_year"] <= tope]
    frac = _fraccion_nacimientos(cfg, tope)
    t = _tabla(sub.groupby(col, observed=False).size(),
               ciudades.groupby(col, observed=False)["nacimientos_cohorte"].sum() * frac,
               esquema["reference_label"], level)
    salidas["h1_robustez_carrera_completa"] = t
    tests.append(_gof("H1", f"solo cohortes ≤ {tope}", t))

    return salidas


def _fraccion_nacimientos(cfg, hasta_anio: int) -> float:
    """Qué fracción de los nacimientos de la ventana cae hasta `hasta_anio`."""
    nac = pd.read_parquet(paths().processed / "nacimientos_provincia_anio.parquet")
    y0, y1 = cfg["cohorts"]["analysis_min_year"], cfg["cohorts"]["analysis_max_year"]
    total = nac[nac["anio"].between(y0, y1)]["nacimientos"].sum()
    return nac[nac["anio"].between(y0, hasta_anio)]["nacimientos"].sum() / total


# --------------------------------------------------------------------------- #
# H2 — geografía
# --------------------------------------------------------------------------- #
def h2_geografia(cfg, players, denom_dept, denom_prov, tests: list) -> dict[str, pd.DataFrame]:
    level = cfg["stats"]["ci_level"]
    p = paths()
    salidas = {}

    prov_nombre = (players.dropna(subset=["prov_id"]).drop_duplicates("prov_id")
                          .set_index("prov_id")["prov_nombre"])
    dept_nombre = (players.dropna(subset=["dept_id"]).drop_duplicates("dept_id")
                          .set_index("dept_id")["dept_nombre"])

    # --- región --------------------------------------------------------------
    t = _tabla(players.groupby("region").size(),
               denom_dept.groupby("region")["nacimientos_cohorte"].sum(), "AMBA", level)
    salidas["h2_regiones"] = t
    tests.append(_gof("H2", "regiones", t))

    # --- provincia: nacimientos REALES, sin ningún supuesto ------------------
    t = _tabla(players.groupby("prov_id").size(),
               denom_prov.set_index("prov_id")["nacimientos_cohorte"], "02", level)
    t["provincia"] = t["unidad"].map(prov_nombre)
    salidas["h2_provincias"] = t.sort_values("tasa", ascending=False)
    tests.append(_gof("H2", "provincias (nacidos vivos reales, DEIS)", t))

    # --- provincia: baselines alternativos, para ver cuánto cambia el orden --
    hist = pd.read_parquet(p.processed / "pop_dept_historica.parquet")
    for censo in sorted(hist["censo"].unique()):
        pob = (hist[hist["censo"] == censo]
               .assign(prov_id=lambda d: d["dept_id"].str[:2])
               .groupby("prov_id")["pob"].sum())
        t_h = _tabla(players.groupby("prov_id").size(), pob, "02", level)
        t_h["provincia"] = t_h["unidad"].map(prov_nombre)
        t_h.insert(0, "baseline", f"población total censo {censo}")
        salidas[f"h2_provincias_censo_{censo}"] = t_h.sort_values("tasa", ascending=False)
        tests.append(_gof("H2", f"provincias (baseline: población censo {censo})", t_h))

    nac_p14 = pd.read_parquet(p.processed / "pop_dept_nacprov.parquet")
    nac_p14 = nac_p14[nac_p14["prov_nac_id"] != "99"].groupby("prov_nac_id")["n"].sum()
    t_p14 = _tabla(players.groupby("prov_id").size(), nac_p14, "02", level)
    t_p14["provincia"] = t_p14["unidad"].map(prov_nombre)
    salidas["h2_provincias_baseline_censo_p14"] = t_p14.sort_values("tasa", ascending=False)
    tests.append(_gof("H2", "provincias (baseline: nacidos según censo 2022, P14)", t_p14))

    # --- departamento --------------------------------------------------------
    t = _tabla(players.groupby("dept_id").size(),
               denom_dept.set_index("dept_id")["nacimientos_cohorte"], None, level)
    t["departamento"] = t["unidad"].map(dept_nombre)
    t["provincia"] = t["unidad"].str[:2].map(prov_nombre)
    t["region"] = t["unidad"].map(denom_dept.set_index("dept_id")["region"])
    t["reportable"] = t["jugadores"] >= cfg["cohorts"]["min_n_subgroup"]

    # Tasa contraída hacia la media nacional. El ranking crudo lo encabezan los
    # departamentos con dos jugadores y mil nacimientos, no los productivos; el
    # IC lo muestra pero no corrige el orden. `tasa_eb` es la que hay que mapear
    # y rankear, y `peso_eb` dice cuánto del dato propio conserva cada unidad.
    eb, alpha_eb, beta_eb, peso = empirical_bayes_poisson(
        t["jugadores"].values, t["nacimientos"].values)
    t["tasa_eb"] = eb * cfg["stats"]["rate_per"]
    t["peso_eb"] = peso
    log.info("empirical Bayes departamental: alpha=%.3f beta=%.0f "
             "(equivale a %.0f nacimientos de previa)", alpha_eb, beta_eb, beta_eb)
    salidas["h2_departamentos"] = t.sort_values("tasa_eb", ascending=False)
    tests.append(_gof("H2", "departamentos", t))

    # --- AMBA vs interior ----------------------------------------------------
    es_amba = players["region"].eq("AMBA")
    n_amba = denom_dept[denom_dept["region"].eq("AMBA")]["nacimientos_cohorte"].sum()
    n_int = denom_dept[~denom_dept["region"].eq("AMBA")]["nacimientos_cohorte"].sum()
    rr, lo, hi = rate_ratio_ci((~es_amba).sum(), n_int, es_amba.sum(), n_amba, level)
    salidas["h2_amba_vs_interior"] = pd.DataFrame([
        {"grupo": "Interior (no AMBA)", "jugadores": int((~es_amba).sum()),
         "nacimientos": n_int, "tasa_100k": PER * (~es_amba).sum() / n_int,
         "RR_vs_AMBA": rr, "RR_ic_lo": lo, "RR_ic_hi": hi},
        {"grupo": "AMBA", "jugadores": int(es_amba.sum()), "nacimientos": n_amba,
         "tasa_100k": PER * es_amba.sum() / n_amba, "RR_vs_AMBA": 1.0,
         "RR_ic_lo": np.nan, "RR_ic_hi": np.nan}])
    return salidas


# --------------------------------------------------------------------------- #
# Temporal
# --------------------------------------------------------------------------- #
def temporal(cfg, players, denom_dept) -> dict[str, pd.DataFrame]:
    """Tasa por región y década, con los nacimientos de cada década.

    Ahora el denominador cambia con la década, porque son los nacimientos de esa
    década. La caída de las dos últimas es censura, no fenómeno: ver
    `diagnostico_censura_cohortes`.
    """
    p = paths()
    nac = pd.read_parquet(p.processed / "nacimientos_provincia_anio.parquet")
    prov_reg = (denom_dept.groupby(["prov_id", "region"], as_index=False)
                ["nacimientos_cohorte"].sum())
    prov_reg["w"] = prov_reg["nacimientos_cohorte"] / \
        prov_reg.groupby("prov_id")["nacimientos_cohorte"].transform("sum")

    filas = []
    for decada, sub in players.groupby("decada"):
        nac_dec = (nac[nac["anio"].between(int(decada), int(decada) + 9)]
                   .groupby("prov_id", as_index=False)["nacimientos"].sum())
        rep = nac_dec.merge(prov_reg[["prov_id", "region", "w"]], on="prov_id", how="left")
        por_region = (rep.assign(n=rep["nacimientos"] * rep["w"])
                      .groupby("region")["n"].sum())
        for region, s in sub.groupby("region"):
            filas.append({"decada": int(decada), "region": region, "jugadores": len(s),
                          "nacimientos": float(por_region.get(region, np.nan))})
    t = pd.DataFrame(filas).dropna(subset=["nacimientos"])
    t = add_rate_columns(t, "jugadores", "nacimientos", per=PER,
                         level=cfg["stats"]["ci_level"])
    t["censurada"] = t["decada"] > cfg["cohorts"]["career_complete_max"] - 10
    return {"temporal_region_decada": t}


# --------------------------------------------------------------------------- #
# Exploratorio: posición × región
# --------------------------------------------------------------------------- #
POSICIONES = {"Q193592": "defensor", "Q280658": "mediocampista",
              "Q336286": "delantero", "Q201330": "arquero"}


def exploratorio_posiciones(cfg, players) -> dict[str, pd.DataFrame]:
    """Posición × región. ESTRICTAMENTE exploratorio.

    Con 4 posiciones × 6 regiones hay 24 contrastes: sin corregir por
    comparaciones múltiples, algo iba a dar «significativo» por azar. Se aplica
    Benjamini-Hochberg y se reporta el p ajustado, no el crudo.
    """
    pos = players.explode("positions")
    pos = pos[pos["positions"].isin(POSICIONES)].copy()
    pos["posicion"] = pos["positions"].map(POSICIONES)

    tab = pd.crosstab(pos["region"], pos["posicion"])
    por_pos, por_reg = tab.sum(axis=0), tab.sum(axis=1)
    n = tab.values.sum()

    filas = []
    for region in tab.index:
        for posicion in tab.columns:
            a = tab.loc[region, posicion]
            b, c = por_reg[region] - a, por_pos[posicion] - a
            d = n - a - b - c
            or_, lo, hi = odds_ratio_ci(a, b, c, d, cfg["stats"]["ci_level"])
            _, pv = st.fisher_exact([[a, b], [c, d]])
            filas.append({"region": region, "posicion": posicion, "n": int(a),
                          "esperado": por_reg[region] * por_pos[posicion] / n,
                          "OR": or_, "OR_ic_lo": lo, "OR_ic_hi": hi, "p_crudo": pv})
    t = pd.DataFrame(filas)
    rechaza, p_adj = fdr_bh(t["p_crudo"].values, cfg["stats"]["alpha"])
    t["p_fdr_bh"], t["significativo_tras_fdr"] = p_adj, rechaza
    return {"exploratorio_posicion_region": t.sort_values("p_fdr_bh")}


# --------------------------------------------------------------------------- #
# Regresión
# --------------------------------------------------------------------------- #
def regresion_tamano(cfg, players, ciudades) -> dict[str, pd.DataFrame]:
    """Binomial negativa: jugadores ~ log(tamaño), offset log(nacimientos).

    Se agrega el término cuadrático porque la hipótesis clásica del birthplace
    effect es una U invertida con pico en ciudades medianas, no una recta. Si el
    cuadrático no aporta, no hay tal pico.
    """
    conteo = players.groupby("ciudad_id").size().rename("jugadores")
    d = ciudades.set_index("ciudad_id").join(conteo).fillna({"jugadores": 0})
    d = d[(d["nacimientos_cohorte"] > 0) & (d["pob_ciudad"] > 0)].copy()
    d["log_tamano"] = np.log(d["pob_ciudad"])
    d["log_tamano2"] = d["log_tamano"] ** 2

    filas = []
    for nombre, cols in {"lineal": ["log_tamano"],
                         "cuadratico": ["log_tamano", "log_tamano2"]}.items():
        X = sm.add_constant(d[cols])
        m = sm.GLM(d["jugadores"], X, family=sm.families.NegativeBinomial(alpha=1.0),
                   offset=np.log(d["nacimientos_cohorte"])).fit()
        for termino in m.params.index:
            filas.append({
                "modelo": nombre, "termino": termino, "coef": m.params[termino],
                "ee": m.bse[termino], "IRR": np.exp(m.params[termino]),
                "IRR_ic_lo": np.exp(m.conf_int().loc[termino, 0]),
                "IRR_ic_hi": np.exp(m.conf_int().loc[termino, 1]),
                "p": m.pvalues[termino], "aic": m.aic, "n_ciudades": int(d.shape[0])})
    return {"regresion_tamano_ciudad": pd.DataFrame(filas)}


# --------------------------------------------------------------------------- #
def main() -> None:
    cfg = load_config()
    p = paths()
    np.random.seed(cfg["stats"]["random_seed"])

    players = pd.read_parquet(p.processed / "analysis_players.parquet")
    denom_dept = pd.read_parquet(p.processed / "denom_cohorte_departamento.parquet")
    denom_prov = pd.read_parquet(p.processed / "denom_cohorte_provincia.parquet")
    nac_prov = pd.read_parquet(p.processed / "nacimientos_provincia_anio.parquet")

    ciudades = cargar_ciudades(p)

    con_ciudad = players[players["ciudad_id"].notna()]
    log.info("muestra: %d jugadores (%d con ciudad asignada), cohortes %d–%d",
             len(players), len(con_ciudad),
             cfg["cohorts"]["analysis_min_year"], cfg["cohorts"]["analysis_max_year"])

    tests: list[dict] = []
    salidas: dict[str, pd.DataFrame] = {
        "diagnostico_censura_cohortes": censura_por_cohorte(cfg, players, nac_prov)}
    salidas |= h1_tamano_ciudad(cfg, con_ciudad, ciudades, tests)
    salidas |= h2_geografia(cfg, players, denom_dept, denom_prov, tests)
    salidas |= temporal(cfg, players, denom_dept)
    salidas |= exploratorio_posiciones(cfg, players)
    salidas |= regresion_tamano(cfg, con_ciudad, ciudades)
    # Comparaciones múltiples también en los contrastes confirmatorios. La regla
    # del proyecto la exigía solo en los exploratorios, y así se cumplía al pie
    # de la letra y se esquivaba en espíritu: los confirmatorios son más (doce
    # tests de bondad de ajuste contra veinticuatro cruces) y no se corregían.
    tb = pd.DataFrame(tests)
    rechaza, p_adj = fdr_bh(tb["p"].values, cfg["stats"]["alpha"])
    tb["p_fdr_bh"], tb["significativo_tras_fdr"] = p_adj, rechaza
    salidas["tests_bondad_ajuste"] = tb
    log.info("bondad de ajuste: %d de %d tests sobreviven a Benjamini-Hochberg",
             int(rechaza.sum()), len(tb))

    for nombre, tabla in salidas.items():
        tabla.to_csv(p.tables / f"{nombre}.csv", index=False, encoding="utf-8")
        log.info("  %-42s %4d filas", nombre + ".csv", len(tabla))

    log.info("\n%s", salidas["diagnostico_censura_cohortes"]
             [["quinquenio", "jugadores", "tasa", "pct_del_pico", "lectura"]]
             .to_string(index=False))


if __name__ == "__main__":
    main()
