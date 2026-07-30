"""Fases 5 y 7 — Nivel competitivo (H4) y flujo nacimiento → formación (H3).

**H4** es, además de una hipótesis, el control del sesgo de cobertura. Wikidata
sobrerrepresenta a los jugadores notables, y ese sesgo podría estar fabricando
el patrón geográfico. Entre los jugadores de la selección mayor la cobertura de
Wikidata es prácticamente censal: si el patrón se sostiene ahí, no lo produce la
cobertura.

**H3** compara la migración de los futbolistas contra la de la población
general. La comparación es lo que la vuelve interpretable: que el 60% de los
futbolistas se forme fuera de su provincia no dice nada hasta saber qué fracción
de los argentinos vive fuera de su provincia de nacimiento — un dato que el
censo 2022 da directamente (variable P14).

Uso:
    python -m src.analysis.run_levels_and_flow
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.analysis.stats import chi2_gof, odds_ratio_ci, poisson_rate_ci, rate_ratio_ci
from src.clean.geo_units import haversine_km
from src.common import get_logger, load_config, paths

log = get_logger("analysis.h3h4")

PER = 100_000


# --------------------------------------------------------------------------- #
# H4 — nivel competitivo
# --------------------------------------------------------------------------- #
def h4_por_nivel(cfg, players, ciudades, denom_dept) -> dict[str, pd.DataFrame]:
    level = cfg["stats"]["ci_level"]
    col = f"tramo_{cfg['city_size']['default_scheme']}"
    pob_tramo = ciudades.groupby(col, observed=False)["pob_cohorte_ciudad"].sum()
    pob_region = denom_dept.groupby("region")["pob_cohorte"].sum()

    filas_tramo, filas_region, tests = [], [], []
    orden = ["T1_seleccion", "T2_europa_top", "T3_primera_ar", "T4_resto"]
    for tier in orden:
        sub = players[players["tier"] == tier]
        if len(sub) < cfg["cohorts"]["min_n_subgroup"]:
            log.info("tier %s: n=%d, por debajo del mínimo; no se reporta", tier, len(sub))
            continue

        obs = sub.groupby(col, observed=False).size().reindex(pob_tramo.index, fill_value=0)
        r, lo, hi = poisson_rate_ci(obs.values, pob_tramo.values, per=PER, level=level)
        ref = cfg["city_size"]["schemes"][cfg["city_size"]["default_scheme"]]["reference_label"]
        rr = [rate_ratio_ci(k, n, obs[ref], pob_tramo[ref], level)
              for k, n in zip(obs.values, pob_tramo.values)]
        filas_tramo.append(pd.DataFrame({
            "tier": tier, "tramo": obs.index, "jugadores": obs.values,
            "poblacion": pob_tramo.values, "pct_jugadores": 100 * obs.values / obs.sum(),
            "tasa": r, "tasa_ic_lo": lo, "tasa_ic_hi": hi,
            "RR_vs_mas_500k": [x[0] for x in rr],
            "RR_ic_lo": [x[1] for x in rr], "RR_ic_hi": [x[2] for x in rr]}))
        g = chi2_gof(obs.values, pob_tramo.values)
        tests.append({"hipotesis": "H4", "variante": f"tamaño de ciudad — {tier}",
                      **g.as_dict()})

        obsr = sub.groupby("region").size().reindex(pob_region.index, fill_value=0)
        r, lo, hi = poisson_rate_ci(obsr.values, pob_region.values, per=PER, level=level)
        filas_region.append(pd.DataFrame({
            "tier": tier, "region": obsr.index, "jugadores": obsr.values,
            "poblacion": pob_region.values, "tasa": r,
            "tasa_ic_lo": lo, "tasa_ic_hi": hi}))
        tests.append({"hipotesis": "H4", "variante": f"regiones — {tier}",
                      **chi2_gof(obsr.values, pob_region.values).as_dict()})

    # ¿El gradiente por tamaño se acentúa con el nivel? Se compara la proporción
    # de nacidos en ciudades chicas (<50k) entre la elite y el resto.
    chicas = players[col].isin(["<10k", "10–50k"])
    elite = players["tier"].isin(["T1_seleccion", "T2_europa_top"])
    a = int((chicas & elite).sum())
    b = int((~chicas & elite).sum())
    c = int((chicas & ~elite).sum())
    d = int((~chicas & ~elite).sum())
    or_, lo_, hi_ = odds_ratio_ci(a, b, c, d, cfg["stats"]["ci_level"])
    contraste = pd.DataFrame([{
        "contraste": "nacidos en ciudades <50k: elite (T1+T2) vs resto (T3+T4)",
        "elite_chicas": a, "elite_grandes": b, "resto_chicas": c, "resto_grandes": d,
        "pct_chicas_elite": 100 * a / max(a + b, 1),
        "pct_chicas_resto": 100 * c / max(c + d, 1),
        "OR": or_, "OR_ic_lo": lo_, "OR_ic_hi": hi_,
        "lectura": ("OR > 1 querría decir que la elite viene más de ciudades chicas; "
                    "un IC que cruza el 1 quiere decir que no hay evidencia de eso"),
    }])

    return {"h4_tramos_por_nivel": pd.concat(filas_tramo, ignore_index=True),
            "h4_regiones_por_nivel": pd.concat(filas_region, ignore_index=True),
            "h4_contraste_elite": contraste,
            "h4_tests": pd.DataFrame(tests)}


# --------------------------------------------------------------------------- #
# H3 — flujo nacimiento → club formador
# --------------------------------------------------------------------------- #
def h3_flujo(cfg, players, clubs, denom_dept) -> dict[str, pd.DataFrame]:
    p = paths()
    # `player_level` ya trae la coordenada del primer club (la puso
    # build_careers); de `clubs_resolved` solo hacen falta las unidades
    # geográficas, o el merge duplica columnas en _x/_y.
    m = players.merge(
        clubs[["team_qid", "club_dept_id", "club_prov_id", "club_region",
               "club_en_argentina"]],
        left_on="primer_club_qid", right_on="team_qid", how="left")
    m["club_en_argentina"] = m["club_en_argentina"].fillna(False).infer_objects(copy=False)

    con_flujo = m[m["primer_club_qid"].notna() & m["club_en_argentina"]
                  & m["dept_id"].notna()].copy()
    log.info("H3: %d jugadores con origen y club formador ubicados (de %d en la muestra)",
             len(con_flujo), len(players))

    con_flujo["cambia_departamento"] = con_flujo["dept_id"] != con_flujo["club_dept_id"]
    con_flujo["cambia_provincia"] = con_flujo["prov_id"] != con_flujo["club_prov_id"]
    con_flujo["cambia_region"] = con_flujo["region"] != con_flujo["club_region"]
    con_flujo["km_hasta_el_club"] = haversine_km(
        con_flujo["lat"].values, con_flujo["lon"].values,
        con_flujo["club_lat"].values, con_flujo["club_lon"].values)

    # --- baseline de la población general -----------------------------------
    # El censo da residentes por departamento según provincia de nacimiento.
    # Agregado a provincia × provincia, es la matriz de migración de toda la
    # población: el punto de comparación que vuelve interpretable el número.
    nac = pd.read_parquet(p.processed / "pop_dept_nacprov.parquet")
    nac = nac[nac["prov_nac_id"] != "99"].copy()
    nac["prov_res_id"] = nac["dept_id"].str[:2]
    pob_total = nac["n"].sum()
    pob_fuera = nac[nac["prov_nac_id"] != nac["prov_res_id"]]["n"].sum()
    pct_pob_fuera = 100 * pob_fuera / pob_total

    pct_jug_fuera = 100 * con_flujo["cambia_provincia"].mean()
    or_, lo_, hi_ = odds_ratio_ci(
        int(con_flujo["cambia_provincia"].sum()),
        int((~con_flujo["cambia_provincia"]).sum()),
        int(pob_fuera), int(pob_total - pob_fuera), cfg["stats"]["ci_level"])
    comparacion = pd.DataFrame([
        {"grupo": "Futbolistas (nacimiento → club formador)",
         "n": len(con_flujo), "pct_fuera_de_su_provincia": pct_jug_fuera},
        {"grupo": "Población general (nacimiento → residencia, Censo 2022)",
         "n": int(pob_total), "pct_fuera_de_su_provincia": pct_pob_fuera},
        {"grupo": "Odds ratio futbolistas vs población general",
         "n": np.nan, "pct_fuera_de_su_provincia": np.nan,
         "OR": or_, "OR_ic_lo": lo_, "OR_ic_hi": hi_},
    ])

    # --- migración por origen ------------------------------------------------
    col = f"tramo_{cfg['city_size']['default_scheme']}"
    por_tamano = (con_flujo.groupby(col, observed=False)
                  .agg(jugadores=("player_qid", "size"),
                       pct_cambia_departamento=("cambia_departamento", lambda s: 100 * s.mean()),
                       pct_cambia_provincia=("cambia_provincia", lambda s: 100 * s.mean()),
                       km_mediana=("km_hasta_el_club", "median"))
                  .reset_index().rename(columns={col: "tramo"}))

    por_region = (con_flujo.groupby("region")
                  .agg(jugadores=("player_qid", "size"),
                       pct_cambia_provincia=("cambia_provincia", lambda s: 100 * s.mean()),
                       pct_cambia_region=("cambia_region", lambda s: 100 * s.mean()),
                       km_mediana=("km_hasta_el_club", "median"))
                  .reset_index())

    # --- matriz de flujo región → región -------------------------------------
    matriz = pd.crosstab(con_flujo["region"], con_flujo["club_region"],
                         rownames=["region_nacimiento"], colnames=["region_club"])
    matriz_pct = (100 * matriz.div(matriz.sum(axis=1), axis=0)).round(1)

    # --- saldo neto por región ----------------------------------------------
    salen = con_flujo.groupby("region").size().rename("nacidos")
    llegan = con_flujo.groupby("club_region").size().rename("formados")
    saldo = pd.concat([salen, llegan], axis=1).fillna(0)
    saldo["saldo_neto"] = saldo["formados"] - saldo["nacidos"]
    saldo["retenidos"] = con_flujo[~con_flujo["cambia_region"]].groupby("region").size()
    saldo["pct_retencion"] = (100 * saldo["retenidos"] / saldo["nacidos"]).round(1)

    return {
        "h3_migracion_vs_poblacion": comparacion,
        "h3_migracion_por_tamano_origen": por_tamano,
        "h3_migracion_por_region_origen": por_region,
        "h3_matriz_flujo_regiones": matriz.reset_index(),
        "h3_matriz_flujo_regiones_pct": matriz_pct.reset_index(),
        "h3_saldo_por_region": saldo.reset_index().rename(columns={"index": "region"}),
    }


def main() -> None:
    cfg = load_config()
    p = paths()
    players = pd.read_parquet(p.processed / "player_level.parquet")
    ciudades = pd.read_parquet(p.processed / "denom_ciudad_unica.parquet")
    denom_dept = pd.read_parquet(p.processed / "denom_departamento.parquet")
    clubs = pd.read_parquet(p.interim / "clubs_resolved.parquet")

    salidas = {}
    salidas |= h4_por_nivel(cfg, players[players["ciudad_id"].notna()], ciudades, denom_dept)
    salidas |= h3_flujo(cfg, players, clubs, denom_dept)

    for nombre, tabla in salidas.items():
        tabla.to_csv(p.tables / f"{nombre}.csv", index=False, encoding="utf-8")
        log.info("  %-38s %3d filas", nombre + ".csv", len(tabla))


if __name__ == "__main__":
    main()
