"""Fase 5 — Análisis completo. Exporta todas las tablas a `outputs/tables/`.

Cada hipótesis se responde con: conteo observado, esperado por la distribución
poblacional real, tasa per cápita con IC exacto de Poisson, razón de tasas
contra una referencia declarada, y un test de bondad de ajuste con su tamaño de
efecto. Nunca un p-valor solo.

Uso:
    python -m src.analysis.run_all
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

from src.analysis.stats import (
    add_rate_columns,
    chi2_gof,
    fdr_bh,
    rate_ratio_ci,
    standardized_residuals,
)
from src.common import get_logger, load_config, paths

log = get_logger("analysis")

PER = 100_000


def _tabla(obs: pd.Series, pob: pd.Series, referencia: str | None,
           level: float) -> pd.DataFrame:
    """Arma la tabla estándar: observado, esperado, tasa+IC y RR contra la referencia.

    La columna de la unidad de análisis siempre sale como `unidad`: los dos
    lados pueden venir con nombres de índice distintos (`prov_id` en el
    numerador, `prov_nac_id` en el denominador) y así todas las tablas tienen
    la misma forma, que es lo que consumen las figuras y el paper.
    """
    obs = obs.rename_axis("unidad")
    pob = pob.rename_axis("unidad")
    t = pd.concat([obs.rename("jugadores"), pob.rename("poblacion")], axis=1).fillna(0)
    t = t[t["poblacion"] > 0]
    t["pct_jugadores"] = 100 * t["jugadores"] / t["jugadores"].sum()
    t["pct_poblacion"] = 100 * t["poblacion"] / t["poblacion"].sum()
    t["esperado"] = t["jugadores"].sum() * t["poblacion"] / t["poblacion"].sum()
    t["obs_sobre_esp"] = t["jugadores"] / t["esperado"]
    t["residuo_estand"] = standardized_residuals(t["jugadores"].values, t["poblacion"].values)
    t = add_rate_columns(t, "jugadores", "poblacion", per=PER, level=level)

    if referencia is not None and referencia in t.index:
        rk, rn = t.loc[referencia, "jugadores"], t.loc[referencia, "poblacion"]
        rr = [rate_ratio_ci(k, n, rk, rn, level) for k, n in
              zip(t["jugadores"], t["poblacion"])]
        t["RR"], t["RR_ic_lo"], t["RR_ic_hi"] = zip(*rr)
        t["RR_referencia"] = referencia
    return t.reset_index()


def _gof_row(hipotesis: str, variante: str, t: pd.DataFrame) -> dict:
    g = chi2_gof(t["jugadores"].values, t["poblacion"].values)
    return {"hipotesis": hipotesis, "variante": variante, **g.as_dict()}


# --------------------------------------------------------------------------- #
# H1 — tamaño de ciudad
# --------------------------------------------------------------------------- #
def h1_tamano_ciudad(cfg, players, ciudades, tests: list) -> dict[str, pd.DataFrame]:
    level = cfg["stats"]["ci_level"]
    salidas = {}

    for scheme_name, scheme in cfg["city_size"]["schemes"].items():
        col = f"tramo_{scheme_name}"
        obs = players.groupby(col, observed=False).size()
        pob = ciudades.groupby(col, observed=False)["pob_cohorte_ciudad"].sum()
        t = _tabla(obs, pob, scheme["reference_label"], level)
        t.insert(0, "esquema", scheme_name)
        salidas[f"h1_tramos_{scheme_name}"] = t
        tests.append(_gof_row("H1", f"esquema {scheme_name}", t))

    # Robustez 1: la localidad sola en vez del aglomerado. Cambia qué se
    # entiende por "ciudad" y es donde la literatura suele ser ambigua.
    scheme = cfg["city_size"]["schemes"][cfg["city_size"]["default_scheme"]]
    denom_loc = pd.read_parquet(paths().processed / "denom_ciudad.parquet")
    from src.clean.geo_units import city_size_series
    denom_loc["tramo_loc"] = city_size_series(denom_loc["pob_localidad"], scheme)
    pl = players.copy()
    pl["tramo_loc"] = city_size_series(pl["pob_localidad"], scheme)
    t = _tabla(pl.groupby("tramo_loc", observed=False).size(),
               denom_loc.groupby("tramo_loc", observed=False)["pob_cohorte_localidad"].sum(),
               scheme["reference_label"], level)
    salidas["h1_robustez_localidad_sola"] = t
    tests.append(_gof_row("H1", "unidad = localidad censal (no aglomerado)", t))

    # Robustez 2: cohortes recientes. Cuanto más joven la cohorte, menos tiempo
    # tuvo de emigrar de su lugar de nacimiento, así que el denominador de 2022
    # se parece más a la población de origen. Si el patrón se sostiene acá, no
    # es un artefacto de la migración.
    col = f"tramo_{cfg['city_size']['default_scheme']}"
    for etiqueta, (y0, y1) in {"1970–1984": (1970, 1984), "1985–2000": (1985, 2000)}.items():
        sub = players[players["birth_year"].between(y0, y1)]
        a0, a1 = 2022 - y1, 2022 - y0
        pob_ciudad = _pob_ciudad_por_edad(a0, a1)
        tramo_de = ciudades.set_index("ciudad_id")[col]
        pob = pob_ciudad.groupby(pob_ciudad.index.map(tramo_de), observed=False).sum()
        t = _tabla(sub.groupby(col, observed=False).size(), pob,
                   cfg["city_size"]["schemes"][cfg["city_size"]["default_scheme"]]["reference_label"],
                   level)
        t.insert(0, "cohorte", etiqueta)
        salidas[f"h1_robustez_cohorte_{y0}_{y1}"] = t
        tests.append(_gof_row("H1", f"cohorte {etiqueta}", t))

    return salidas


def _pob_ciudad_por_edad(a0: int, a1: int) -> pd.Series:
    """Población de cada ciudad en el rango de edades pedido (censo 2022)."""
    p = paths()
    loc = pd.read_parquet(p.processed / "pop_localidad_edad.parquet")
    aglo = pd.read_parquet(p.processed / "pop_aglomerado_edad.parquet")
    ci = pd.read_parquet(p.processed / "denom_ciudad.parquet")
    loc = loc[loc["edad"].between(a0, a1)].groupby("localidad_id")["n"].sum()
    aglo = aglo[aglo["edad"].between(a0, a1)].groupby("aglomerado_id")["n"].sum()
    ci = ci.assign(
        ciudad_id=np.where(ci["aglomerado_id"].notna(),
                           "AGLO_" + ci["aglomerado_id"].astype(str),
                           "LOC_" + ci["localidad_id"].astype(str)),
        pob=np.where(ci["aglomerado_id"].notna(),
                     ci["aglomerado_id"].map(aglo), ci["localidad_id"].map(loc)))
    return ci.drop_duplicates("ciudad_id").set_index("ciudad_id")["pob"]


# --------------------------------------------------------------------------- #
# H2 — geografía
# --------------------------------------------------------------------------- #
def h2_geografia(cfg, players, denom_dept, tests: list) -> dict[str, pd.DataFrame]:
    level = cfg["stats"]["ci_level"]
    p = paths()
    salidas = {}

    # --- región -------------------------------------------------------------
    t = _tabla(players.groupby("region").size(),
               denom_dept.groupby("region")["pob_cohorte"].sum(), "AMBA", level)
    salidas["h2_regiones"] = t
    tests.append(_gof_row("H2", "regiones", t))

    # --- provincia ----------------------------------------------------------
    prov_nombre = (players.dropna(subset=["prov_id"])
                          .drop_duplicates("prov_id").set_index("prov_id")["prov_nombre"])
    t = _tabla(players.groupby("prov_id").size(),
               denom_dept.groupby("prov_id")["pob_cohorte"].sum(), "02", level)
    t["provincia"] = t["unidad"].map(prov_nombre)
    salidas["h2_provincias"] = t.sort_values("tasa", ascending=False)
    tests.append(_gof_row("H2", "provincias (baseline: residentes 2022, cohorte)", t))

    # --- provincia, baseline por LUGAR DE NACIMIENTO ------------------------
    # El censo pregunta provincia de nacimiento (P14). Ese denominador cuenta
    # nacimientos, no residencia: no lo distorsiona la migración interna, que
    # es exactamente el sesgo que amenaza a H2. No está cruzado por edad, así
    # que es de todas las cohortes: se reporta como contraste, no como principal.
    nac = pd.read_parquet(p.processed / "pop_dept_nacprov.parquet")
    # El código 99 es «Ignorado»: no es una provincia y no puede ser denominador.
    nacidos = (nac[nac["prov_nac_id"] != "99"]
               .groupby("prov_nac_id")["n"].sum())
    t_nac = _tabla(players.groupby("prov_id").size(), nacidos, "02", level)
    t_nac["provincia"] = t_nac["unidad"].map(prov_nombre)
    salidas["h2_provincias_baseline_nacimiento"] = t_nac.sort_values("tasa", ascending=False)
    tests.append(_gof_row("H2", "provincias (baseline: nacidos en la provincia, P14)", t_nac))

    # --- provincia, baseline censo histórico --------------------------------
    hist = pd.read_parquet(p.processed / "pop_dept_historica.parquet")
    for censo in sorted(hist["censo"].unique()):
        pob = (hist[hist["censo"] == censo]
               .assign(prov_id=lambda d: d["dept_id"].str[:2])
               .groupby("prov_id")["pob"].sum())
        t_h = _tabla(players.groupby("prov_id").size(), pob, "02", level)
        t_h["provincia"] = t_h["unidad"].map(prov_nombre)
        t_h.insert(0, "censo_baseline", censo)
        salidas[f"h2_provincias_censo_{censo}"] = t_h.sort_values("tasa", ascending=False)
        tests.append(_gof_row("H2", f"provincias (baseline: población total censo {censo})", t_h))

    # --- departamento -------------------------------------------------------
    dept_nombre = (players.dropna(subset=["dept_id"])
                          .drop_duplicates("dept_id").set_index("dept_id")["dept_nombre"])
    t = _tabla(players.groupby("dept_id").size(),
               denom_dept.set_index("dept_id")["pob_cohorte"], None, level)
    t["departamento"] = t["unidad"].map(dept_nombre)
    t["provincia"] = t["unidad"].str[:2].map(prov_nombre)
    t["region"] = t["unidad"].map(denom_dept.set_index("dept_id")["region"])
    min_n = cfg["cohorts"]["min_n_subgroup"]
    t["reportable"] = t["jugadores"] >= min_n
    salidas["h2_departamentos"] = t.sort_values("tasa", ascending=False)
    tests.append(_gof_row("H2", "departamentos", t))

    # --- AMBA vs interior ---------------------------------------------------
    esamba = players["region"].eq("AMBA")
    pob_amba = denom_dept[denom_dept["region"].eq("AMBA")]["pob_cohorte"].sum()
    pob_int = denom_dept[~denom_dept["region"].eq("AMBA")]["pob_cohorte"].sum()
    rr, lo, hi = rate_ratio_ci((~esamba).sum(), pob_int, esamba.sum(), pob_amba, level)
    salidas["h2_amba_vs_interior"] = pd.DataFrame([{
        "grupo": "Interior (no AMBA)", "jugadores": int((~esamba).sum()), "poblacion": pob_int,
        "tasa_100k": PER * (~esamba).sum() / pob_int,
        "RR_vs_AMBA": rr, "RR_ic_lo": lo, "RR_ic_hi": hi,
    }, {
        "grupo": "AMBA", "jugadores": int(esamba.sum()), "poblacion": pob_amba,
        "tasa_100k": PER * esamba.sum() / pob_amba,
        "RR_vs_AMBA": 1.0, "RR_ic_lo": np.nan, "RR_ic_hi": np.nan,
    }])
    return salidas


# --------------------------------------------------------------------------- #
# Temporal
# --------------------------------------------------------------------------- #
def temporal(cfg, players, tests: list) -> dict[str, pd.DataFrame]:
    """Tasa por década de nacimiento, con el denominador de cada cohorte.

    Ojo con la lectura: hacia atrás la mortalidad y la emigración achican el
    denominador y hacia adelante hay jugadores que todavía no debutaron. La
    serie sirve para ver el patrón geográfico, no el nivel absoluto.
    """
    p = paths()
    level = cfg["stats"]["ci_level"]
    dept_edad = pd.read_parquet(p.processed / "pop_dept_edad.parquet")
    filas = []
    for decada, sub in players.groupby("decada"):
        a0, a1 = 2022 - int(decada) - 9, 2022 - int(decada)
        pob = dept_edad[dept_edad["edad"].between(a0, a1)]
        for region, s in sub.groupby("region"):
            dep_reg = pd.read_parquet(p.processed / "denom_departamento.parquet")
            ids = dep_reg[dep_reg["region"] == region]["dept_id"]
            filas.append({"decada": int(decada), "region": region, "jugadores": len(s),
                          "poblacion": int(pob[pob["dept_id"].isin(ids)]["n"].sum())})
    t = pd.DataFrame(filas)
    t = add_rate_columns(t, "jugadores", "poblacion", per=PER, level=level)
    return {"temporal_region_decada": t}


# --------------------------------------------------------------------------- #
# Exploratorio: posición × región
# --------------------------------------------------------------------------- #
POSICIONES = {
    "Q193592": "defensor", "Q280658": "mediocampista",
    "Q336286": "delantero", "Q201330": "arquero",
}


def exploratorio_posiciones(cfg, players) -> dict[str, pd.DataFrame]:
    """Posición × región. ESTRICTAMENTE exploratorio.

    Con 4 posiciones × 6 regiones hay 24 contrastes: sin corrección por
    comparaciones múltiples, algo iba a dar «significativo» por azar. Se aplica
    Benjamini-Hochberg y se reporta el p ajustado, no el crudo.
    """
    pos = players.explode("positions")
    pos = pos[pos["positions"].isin(POSICIONES)].copy()
    pos["posicion"] = pos["positions"].map(POSICIONES)

    tab = pd.crosstab(pos["region"], pos["posicion"])
    total_por_pos = tab.sum(axis=0)
    total_por_reg = tab.sum(axis=1)
    n = tab.values.sum()

    filas = []
    for region in tab.index:
        for posicion in tab.columns:
            a = tab.loc[region, posicion]
            b = total_por_reg[region] - a
            c = total_por_pos[posicion] - a
            d = n - a - b - c
            from src.analysis.stats import odds_ratio_ci
            or_, lo, hi = odds_ratio_ci(a, b, c, d, cfg["stats"]["ci_level"])
            from scipy import stats as st
            _, p_val = st.fisher_exact([[a, b], [c, d]])
            filas.append({"region": region, "posicion": posicion, "n": int(a),
                          "esperado": total_por_reg[region] * total_por_pos[posicion] / n,
                          "OR": or_, "OR_ic_lo": lo, "OR_ic_hi": hi, "p_crudo": p_val})
    t = pd.DataFrame(filas)
    rechaza, p_adj = fdr_bh(t["p_crudo"].values, cfg["stats"]["alpha"])
    t["p_fdr_bh"] = p_adj
    t["significativo_tras_fdr"] = rechaza
    chi2 = chi2_gof(tab.values.flatten(),
                    np.outer(total_por_reg, total_por_pos).flatten())
    t.attrs["cramers_v"] = chi2.cramers_v
    return {"exploratorio_posicion_region": t.sort_values("p_fdr_bh")}


# --------------------------------------------------------------------------- #
# Regresión
# --------------------------------------------------------------------------- #
def regresion_tamano(cfg, players, ciudades) -> dict[str, pd.DataFrame]:
    """Modelo binomial negativo: jugadores ~ log(tamaño), offset log(población).

    Se agrega el término cuadrático porque la hipótesis clásica del birthplace
    effect es una U invertida (pico en ciudades medianas), no una recta. Si el
    cuadrático no aporta, no hay tal pico.
    """
    conteo = players.groupby("ciudad_id").size().rename("jugadores")
    d = ciudades.set_index("ciudad_id").join(conteo).fillna({"jugadores": 0})
    d = d[(d["pob_cohorte_ciudad"] > 0) & (d["pob_ciudad"] > 0)].copy()
    d["log_tamano"] = np.log(d["pob_ciudad"])
    d["log_tamano2"] = d["log_tamano"] ** 2

    filas = []
    for nombre, cols in {"lineal": ["log_tamano"],
                         "cuadratico": ["log_tamano", "log_tamano2"]}.items():
        X = sm.add_constant(d[cols])
        modelo = sm.GLM(d["jugadores"], X, family=sm.families.NegativeBinomial(alpha=1.0),
                        offset=np.log(d["pob_cohorte_ciudad"])).fit()
        for termino in modelo.params.index:
            filas.append({
                "modelo": nombre, "termino": termino,
                "coef": modelo.params[termino], "ee": modelo.bse[termino],
                "IRR": np.exp(modelo.params[termino]),
                "IRR_ic_lo": np.exp(modelo.conf_int().loc[termino, 0]),
                "IRR_ic_hi": np.exp(modelo.conf_int().loc[termino, 1]),
                "p": modelo.pvalues[termino], "aic": modelo.aic, "n_ciudades": int(d.shape[0]),
            })
    return {"regresion_tamano_ciudad": pd.DataFrame(filas)}


# --------------------------------------------------------------------------- #
def main() -> None:
    cfg = load_config()
    p = paths()
    np.random.seed(cfg["stats"]["random_seed"])

    players = pd.read_parquet(p.processed / "analysis_players.parquet")
    ciudades = pd.read_parquet(p.processed / "denom_ciudad_unica.parquet")
    denom_dept = pd.read_parquet(p.processed / "denom_departamento.parquet")

    con_ciudad = players[players["ciudad_id"].notna()]
    log.info("muestra: %d jugadores (%d con ciudad asignada)", len(players), len(con_ciudad))

    tests: list[dict] = []
    salidas: dict[str, pd.DataFrame] = {}
    salidas |= h1_tamano_ciudad(cfg, con_ciudad, ciudades, tests)
    salidas |= h2_geografia(cfg, players, denom_dept, tests)
    salidas |= temporal(cfg, players, tests)
    salidas |= exploratorio_posiciones(cfg, players)
    salidas |= regresion_tamano(cfg, con_ciudad, ciudades)
    salidas["tests_bondad_ajuste"] = pd.DataFrame(tests)

    for nombre, tabla in salidas.items():
        tabla.to_csv(p.tables / f"{nombre}.csv", index=False, encoding="utf-8")
        log.info("  %-42s %4d filas", nombre + ".csv", len(tabla))

    log.info("\n%s", salidas["tests_bondad_ajuste"].to_string(index=False))
    log.info("listo: %d tablas en %s", len(salidas), p.tables)


if __name__ == "__main__":
    main()
