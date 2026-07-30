"""Fase 3 — Puente entre el padrón Georef y las localidades del Censo 2022.

**Por qué existe este módulo.** Los ids de `localidades_censales` de Georef son
los del Censo 2010 y el Censo 2022 renumeró: en el departamento de Olavarría,
Georef dice que 06595080 es Olavarría, mientras que para el censo 2022 esa
ciudad es 06595070 y 06595080 es Recalde. Unir por id da poblaciones de otra
localidad — un error silencioso que convierte una ciudad de 100.000 en un
pueblo de 350.

El puente se arma por **departamento + nombre normalizado**, que es estable
entre censos, y se valida contando cuánto queda sin emparejar.

El censo 2022 además agrega pseudo-localidades «ZONA RURAL» por departamento,
donde agrupa la población rural dispersa. No son localidades y no existen en
Georef: se marcan aparte porque nadie «nace en la zona rural» según Wikidata,
pero su población sí cuenta en el denominador.

Salidas: `data/interim/crosswalk_localidades.parquet`
         `outputs/tables/qa_crosswalk_localidades.csv`

Uso:
    python -m src.clean.crosswalk_localidades
"""

from __future__ import annotations

import json

import pandas as pd

from src.clean.geo_units import normalize_name
from src.common import get_logger, load_config, paths

log = get_logger("clean.crosswalk")

ZONA_RURAL = "ZONA RURAL"


def censo_localidades(processed) -> pd.DataFrame:
    geo = pd.read_parquet(processed / "radio_geo.parquet")
    loc = (geo.groupby(["localidad_id", "localidad_nombre"], as_index=False)
              .size().rename(columns={"size": "n_radios"}))
    loc["dept_id_censo"] = loc["localidad_id"].str[:5]
    loc["nombre_norm"] = loc["localidad_nombre"].map(normalize_name)
    loc["es_zona_rural"] = loc["localidad_nombre"].str.upper().eq(ZONA_RURAL)
    return loc


def georef_localidades(raw) -> pd.DataFrame:
    items = json.loads((raw / "georef" / "localidades_censales.json").read_text(encoding="utf-8"))["items"]
    df = pd.DataFrame({
        "georef_id": [i["id"] for i in items],
        "georef_nombre": [i["nombre"] for i in items],
        "dept_id_georef": [i["departamento"]["id"] for i in items],
        "lat": [i["centroide"]["lat"] for i in items],
        "lon": [i["centroide"]["lon"] for i in items],
    })
    df["nombre_norm"] = df["georef_nombre"].map(normalize_name)
    return df


def build(censo: pd.DataFrame, georef: pd.DataFrame) -> pd.DataFrame:
    """Empareja por departamento + nombre normalizado.

    Se exige que el nombre sea único dentro del departamento en ambos padrones:
    si hay ambigüedad se deja sin emparejar en vez de elegir al azar.
    """
    c = censo[~censo["es_zona_rural"]].copy()
    g = georef.copy()

    c_key = c.groupby(["dept_id_censo", "nombre_norm"])["localidad_id"].nunique()
    g_key = g.groupby(["dept_id_georef", "nombre_norm"])["georef_id"].nunique()
    c_unico = set(c_key[c_key == 1].index)
    g_unico = set(g_key[g_key == 1].index)

    merged = g.merge(c, left_on=["dept_id_georef", "nombre_norm"],
                     right_on=["dept_id_censo", "nombre_norm"], how="left")
    ambiguo = ~merged.apply(
        lambda r: (r["dept_id_georef"], r["nombre_norm"]) in g_unico
        and (r["dept_id_georef"], r["nombre_norm"]) in c_unico, axis=1)
    merged.loc[ambiguo, ["localidad_id", "localidad_nombre"]] = None

    merged["match"] = merged["localidad_id"].notna().map(
        {True: "depto_y_nombre", False: "sin_correspondencia"})
    return merged[["georef_id", "georef_nombre", "dept_id_georef", "lat", "lon",
                   "nombre_norm", "localidad_id", "localidad_nombre", "match"]]


def main() -> None:
    load_config()
    p = paths()

    censo = censo_localidades(p.processed)
    georef = georef_localidades(p.raw)
    cw = build(censo, georef)

    cw.to_parquet(p.interim / "crosswalk_localidades.parquet", index=False)

    emparejadas = cw["localidad_id"].notna().sum()
    censo_reales = (~censo["es_zona_rural"]).sum()
    qa = pd.DataFrame([
        {"concepto": "localidades en Georef (censo 2010)", "n": len(georef)},
        {"concepto": "localidades en el Censo 2022", "n": int(censo_reales)},
        {"concepto": "pseudo-localidades ZONA RURAL (censo 2022)",
         "n": int(censo["es_zona_rural"].sum())},
        {"concepto": "emparejadas por departamento + nombre", "n": int(emparejadas)},
        {"concepto": "Georef sin correspondencia en el censo 2022",
         "n": int(len(cw) - emparejadas)},
        {"concepto": "localidades del censo 2022 sin par en Georef",
         "n": int(censo_reales - cw["localidad_id"].nunique())},
    ])
    qa["pct_georef"] = (100 * qa["n"] / len(georef)).round(1)
    qa.to_csv(p.tables / "qa_crosswalk_localidades.csv", index=False, encoding="utf-8")

    log.info("\n%s", qa.to_string(index=False))
    ejemplo = cw[cw["georef_nombre"].str.startswith("Olavarr", na=False)]
    log.info("control Olavarría:\n%s", ejemplo[["georef_id", "georef_nombre",
                                                "localidad_id", "localidad_nombre"]]
             .to_string(index=False))


if __name__ == "__main__":
    main()
