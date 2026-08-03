"""Fase 10 — Test placebo: ¿la geografía es del fútbol o del país?

**La pregunta.** Todo el trabajo mide dónde nacen los futbolistas contra dónde
nacen los argentinos. Lo que no puede contestar solo es si el patrón que
encuentra es **del fútbol** o es el de cualquier actividad registrada: dónde hay
clase media, dónde hay infraestructura deportiva de cualquier tipo, dónde
Wikipedia tiene editores que escriben biografías.

**El diseño.** Se corre exactamente el mismo análisis sobre deportistas
argentinos de otros deportes: misma ventana de cohortes, misma cadena de
geocoding, mismo denominador de nacidos vivos, mismos tramos de tamaño. Lo único
que cambia es el deporte.

**Qué se compara.** No las tasas —no son comparables entre deportes, porque la
cobertura de Wikidata es muy distinta— sino la **forma**: el cociente entre la
proporción observada y la esperada por nacimientos, tramo por tramo y región por
región. Y un test de homogeneidad entre la distribución del fútbol y la de cada
placebo.

    Si la forma es la misma  -> se está midiendo algo general (infraestructura,
                                registro, cobertura), no algo futbolístico.
    Si la forma es distinta  -> hay algo específico del fútbol.

Las dos respuestas son informativas y las dos cambian el paper.

Salidas en `outputs/tables/`:
    placebo_muestras.csv
    placebo_por_tramo.csv
    placebo_por_region.csv
    placebo_tests_homogeneidad.csv

Uso:
    python -m src.analysis.run_placebo
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
from scipy import stats

from src.analysis.stats import poisson_rate_ci
from src.clean.geo_units import city_size_series, collapse_caba, region_of
from src.clean.geocode_places import (
    assign_localidad,
    collapse_places,
    granularity,
    reverse_geocode,
)
from src.common import get_logger, load_config, paths, write_run_manifest
from src.denominadores import cargar_ciudades

log = get_logger("analysis.placebo")

GENERO_MASCULINO = "Q6581097"
GENERO_FEMENINO = "Q6581072"
ORDEN_TRAMOS = ["<10k", "10–50k", "50–100k", "100–500k", ">500k"]


# --------------------------------------------------------------------------- #
# Resolución geográfica de los lugares nuevos
# --------------------------------------------------------------------------- #
def lugares_resueltos(cfg, p) -> pd.DataFrame:
    """Los lugares ya resueltos por el pipeline del fútbol, más los nuevos.

    Los nuevos pasan por exactamente la misma cadena: granularidad, geocoding
    inverso contra Georef y asignación de localidad censal por cercanía dentro
    del departamento. Si la cadena fuera distinta, la comparación no valdría.
    """
    base = pd.read_parquet(p.interim / "places_resolved.parquet")
    crudo = json.loads((p.raw / "wikidata" / "placebo" / "places.json")
                       .read_text(encoding="utf-8"))["bindings"]
    if not crudo:
        return base

    nuevos = collapse_places(crudo)
    nuevos["granularity"] = nuevos["types"].apply(granularity)
    geo = cfg["geography"]["geocoder"]
    nuevos = nuevos.merge(
        reverse_geocode(nuevos, geo["base_url"], cfg["ingest"]["georef"]["batch_size"]),
        on="place_qid", how="left")

    cw = pd.read_parquet(p.interim / "crosswalk_localidades.parquet")
    localidades = pd.DataFrame({"id": cw["georef_id"], "nombre": cw["georef_nombre"],
                                "dept_id_raw": cw["dept_id_georef"], "lat": cw["lat"],
                                "lon": cw["lon"], "censo_localidad_id": cw["localidad_id"]})
    nuevos = nuevos.merge(assign_localidad(nuevos, localidades), on="place_qid", how="left")
    nuevos["dept_id"] = nuevos["dept_id_raw"].apply(collapse_caba)
    demasiado_grueso = nuevos["granularity"].isin(["pais", "region", "provincia"])
    nuevos.loc[demasiado_grueso, ["dept_id", "dept_id_raw"]] = None
    nuevos["geo_status"] = np.where(nuevos["prov_id"].notna(), "ok", "fuera_de_argentina")

    comunes = [c for c in base.columns if c in nuevos.columns]
    log.info("lugares nuevos resueltos: %d (%d dentro de Argentina)",
             len(nuevos), int((nuevos["geo_status"] == "ok").sum()))
    return pd.concat([base[comunes], nuevos[comunes]], ignore_index=True)


def bindings_futbol_femenino(p, cfg) -> list[dict]:
    """Futbolistas mujeres, desde el crudo del fútbol.

    `players.parquet` viene filtrado a varones (`sample.gender_filter`), así que
    la muestra femenina hay que sacarla del JSON crudo. Es el mismo corpus y la
    misma consulta: el único filtro que cambia es el sexo.
    """
    c = cfg["cohorts"]
    y0, y1 = c["analysis_min_year"], c["analysis_max_year"]
    out = []
    for f in sorted((p.raw / "wikidata" / "players").glob("*.json")):
        if not (y0 <= int(f.stem) <= y1):
            continue
        out += json.loads(f.read_text(encoding="utf-8"))["bindings"]
    return out


def cargar_deporte(deporte: str, p, cfg, places: pd.DataFrame,
                   tamano: pd.DataFrame, genero: str | None = None,
                   bindings: list[dict] | None = None) -> pd.DataFrame:
    if bindings is None:
        ruta = p.raw / "wikidata" / "placebo" / f"{deporte}.json"
        bindings = json.loads(ruta.read_text(encoding="utf-8"))["bindings"]
    filas = {}
    for b in bindings:
        # En el crudo del fútbol el P19 es OPTIONAL: sin lugar de nacimiento el
        # jugador no entra al análisis geográfico.
        if "birthplace" not in b:
            continue
        q = b["player"]["value"].rsplit("/", 1)[-1]
        filas.setdefault(q, {
            "player_qid": q,
            "nombre": b.get("playerLabel", {}).get("value"),
            "birth_year": int(b["dob"]["value"][:4]),
            "dob_precision": int(b["dobPrec"]["value"]),
            "gender_qid": b.get("gender", {}).get("value", "").rsplit("/", 1)[-1] or None,
            "birthplace_qid": b["birthplace"]["value"].rsplit("/", 1)[-1],
            "sitelinks": int(b["sitelinks"]["value"]),
        })
    d = pd.DataFrame(filas.values())
    # Mismos filtros que la muestra de fútbol: precisión de fecha y sexo.
    d = d[d["dob_precision"] >= 9]
    d = d[d["birth_year"].between(cfg["cohorts"]["analysis_min_year"],
                                  cfg["cohorts"]["analysis_max_year"])]
    objetivo = genero or (GENERO_MASCULINO if cfg["sample"]["gender_filter"] == "male"
                          else None)
    if objetivo:
        d = d[d["gender_qid"] == objetivo]

    d = d.merge(places[["place_qid", "granularity", "geo_status", "prov_id",
                        "dept_id", "localidad_id"]],
                left_on="birthplace_qid", right_on="place_qid", how="left")
    d = d[d["geo_status"].eq("ok")]
    d["region"] = d["dept_id"].map(lambda x: region_of(x, cfg))
    d = d.merge(tamano[["localidad_id", "pob_ciudad", "aglomerado_id"]],
                on="localidad_id", how="left")
    esquema = cfg["city_size"]["schemes"][cfg["city_size"]["default_scheme"]]
    d["tramo"] = city_size_series(d["pob_ciudad"], esquema)
    d["ciudad_id"] = np.where(d["aglomerado_id"].notna(),
                              "AGLO_" + d["aglomerado_id"].astype(str),
                              "LOC_" + d["localidad_id"].astype(str))
    d["deporte"] = deporte
    return d


# --------------------------------------------------------------------------- #
# Comparación de formas
# --------------------------------------------------------------------------- #
def forma(d: pd.DataFrame, col: str, denom: pd.Series, orden: list[str]) -> pd.DataFrame:
    """Observado sobre esperado por nacimientos, categoría por categoría.

    Se reportan además tasas por millón con IC exacto de Poisson. Las tasas **no**
    son comparables entre deportes —la cobertura de Wikidata es muy distinta— pero
    sí lo son dentro de un deporte, y son las que permiten poner un intervalo
    alrededor de la forma en vez de leer un cociente pelado.
    """
    obs = d.groupby(col, observed=False).size().reindex(orden).fillna(0)
    nac = denom.reindex(orden)
    tasa, lo, hi = poisson_rate_ci(obs.values, nac.values, per=1e6)
    out = pd.DataFrame({col: orden, "n": obs.values, "nacimientos": nac.values,
                        "pct_observado": (obs / obs.sum() * 100).values,
                        "pct_esperado": (nac / nac.sum() * 100).values,
                        "tasa_por_millon": tasa, "tasa_ic_lo": lo, "tasa_ic_hi": hi})
    out["obs_sobre_esp"] = out["pct_observado"] / out["pct_esperado"]
    return out


def contraste_optimo(d: pd.DataFrame, denom: pd.Series, deporte: str) -> dict:
    """El contraste que define el *birthplace effect*: 50–100k contra la metrópoli.

    Côté et al. (2006) sitúan el óptimo entre 50.000 y 100.000 habitantes. Un RR
    mayor que 1 es el efecto clásico; menor que 1, su inverso. Es la comparación
    que separa a los deportes entre sí.
    """
    obs = d.groupby("tramo", observed=False).size().reindex(ORDEN_TRAMOS).fillna(0)
    n1, n2 = float(obs["50–100k"]), float(obs[">500k"])
    d1, d2 = float(denom["50–100k"]), float(denom[">500k"])
    if n1 == 0 or n2 == 0:
        return {"deporte": deporte, "n_50_100k": int(n1), "n_mas_500k": int(n2),
                "RR": np.nan, "RR_ic_lo": np.nan, "RR_ic_hi": np.nan}
    rr = (n1 / d1) / (n2 / d2)
    se = np.sqrt(1 / n1 + 1 / n2)
    return {"deporte": deporte, "n_50_100k": int(n1), "n_mas_500k": int(n2),
            "tasa_50_100k_por_millon": n1 / d1 * 1e6,
            "tasa_mas_500k_por_millon": n2 / d2 * 1e6,
            "RR": rr, "RR_ic_lo": rr * np.exp(-1.96 * se),
            "RR_ic_hi": rr * np.exp(1.96 * se),
            "lectura": ("RR > 1 = birthplace effect clásico (el óptimo de Côté "
                        "et al. 2006); RR < 1 = efecto invertido")}


def homogeneidad(a: pd.Series, b: pd.Series, etiqueta: str) -> dict:
    """Chi-cuadrado de homogeneidad entre dos distribuciones categóricas.

    La hipótesis nula es que los dos deportes se reparten igual entre las
    categorías. **No rechazar no prueba que sean iguales**, sobre todo con las
    muestras chicas de los placebos; por eso se reporta también el tamaño de
    efecto (V de Cramér), que no depende de n del mismo modo.
    """
    tabla = np.vstack([a.values, b.values])
    tabla = tabla[:, tabla.sum(axis=0) > 0]
    chi2, pval, gl, _ = stats.chi2_contingency(tabla)
    n = tabla.sum()
    v = float(np.sqrt(chi2 / (n * (min(tabla.shape) - 1))))
    return {"contraste": etiqueta, "chi2": float(chi2), "gl": int(gl), "p": float(pval),
            "n": int(n), "cramers_v": v,
            "lectura": ("p alto = no se puede distinguir la forma de los dos deportes; "
                        "con muestras chicas eso es poco informativo, mirar V")}


def main() -> None:
    cfg = load_config()
    p = paths()
    places = lugares_resueltos(cfg, p)
    tamano = pd.read_parquet(p.processed / "tamano_localidad.parquet")

    futbol = pd.read_parquet(p.processed / "analysis_players.parquet")
    futbol["deporte"] = "futbol"

    ciudades = cargar_ciudades(p)
    denom_tramo = ciudades.groupby("tramo", observed=False)["nacimientos_cohorte"].sum()
    denom_dept = pd.read_parquet(p.processed / "denom_cohorte_departamento.parquet")
    denom_region = denom_dept.groupby("region")["nacimientos_cohorte"].sum()
    orden_regiones = list(denom_region.sort_values(ascending=False).index)

    deportes = ["basquet", "rugby", "voley", "hockey"]
    muestras = {"futbol": futbol}
    for dep in deportes:
        muestras[dep] = cargar_deporte(dep, p, cfg, places, tamano)
    # Fútbol femenino: mismo corpus y misma consulta que la muestra principal,
    # con el único filtro de sexo cambiado. Es un contraste de infraestructura
    # —el fútbol femenino argentino se profesionalizó recién en 2019— dentro del
    # mismo deporte, no un placebo.
    muestras["futbol_femenino"] = cargar_deporte(
        "futbol_femenino", p, cfg, places, tamano, genero=GENERO_FEMENINO,
        bindings=bindings_futbol_femenino(p, cfg))

    resumen, formas_t, formas_r, tests, optimos = [], [], [], [], []
    ref_t = futbol.groupby("tramo", observed=False).size().reindex(ORDEN_TRAMOS).fillna(0)
    ref_r = futbol.groupby("region", observed=False).size().reindex(orden_regiones).fillna(0)

    for nombre, d in muestras.items():
        con_tramo = d[d["tramo"].notna()]
        con_region = d[d["region"].notna()]
        resumen.append({"deporte": nombre, "n_total": len(d),
                        "n_con_tramo": len(con_tramo), "n_con_region": len(con_region),
                        "pct_en_mas_500k": float(
                            (con_tramo["tramo"] == ">500k").mean() * 100) if len(con_tramo) else np.nan,
                        "pct_en_AMBA": float(
                            (con_region["region"] == "AMBA").mean() * 100) if len(con_region) else np.nan})
        formas_t.append(forma(con_tramo, "tramo", denom_tramo, ORDEN_TRAMOS)
                        .assign(deporte=nombre))
        formas_r.append(forma(con_region, "region", denom_region, orden_regiones)
                        .assign(deporte=nombre))
        optimos.append(contraste_optimo(con_tramo, denom_tramo, nombre))
        if nombre == "futbol":
            continue
        tests.append(homogeneidad(
            ref_t, con_tramo.groupby("tramo", observed=False).size().reindex(ORDEN_TRAMOS).fillna(0),
            f"fútbol vs {nombre} — tamaño de ciudad"))
        tests.append(homogeneidad(
            ref_r, con_region.groupby("region", observed=False).size().reindex(orden_regiones).fillna(0),
            f"fútbol vs {nombre} — región"))

    salidas = {
        "placebo_muestras": pd.DataFrame(resumen),
        "placebo_por_tramo": pd.concat(formas_t, ignore_index=True),
        "placebo_por_region": pd.concat(formas_r, ignore_index=True),
        "placebo_tests_homogeneidad": pd.DataFrame(tests),
        "placebo_contraste_optimo": pd.DataFrame(optimos),
    }
    for nombre, tabla in salidas.items():
        tabla.to_csv(p.tables / f"{nombre}.csv", index=False, encoding="utf-8")
        log.info("%-34s %3d filas", nombre + ".csv", len(tabla))

    write_run_manifest(p.tables, "run_placebo",
                       {k: len(v) for k, v in salidas.items()})

    log.info("\n%s", salidas["placebo_muestras"].round(1).to_string(index=False))
    log.info("\n%s", salidas["placebo_tests_homogeneidad"]
             .drop(columns="lectura").round(4).to_string(index=False))


if __name__ == "__main__":
    main()
