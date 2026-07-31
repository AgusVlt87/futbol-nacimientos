"""Fase 7b — El lado futbolístico: clubes formadores, cunas y selección.

Tres preguntas que el análisis geográfico deja planteadas y que se responden
con los mismos datos:

1. **¿Qué clubes forman?** Y sobre todo: ¿de dónde sacan a sus pibes? Un club
   que forma 80 jugadores nacidos a 5 km no hace lo mismo que uno que forma 80
   traídos de 600 km.
2. **¿Cuáles son las cunas?** El ranking de ciudades y departamentos por
   futbolistas cada 100.000 nacidos, que es la pregunta que cualquier hincha
   hace y que sin denominador nadie puede contestar.
3. **¿De dónde sale la selección?** Los jugadores de la mayor son el subconjunto
   con cobertura de datos prácticamente completa: si el patrón se sostiene ahí,
   no lo fabrica Wikidata.

Uso:
    python -m src.analysis.run_futbol
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.analysis.stats import poisson_rate_ci
from src.clean.geo_units import haversine_km
from src.common import get_logger, load_config, paths

log = get_logger("analysis.futbol")
PER = 100_000


# --------------------------------------------------------------------------- #
def clubes_formadores(cfg, players, clubs) -> dict[str, pd.DataFrame]:
    """Ranking de clubes por jugadores formados y por su radio de captación."""
    m = players[players["primer_club_qid"].notna()].merge(
        clubs[["team_qid", "club_dept_id", "club_prov_id", "club_region",
               "club_en_argentina", "team_label"]],
        left_on="primer_club_qid", right_on="team_qid", how="left")
    m = m[m["club_en_argentina"].fillna(False).infer_objects(copy=False)].copy()
    m["km"] = haversine_km(m["lat"].values, m["lon"].values,
                           m["club_lat"].values, m["club_lon"].values)
    m["de_otra_provincia"] = m["prov_id"] != m["club_prov_id"]

    g = m.groupby(["primer_club_qid", "primer_club"]).agg(
        formados=("player_qid", "size"),
        km_mediana=("km", "median"),
        km_p90=("km", lambda s: s.quantile(0.90)),
        pct_de_otra_provincia=("de_otra_provincia", lambda s: 100 * s.mean()),
        provincias_de_origen=("prov_id", "nunique"),
        a_seleccion=("seleccion_mayor", "sum"),
        a_europa_top=("liga_elite_uefa", "sum"),
    ).reset_index()
    g["prov_club"] = g["primer_club_qid"].map(
        clubs.set_index("team_qid")["club_prov_id"])
    g["region_club"] = g["primer_club_qid"].map(
        clubs.set_index("team_qid")["club_region"])
    g = g.sort_values("formados", ascending=False)
    g["reportable"] = g["formados"] >= 10

    # Concentración: cuánto del total forman los pocos de arriba.
    total = g["formados"].sum()
    concentracion = pd.DataFrame([
        {"top_n": n, "clubes": n,
         "formados": int(g.head(n)["formados"].sum()),
         "pct_del_total": 100 * g.head(n)["formados"].sum() / total}
        for n in (5, 10, 20, 50)])
    concentracion["total_jugadores_con_club"] = int(total)
    concentracion["clubes_distintos"] = int(len(g))
    return {"futbol_clubes_formadores": g,
            "futbol_concentracion_clubes": concentracion}


# --------------------------------------------------------------------------- #
def cunas(cfg, players, ciudades, denom_dept) -> dict[str, pd.DataFrame]:
    """Ranking de ciudades y departamentos por futbolistas cada 100.000 nacidos.

    Solo se rankean unidades con al menos `min_n_subgroup` jugadores: con tres
    jugadores nacidos en un pueblo de 900 la tasa da 500 por 100.000 y encabeza
    cualquier ranking sin significar nada.
    """
    min_n = cfg["cohorts"]["min_n_subgroup"]
    level = cfg["stats"]["ci_level"]

    conteo = players.groupby("ciudad_id").size().rename("futbolistas")
    c = ciudades.set_index("ciudad_id").join(conteo).fillna({"futbolistas": 0})
    c = c[c["nacimientos_cohorte"] > 0].reset_index()
    r, lo, hi = poisson_rate_ci(c["futbolistas"], c["nacimientos_cohorte"],
                                per=PER, level=level)
    c["tasa"], c["tasa_ic_lo"], c["tasa_ic_hi"] = r, lo, hi
    c["reportable"] = c["futbolistas"] >= min_n
    ciudades_rank = (c[c["reportable"]].sort_values("tasa", ascending=False)
                     [["ciudad_id", "ciudad_nombre", "prov_id", "pob_ciudad", "tramo",
                       "futbolistas", "nacimientos_cohorte", "tasa",
                       "tasa_ic_lo", "tasa_ic_hi"]])

    dep = pd.read_csv(paths().tables / "h2_departamentos.csv")
    dep_rank = dep[dep["reportable"]].sort_values("tasa", ascending=False)

    return {"futbol_cunas_ciudades": ciudades_rank,
            "futbol_cunas_departamentos": dep_rank}


# --------------------------------------------------------------------------- #
def seleccion(cfg, players, ciudades, denom_dept) -> dict[str, pd.DataFrame]:
    """De dónde salen los que llegan a la mayor.

    Es el control de cobertura del estudio: de los jugadores de la selección
    argentina Wikidata tiene registro prácticamente censal, así que acá el sesgo
    de notoriedad no puede fabricar un patrón geográfico.
    """
    level = cfg["stats"]["ci_level"]
    sel = players[players["seleccion_mayor"]]
    col = f"tramo_{cfg['city_size']['default_scheme']}"

    por_tramo = pd.concat([
        sel.groupby(col, observed=False).size().rename("seleccionados"),
        ciudades.groupby(col, observed=False)["nacimientos_cohorte"].sum()
        .rename("nacimientos")], axis=1).reset_index().rename(columns={col: "tramo"})
    r, lo, hi = poisson_rate_ci(por_tramo["seleccionados"], por_tramo["nacimientos"],
                                per=1_000_000, level=level)
    por_tramo["por_millon"], por_tramo["ic_lo"], por_tramo["ic_hi"] = r, lo, hi

    por_region = pd.concat([
        sel.groupby("region").size().rename("seleccionados"),
        denom_dept.groupby("region")["nacimientos_cohorte"].sum().rename("nacimientos")],
        axis=1).reset_index().rename(columns={"index": "region"})
    r, lo, hi = poisson_rate_ci(por_region["seleccionados"], por_region["nacimientos"],
                                per=1_000_000, level=level)
    por_region["por_millon"], por_region["ic_lo"], por_region["ic_hi"] = r, lo, hi

    origen = (sel.groupby(["localidad_nombre", "prov_nombre"]).size()
              .rename("seleccionados").reset_index()
              .sort_values("seleccionados", ascending=False))

    return {"futbol_seleccion_por_tramo": por_tramo,
            "futbol_seleccion_por_region": por_region.sort_values("por_millon",
                                                                  ascending=False),
            "futbol_seleccion_origenes": origen}


# --------------------------------------------------------------------------- #
def main() -> None:
    cfg = load_config()
    p = paths()
    players = pd.read_parquet(p.processed / "player_level.parquet")
    clubs = pd.read_parquet(p.interim / "clubs_resolved.parquet")
    denom_dept = pd.read_parquet(p.processed / "denom_cohorte_departamento.parquet")
    ciudades = (pd.read_parquet(p.processed / "denom_ciudad_unica.parquet")
                .merge(pd.read_parquet(p.processed / "denom_cohorte_ciudad.parquet"),
                       on="ciudad_id", how="left"))

    salidas = {}
    salidas |= clubes_formadores(cfg, players, clubs)
    salidas |= cunas(cfg, players[players["ciudad_id"].notna()], ciudades, denom_dept)
    salidas |= seleccion(cfg, players, ciudades, denom_dept)

    for nombre, tabla in salidas.items():
        tabla.to_csv(p.tables / f"{nombre}.csv", index=False, encoding="utf-8")
        log.info("  %-38s %4d filas", nombre + ".csv", len(tabla))

    top = salidas["futbol_clubes_formadores"].head(10)
    log.info("\nclubes que más forman:\n%s",
             top[["primer_club", "formados", "km_mediana",
                  "pct_de_otra_provincia"]].round(1).to_string(index=False))


if __name__ == "__main__":
    main()
