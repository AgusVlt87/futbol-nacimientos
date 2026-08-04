"""Fase 9 — La selección argentina como criterio de éxito deportivo.

**Por qué existe este módulo.** Todo el resto del estudio mide *tasas de
producción*: futbolistas por cada 100.000 nacidos en un lugar. Esa métrica
depende de un denominador —los nacidos vivos repartidos por departamento— que
tiene dos problemas conocidos y declarados: el reparto intraprovincial
sobreestima un 17% a los departamentos más chicos, y el lugar de nacimiento
registrado es el de la maternidad, no el de crianza, lo que vacía a los pueblos
y llena a las cabeceras.

Este módulo agrega un análisis que **no depende de ningún denominador
poblacional** y que por lo tanto no lo toca ninguno de esos dos problemas:

    Entre los jugadores que YA llegaron a un juvenil de la selección,
    ¿qué proporción llega después a la Mayor, según dónde nacieron?

Es un contraste *dentro* de un grupo ya filtrado por talento reconocido. No hay
denominador que sesgar. La cobertura de Wikidata en juveniles de selección es
casi censal, así que tampoco la fabrica el corpus. Y si un pibe nacido en un
pueblo figura como nacido en la cabecera, eso **atenúa** el efecto en vez de
crearlo: el sesgo juega en contra del hallazgo, no a favor.

Se reportan tres cosas:

    1. Tasas de producción de seleccionados (Mayor, juvenil, cualquiera) por
       tramo de ciudad y por región. Tiene denominador, con sus limitaciones.
    2. **Conversión juvenil → Mayor**, el análisis sin denominador.
    3. Migración y clubes formadores de los seleccionados.

Salidas en `outputs/tables/seleccion_*.csv`.

Uso:
    python -m src.analysis.run_seleccion
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

from src.analysis.stats import odds_ratio_ci, poisson_rate_ci
from src.clean.geo_units import haversine_km
from src.common import get_logger, load_config, paths, write_run_manifest
from src.denominadores import cargar_ciudades, cargar_departamentos

log = get_logger("analysis.seleccion")

POR_MILLON = 1_000_000
# Un jugador no puede haber firmado su primer contrato antes de nacer ni a los
# 45 años: Wikidata tiene fechas de vínculo mal cargadas y hay que acotarlas.
EDAD_PRIMER_CLUB_MIN, EDAD_PRIMER_CLUB_MAX = 12, 35


def cargar(cfg, p) -> pd.DataFrame:
    """Muestra de análisis con las banderas de selección ya resueltas."""
    lv = pd.read_parquet(p.processed / "player_level.parquet")
    c = cfg["cohorts"]
    d = lv[lv["birth_year"].between(c["analysis_min_year"], c["analysis_max_year"])
           & lv["geo_status"].eq("ok")].copy()
    d["seleccionado"] = d["seleccion_mayor"] | d["seleccion_juvenil"]
    d["metro"] = d["tramo"].eq(">500k")
    d["edad_primer_club"] = d["primer_club_anio"] - d["birth_year"]
    fuera = ~d["edad_primer_club"].between(EDAD_PRIMER_CLUB_MIN, EDAD_PRIMER_CLUB_MAX)
    d.loc[fuera, "edad_primer_club"] = np.nan
    return d


# --------------------------------------------------------------------------- #
# 1. Producción de seleccionados (con denominador)
# --------------------------------------------------------------------------- #
def tasas_de_produccion(cfg, d, ciudades, denom_dept) -> dict[str, pd.DataFrame]:
    """Seleccionados por millón de nacidos, por tramo de ciudad y por región."""
    level = cfg["stats"]["ci_level"]
    col = f"tramo_{cfg['city_size']['default_scheme']}"
    nac_tramo = ciudades.groupby(col, observed=False)["nacimientos_cohorte"].sum()
    nac_region = denom_dept.groupby("region")["nacimientos_cohorte"].sum()

    grupos = {"seleccion_mayor": "Selección Mayor",
              "seleccion_juvenil": "Juveniles (sub-17 / sub-20)",
              "seleccionado": "Mayor o juvenil"}

    filas_t, filas_r = [], []
    for flag, etiqueta in grupos.items():
        sub = d[d[flag]]
        obs = sub.groupby(col, observed=False).size().reindex(nac_tramo.index, fill_value=0)
        r, lo, hi = poisson_rate_ci(obs.values, nac_tramo.values, per=POR_MILLON, level=level)
        filas_t.append(pd.DataFrame({
            "grupo": etiqueta, "tramo": obs.index, "seleccionados": obs.values,
            "nacimientos": nac_tramo.values, "por_millon": r, "ic_lo": lo, "ic_hi": hi}))

        obsr = sub.groupby("region").size().reindex(nac_region.index, fill_value=0)
        r, lo, hi = poisson_rate_ci(obsr.values, nac_region.values, per=POR_MILLON, level=level)
        filas_r.append(pd.DataFrame({
            "grupo": etiqueta, "region": obsr.index, "seleccionados": obsr.values,
            "nacimientos": nac_region.values, "por_millon": r, "ic_lo": lo, "ic_hi": hi}))

    return {"seleccion_tasas_por_tramo": pd.concat(filas_t, ignore_index=True),
            "seleccion_tasas_por_region": pd.concat(filas_r, ignore_index=True)}


# --------------------------------------------------------------------------- #
# 2. Conversión juvenil -> Mayor (SIN denominador). El resultado robusto.
# --------------------------------------------------------------------------- #
def conversion(cfg, d) -> dict[str, pd.DataFrame]:
    """De los que pasan por un juvenil, ¿quiénes llegan a la Mayor?

    Este es el análisis que no depende del denominador poblacional. El
    denominador acá es «jugadores que ya llegaron a un juvenil de la selección»,
    que es un dato observado, no una estimación.
    """
    j = d[d["seleccion_juvenil"]].copy()
    col = f"tramo_{cfg['city_size']['default_scheme']}"

    por_tramo = (j.groupby(col, observed=False)
                  .agg(juveniles=("player_qid", "size"),
                       llegan_a_mayor=("seleccion_mayor", "sum"))
                  .reset_index().rename(columns={col: "tramo"}))
    por_tramo["pct_conversion"] = 100 * por_tramo["llegan_a_mayor"] / por_tramo["juveniles"]
    # IC binomial exacto (Clopper-Pearson): con 19 casos en el tramo más chico,
    # la aproximación normal no sirve.
    ic = [stats.binomtest(int(k), int(n)).proportion_ci(cfg["stats"]["ci_level"])
          if n > 0 else (np.nan, np.nan)
          for k, n in zip(por_tramo["llegan_a_mayor"], por_tramo["juveniles"])]
    por_tramo["ic_lo"] = [100 * x[0] for x in ic]
    por_tramo["ic_hi"] = [100 * x[1] for x in ic]

    por_region = (j.groupby("region")
                   .agg(juveniles=("player_qid", "size"),
                        llegan_a_mayor=("seleccion_mayor", "sum"))
                   .reset_index())
    por_region["pct_conversion"] = 100 * por_region["llegan_a_mayor"] / por_region["juveniles"]

    # --- el contraste con potencia: metrópoli vs todo lo demás ---------------
    # Los cinco tramos por separado tienen entre 19 y 31 casos fuera del AMBA:
    # no alcanzan para un gradiente. El contraste binario sí tiene potencia y es
    # además la forma que tiene el efecto en el resto del estudio.
    #
    # OJO con el filtro. `metro` sale de `tramo.eq(">500k")`, y `.eq()` devuelve
    # **False** —no NaN— cuando `tramo` es nulo. Como `metro` queda booleano
    # puro, el `dropna(subset=["metro"])` que había acá no descartaba nada y los
    # jugadores sin ciudad asignada (los que tienen `P19` a nivel provincia o
    # departamento) entraban al contraste como si hubieran nacido fuera de un
    # gran aglomerado: 105 casos en vez de 95. Son exactamente los mismos que
    # §2.4 excluye del análisis de tamaño de ciudad, así que el contraste usaba
    # un criterio distinto del resto del trabajo. Hay que filtrar por `tramo`.
    jj = j[j["tramo"].notna()]
    a = int(((~jj["metro"]) & jj["seleccion_mayor"]).sum())
    b = int(((~jj["metro"]) & ~jj["seleccion_mayor"]).sum())
    c = int((jj["metro"] & jj["seleccion_mayor"]).sum())
    e = int((jj["metro"] & ~jj["seleccion_mayor"]).sum())
    or_, lo_, hi_ = odds_ratio_ci(a, b, c, e, cfg["stats"]["ci_level"])
    chi2, p_chi, dof, _ = stats.chi2_contingency([[a, b], [c, e]])
    p_fisher = stats.fisher_exact([[a, b], [c, e]])[1]

    # --- control por cohorte -------------------------------------------------
    # La objeción obvia: quizá los del interior son de cohortes más viejas,
    # cuando llegar a la Mayor era más fácil. Se controla con una logística.
    jj = jj.copy()
    jj["fuera_de_metro"] = (~jj["metro"]).astype(int)
    X = sm.add_constant(jj[["fuera_de_metro", "birth_year"]].astype(float))
    modelo = sm.Logit(jj["seleccion_mayor"].astype(int), X).fit(disp=0)
    coef = modelo.params["fuera_de_metro"]
    ci = modelo.conf_int().loc["fuera_de_metro"]

    tests = pd.DataFrame([
        {"analisis": "conversión juvenil → Mayor: nacidos fuera de un gran aglomerado vs en uno",
         "n": a + b + c + e,
         "fuera_metro_llegan": a, "fuera_metro_total": a + b,
         "fuera_metro_pct": 100 * a / (a + b),
         "metro_llegan": c, "metro_total": c + e, "metro_pct": 100 * c / (c + e),
         "OR": or_, "OR_ic_lo": lo_, "OR_ic_hi": hi_,
         "chi2": chi2, "df": dof, "p_chi2": p_chi, "p_fisher_exacto": p_fisher,
         "OR_ajustado_por_cohorte": float(np.exp(coef)),
         "OR_aj_ic_lo": float(np.exp(ci[0])), "OR_aj_ic_hi": float(np.exp(ci[1])),
         "p_ajustado": float(modelo.pvalues["fuera_de_metro"]),
         "lectura": ("no usa denominador poblacional: el denominador son los "
                     "juveniles observados. No lo afecta ni el reparto "
                     "intraprovincial ni el artefacto de maternidad ni la "
                     "cobertura de Wikidata. Leer junto a la tabla "
                     "seleccion_conversion_loso: el contraste depende de un "
                     "solo estrato.")},
    ])

    # --- ¿de qué estrato depende el contraste? -------------------------------
    # El agregado «fuera de un gran aglomerado» junta cuatro tramos con 19 a 31
    # casos cada uno. Si el resultado lo aporta uno solo, el agregado no es un
    # hallazgo sobre el interior sino sobre esa celda. Se saca un tramo por vez.
    filas = []
    ref_metro = cfg["city_size"]["schemes"][cfg["city_size"]["default_scheme"]]["reference_label"]
    for tramo in [t for t in por_tramo["tramo"] if t != ref_metro]:
        s = jj[jj["tramo"] != tramo]
        a2 = int(((~s["metro"]) & s["seleccion_mayor"]).sum())
        b2 = int(((~s["metro"]) & ~s["seleccion_mayor"]).sum())
        c2 = int((s["metro"] & s["seleccion_mayor"]).sum())
        e2 = int((s["metro"] & ~s["seleccion_mayor"]).sum())
        o2, l2, h2 = odds_ratio_ci(a2, b2, c2, e2, cfg["stats"]["ci_level"])
        filas.append({
            "tramo_excluido": tramo, "n": a2 + b2 + c2 + e2,
            "fuera_metro_llegan": a2, "fuera_metro_total": a2 + b2,
            "fuera_metro_pct": 100 * a2 / max(a2 + b2, 1),
            "OR": o2, "OR_ic_lo": l2, "OR_ic_hi": h2,
            "p_fisher_exacto": stats.fisher_exact([[a2, b2], [c2, e2]])[1],
            "sobrevive": bool(l2 > 1.0)})
    loso = pd.DataFrame(filas)

    return {"seleccion_conversion_por_tramo": por_tramo,
            "seleccion_conversion_por_region": por_region,
            "seleccion_conversion_tests": tests,
            "seleccion_conversion_loso": loso}


# --------------------------------------------------------------------------- #
# 3. Migración y clubes formadores de los seleccionados
# --------------------------------------------------------------------------- #
def migracion_y_clubes(cfg, d) -> dict[str, pd.DataFrame]:
    s = d[d["club_lat"].notna() & d["lat"].notna()].copy()
    s["km"] = haversine_km(s["lat"].values, s["lon"].values,
                           s["club_lat"].values, s["club_lon"].values)

    grupo = np.where(s["seleccion_mayor"], "Selección Mayor",
                     np.where(s["seleccion_juvenil"], "Juveniles", "Resto de la muestra"))
    s["grupo"] = grupo
    mig = (s.groupby("grupo")
            .agg(jugadores=("player_qid", "size"),
                 km_mediana=("km", "median"),
                 km_p75=("km", lambda x: x.quantile(0.75)),
                 edad_mediana_primer_club=("edad_primer_club", "median"))
            .reset_index())

    col = f"tramo_{cfg['city_size']['default_scheme']}"
    mig_tramo = (s[s["seleccionado"]].groupby(col, observed=False)
                 .agg(seleccionados=("player_qid", "size"),
                      km_mediana=("km", "median"),
                      edad_mediana_primer_club=("edad_primer_club", "median"))
                 .reset_index().rename(columns={col: "tramo"}))

    sel = d[d["seleccionado"] & d["primer_club"].notna()]
    clubes = (sel.groupby("primer_club")
              .agg(seleccionados=("player_qid", "size"),
                   de_los_cuales_mayor=("seleccion_mayor", "sum"))
              .reset_index().sort_values("seleccionados", ascending=False))
    clubes["pct_del_total"] = 100 * clubes["seleccionados"] / clubes["seleccionados"].sum()
    clubes["acumulado_pct"] = clubes["pct_del_total"].cumsum()

    return {"seleccion_migracion": mig,
            "seleccion_migracion_por_tramo": mig_tramo,
            "seleccion_clubes_formadores": clubes}


def main() -> None:
    cfg = load_config()
    p = paths()
    d = cargar(cfg, p)

    ciudades = cargar_ciudades(p)
    denom_dept = cargar_departamentos(p, ["nacimientos_cohorte"])

    log.info("muestra: %d jugadores | Mayor: %d | juveniles: %d | juvenil y Mayor: %d",
             len(d), int(d["seleccion_mayor"].sum()), int(d["seleccion_juvenil"].sum()),
             int((d["seleccion_juvenil"] & d["seleccion_mayor"]).sum()))

    salidas = {}
    salidas |= tasas_de_produccion(cfg, d, ciudades, denom_dept)
    salidas |= conversion(cfg, d)
    salidas |= migracion_y_clubes(cfg, d)

    for nombre, tabla in salidas.items():
        tabla.to_csv(p.tables / f"{nombre}.csv", index=False, encoding="utf-8")
        log.info("  %-40s %3d filas", nombre + ".csv", len(tabla))

    write_run_manifest(p.tables, "run_seleccion",
                       {k: len(v) for k, v in salidas.items()})

    t = salidas["seleccion_conversion_tests"].iloc[0]
    # La consola de Windows es cp1252 y no puede escribir «→».
    log.info("\nCONVERSION JUVENIL -> MAYOR (sin denominador poblacional)")
    log.info("  fuera de un gran aglomerado: %d/%d = %.1f%%",
             t["fuera_metro_llegan"], t["fuera_metro_total"], t["fuera_metro_pct"])
    log.info("  en un gran aglomerado:       %d/%d = %.1f%%",
             t["metro_llegan"], t["metro_total"], t["metro_pct"])
    log.info("  OR = %.2f (IC 95%% %.2f–%.2f), p = %.4f",
             t["OR"], t["OR_ic_lo"], t["OR_ic_hi"], t["p_fisher_exacto"])
    log.info("  OR ajustado por cohorte = %.2f (IC 95%% %.2f–%.2f), p = %.4f",
             t["OR_ajustado_por_cohorte"], t["OR_aj_ic_lo"], t["OR_aj_ic_hi"],
             t["p_ajustado"])


if __name__ == "__main__":
    main()
