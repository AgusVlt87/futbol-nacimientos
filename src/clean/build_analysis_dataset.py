"""Fase 3 — Dataset de análisis: jugadores con su geografía y su denominador.

Une jugadores + lugares resueltos + unidades censales, y arma los denominadores
emparejados por cohorte. La regla de emparejamiento es explícita: para la
cohorte nacida en el año Y, el denominador es la población de edad
(2022 − Y) en el censo 2022. Ese es el sentido de `census_cohort`.

Salidas en `data/processed/`:
    analysis_players.parquet   una fila por jugador de la muestra de análisis
    denom_departamento.parquet población por departamento para la ventana
    denom_ciudad.parquet       población por localidad/aglomerado y su tramo
    outputs/tables/qa_muestra_analisis.csv

Uso:
    python -m src.clean.build_analysis_dataset
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.clean.geo_units import city_size_series, region_of
from src.common import get_logger, load_config, paths

log = get_logger("clean.dataset")

CENSO_YEAR = 2022


def cohort_ages(cfg: dict) -> tuple[int, int]:
    """Rango de edades en 2022 que corresponde a la ventana de cohortes."""
    c = cfg["cohorts"]
    return CENSO_YEAR - c["analysis_max_year"], CENSO_YEAR - c["analysis_min_year"]


def main() -> None:
    cfg = load_config()
    p = paths()

    players = pd.read_parquet(p.interim / "players.parquet")
    places = pd.read_parquet(p.interim / "places_resolved.parquet")
    tamano = pd.read_parquet(p.processed / "tamano_localidad.parquet")

    df = players.merge(
        places[["place_qid", "label", "granularity", "geo_status", "prov_id", "prov_nombre",
                "dept_id", "dept_nombre", "localidad_id", "localidad_nombre",
                "localidad_match", "lat", "lon"]],
        left_on="birthplace_qid", right_on="place_qid", how="left")

    qa: list[dict] = [{"paso": "jugadores con lugar de nacimiento", "n": len(df)}]

    def step(mask: pd.Series, label: str) -> None:
        nonlocal df
        before = len(df)
        df = df[mask].copy()
        qa.append({"paso": label, "n": len(df), "descartados": before - len(df)})

    step(df["geo_status"].eq("ok"), "lugar resuelto dentro de Argentina")

    c = cfg["cohorts"]
    step(df["birth_year"].between(c["analysis_min_year"], c["analysis_max_year"]),
         f"cohorte {c['analysis_min_year']}–{c['analysis_max_year']}")

    # --- atributos geográficos ---------------------------------------------
    df["region"] = df["dept_id"].map(lambda d: region_of(d, cfg))
    df = df.merge(tamano[["localidad_id", "pob_localidad", "pob_ciudad",
                          "aglomerado_id", "aglomerado_nombre"]],
                  on="localidad_id", how="left")

    scheme_name = cfg["city_size"]["default_scheme"]
    for name, scheme in cfg["city_size"]["schemes"].items():
        df[f"tramo_{name}"] = city_size_series(df["pob_ciudad"], scheme)
    df["tramo"] = df[f"tramo_{scheme_name}"]

    df["edad_censo_2022"] = CENSO_YEAR - df["birth_year"]
    df["decada"] = (df["birth_year"] // 10) * 10

    out = p.processed / "analysis_players.parquet"
    df.to_parquet(out, index=False)

    # --- denominadores ------------------------------------------------------
    a0, a1 = cohort_ages(cfg)
    log.info("ventana de cohortes -> edades %d–%d en el censo %d", a0, a1, CENSO_YEAR)

    dept_edad = pd.read_parquet(p.processed / "pop_dept_edad.parquet")
    denom_dept = (dept_edad[dept_edad["edad"].between(a0, a1)]
                  .groupby("dept_id", as_index=False)["n"].sum()
                  .rename(columns={"n": "pob_cohorte"}))
    dept_total = dept_edad.groupby("dept_id", as_index=False)["n"].sum() \
                          .rename(columns={"n": "pob_total"})
    denom_dept = denom_dept.merge(dept_total, on="dept_id", how="outer")
    denom_dept["region"] = denom_dept["dept_id"].map(lambda d: region_of(d, cfg))
    denom_dept["prov_id"] = denom_dept["dept_id"].str[:2]
    denom_dept.to_parquet(p.processed / "denom_departamento.parquet", index=False)

    loc_edad = pd.read_parquet(p.processed / "pop_localidad_edad.parquet")
    aglo_edad = pd.read_parquet(p.processed / "pop_aglomerado_edad.parquet")
    loc_coh = (loc_edad[loc_edad["edad"].between(a0, a1)]
               .groupby("localidad_id", as_index=False)["n"].sum()
               .rename(columns={"n": "pob_cohorte_localidad"}))
    aglo_coh = (aglo_edad[aglo_edad["edad"].between(a0, a1)]
                .groupby("aglomerado_id", as_index=False)["n"].sum()
                .rename(columns={"n": "pob_cohorte_aglomerado"}))

    ciudad = (tamano.merge(loc_coh, on="localidad_id", how="left")
                    .merge(aglo_coh, on="aglomerado_id", how="left"))
    # La cohorte de la "ciudad": el aglomerado si existe, si no la localidad.
    ciudad["pob_cohorte_ciudad"] = ciudad["pob_cohorte_aglomerado"].fillna(
        ciudad["pob_cohorte_localidad"])
    for name, scheme in cfg["city_size"]["schemes"].items():
        ciudad[f"tramo_{name}"] = city_size_series(ciudad["pob_ciudad"], scheme)
    ciudad["tramo"] = ciudad[f"tramo_{scheme_name}"]
    ciudad.to_parquet(p.processed / "denom_ciudad.parquet", index=False)

    qa_df = pd.DataFrame(qa)
    qa_df["pct_restante"] = (100 * qa_df["n"] / qa_df["n"].iloc[0]).round(1)
    qa_df.to_csv(p.tables / "qa_muestra_analisis.csv", index=False, encoding="utf-8")

    log.info("\n%s", qa_df.to_string(index=False))
    log.info("sin tramo de tamaño (granularidad > localidad): %d de %d",
             df["tramo"].isna().sum(), len(df))
    log.info("guardado: %s", out)


if __name__ == "__main__":
    main()
