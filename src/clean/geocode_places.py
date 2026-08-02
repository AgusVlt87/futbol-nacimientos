"""Fase 3 — Resolución de los lugares de nacimiento a unidades oficiales.

El problema: los nombres de lugares argentinos en Wikidata vienen inconsistentes
(homónimos entre provincias, variantes ortográficas, a veces la provincia en vez
de la ciudad). Resolverlos por string es una fuente de error garantizada.

La solución: resolver por **coordenada** (`P625`) contra la API Georef, que
devuelve el departamento y la provincia oficiales. El nombre solo se usa como
chequeo cruzado al asignar la localidad censal.

La granularidad importa. Wikidata mezcla ciudades con provincias y partidos: si
el lugar de nacimiento es "Provincia de Buenos Aires", su coordenada es un
centroide y asignarle una localidad sería inventar un dato. Esos casos se
resuelven solo hasta el nivel que corresponde y se marcan.

Salida: `data/interim/places_resolved.parquet`
        `outputs/tables/qa_geocoding.csv`

Uso:
    python -m src.clean.geocode_places [--force]
"""

from __future__ import annotations

import argparse
import json

import numpy as np
import pandas as pd
import requests

from src.clean.geo_units import collapse_caba, haversine_km, normalize_name
from src.common import get_logger, load_config, paths
from src.ingest.download import UA

log = get_logger("clean.geocode")

# Tipos (P31) que indican que la entidad NO es una localidad sino una unidad
# administrativa mayor. El orden es de más grueso a más fino.
#
# El caso país no es teórico: 255 jugadores de la muestra tienen como lugar de
# nacimiento la entidad «Argentina» (Q414). Su coordenada es el centroide del
# país, que cae en el departamento Presidente Roque Sáenz Peña de Córdoba: sin
# este filtro, un pueblo de 5.674 habitantes aparecía como la tercera cuna de
# futbolistas del país.
COUNTRY_TYPES = {"Q6256",        # país
                 "Q3624078",     # estado soberano
                 "Q10551526",    # estado unitario / república federal
                 "Q6266"}        # nación
PROVINCE_TYPES = {"Q44753"}                    # provincia de Argentina
DEPARTMENT_TYPES = {"Q952274",                 # departamento de Argentina
                    "Q13997861"}               # partido de la provincia de Buenos Aires

# Entidades poblacionales legítimas: ciudad, pueblo, barrio, municipio, etc.
LOCALITY_TYPES = {
    "Q515", "Q5770918", "Q3257686", "Q486972", "Q15284", "Q3243765", "Q532",
    "Q3957", "Q1549591", "Q851517", "Q123705", "Q902814", "Q15303838", "Q1901835",
}

# Regiones y aglomerados sin límites administrativos: "Cuyo", "Gran Buenos
# Aires". El centroide de una región no ubica a nadie; se excluyen del análisis
# geográfico en vez de asignarles un departamento arbitrario.
REGION_TYPES = {"Q82794",      # región geográfica
                "Q159313",     # aglomeración urbana
                "Q174844",     # megaciudad
                "Q1907114"}    # área metropolitana

# CABA no aparece en la capa de localidades censales de Georef: el INDEC la
# trata como una jurisdicción entera. Se la representa como una localidad
# única, que es lo que es a efectos de "tamaño de ciudad".
CABA_LOCALIDAD_ID = "02000010"
CABA_LOCALIDAD_NOMBRE = "Ciudad Autónoma de Buenos Aires"

# Distancia máxima entre el punto de nacimiento y el centroide de la localidad
# censal para aceptar la asignación sin coincidencia de nombre. Por encima, la
# localidad queda sin asignar: es preferible un faltante a un dato inventado.
MAX_LOCALIDAD_KM = 25.0


def collapse_places(bindings: list[dict]) -> pd.DataFrame:
    """Una fila por lugar, con tipos y poblaciones agregadas."""
    acc: dict[str, dict] = {}
    for b in bindings:
        q = b["item"]["value"].rsplit("/", 1)[-1]
        rec = acc.setdefault(q, {"place_qid": q, "label": None, "lat": None, "lon": None,
                                 "country_qid": None, "types": set(), "admin_qids": set(),
                                 "pops": []})
        rec["label"] = rec["label"] or b.get("itemLabel", {}).get("value")
        if rec["lat"] is None and "coord" in b:
            # Formato "Point(lon lat)". Wikidata también admite «valor
            # desconocido», que llega como nodo en blanco: se ignora.
            raw = b["coord"]["value"]
            if raw.startswith("Point("):
                lon, lat = raw.removeprefix("Point(").removesuffix(")").split()
                rec["lat"], rec["lon"] = float(lat), float(lon)
        if "country" in b:
            rec["country_qid"] = b["country"]["value"].rsplit("/", 1)[-1]
        if "type" in b:
            rec["types"].add(b["type"]["value"].rsplit("/", 1)[-1])
        if "admin" in b:
            rec["admin_qids"].add(b["admin"]["value"].rsplit("/", 1)[-1])
        if "pop" in b:
            rec["pops"].append((b.get("popDate", {}).get("value", ""), float(b["pop"]["value"])))

    rows = []
    for rec in acc.values():
        pops = sorted(rec["pops"])
        rows.append({**{k: v for k, v in rec.items() if k not in {"types", "admin_qids", "pops"}},
                     "types": sorted(rec["types"]),
                     "admin_qids": sorted(rec["admin_qids"]),
                     "wikidata_pop": pops[-1][1] if pops else np.nan,
                     "wikidata_pop_date": pops[-1][0][:10] if pops else None})
    return pd.DataFrame(rows)


def granularity(types: list[str]) -> str:
    """Nivel geográfico real de la entidad, de más grueso a más fino.

    Provincia y departamento ganan sobre localidad: si el ítem es el partido y
    no la ciudad, su coordenada es un centroide y tratarlo como localidad
    inventaría precisión. `region` es el caso irrecuperable (Cuyo, Gran Buenos
    Aires) y queda fuera del análisis geográfico.
    """
    ts = set(types)
    if ts & COUNTRY_TYPES:
        return "pais"
    if ts & PROVINCE_TYPES:
        return "provincia"
    if ts & DEPARTMENT_TYPES:
        return "departamento"
    if ts & LOCALITY_TYPES:
        return "localidad"
    if ts & REGION_TYPES:
        return "region"
    return "localidad"


def reverse_geocode(df: pd.DataFrame, base_url: str, batch: int) -> pd.DataFrame:
    """Coordenada -> provincia + departamento oficiales, en lote (POST)."""
    have = df[df["lat"].notna()].copy()
    results: list[dict] = []
    for i in range(0, len(have), batch):
        chunk = have.iloc[i:i + batch]
        body = {"ubicaciones": [{"lat": r.lat, "lon": r.lon} for r in chunk.itertuples()]}
        r = requests.post(f"{base_url}/ubicacion", json=body,
                          headers={"User-Agent": UA}, timeout=300)
        r.raise_for_status()
        for qid, res in zip(chunk["place_qid"], r.json()["resultados"]):
            u = res.get("ubicacion") or {}
            results.append({
                "place_qid": qid,
                "prov_id": (u.get("provincia") or {}).get("id"),
                "prov_nombre": (u.get("provincia") or {}).get("nombre"),
                "dept_id_raw": (u.get("departamento") or {}).get("id"),
                "dept_nombre_raw": (u.get("departamento") or {}).get("nombre"),
            })
        log.info("reverse geocoding %d/%d", min(i + batch, len(have)), len(have))
    return pd.DataFrame(results)


def assign_localidad(df: pd.DataFrame, localidades: pd.DataFrame) -> pd.DataFrame:
    """Localidad censal más cercana dentro del mismo departamento.

    Se exige que caiga en el departamento ya resuelto: eso descarta de entrada
    los homónimos de otras provincias, que es el error clásico.
    """
    out = []
    by_dept = {k: v for k, v in localidades.groupby("dept_id_raw")}
    for row in df.itertuples():
        if row.granularity != "localidad" or pd.isna(row.lat) or not row.dept_id_raw:
            out.append({"place_qid": row.place_qid, "georef_localidad_id": None,
                        "localidad_id": None,
                        "localidad_nombre": None, "localidad_km": np.nan,
                        "localidad_match": ("no_aplica_por_granularidad"
                                            if row.granularity != "localidad"
                                            else "sin_departamento")})
            continue
        if str(row.dept_id_raw).startswith("02"):
            # CABA: una sola localidad. Cualquier barrio cae en ella.
            out.append({"place_qid": row.place_qid, "georef_localidad_id": None,
                        "localidad_id": CABA_LOCALIDAD_ID,
                        "localidad_nombre": CABA_LOCALIDAD_NOMBRE, "localidad_km": 0.0,
                        "localidad_match": "caba_unidad_unica"})
            continue
        cand = by_dept.get(row.dept_id_raw)
        if cand is None or cand.empty:
            out.append({"place_qid": row.place_qid, "georef_localidad_id": None,
                        "localidad_id": None,
                        "localidad_nombre": None, "localidad_km": np.nan,
                        "localidad_match": "departamento_sin_localidades"})
            continue
        d = haversine_km(row.lat, row.lon, cand["lat"].values, cand["lon"].values)
        j = int(np.argmin(d))
        km = float(d[j])
        best = cand.iloc[j]
        name_hit = normalize_name(row.label) == normalize_name(best["nombre"])
        if name_hit:
            match = "nombre_y_cercania"
        elif km <= MAX_LOCALIDAD_KM:
            match = "solo_cercania"
        else:
            match = "descartado_por_distancia"
        ok = match != "descartado_por_distancia"
        # `censo_id` es el id del Censo 2022, que NO es el de Georef: viene del
        # crosswalk. Si la localidad desapareció o se fusionó en 2022, queda
        # sin id censal y por lo tanto sin tamaño de ciudad.
        censo_id = best.get("censo_localidad_id") if ok else None
        if ok and (censo_id is None or (isinstance(censo_id, float) and np.isnan(censo_id))):
            match = "sin_localidad_censal_2022"
            censo_id = None
        out.append({"place_qid": row.place_qid,
                    "georef_localidad_id": best["id"] if ok else None,
                    "localidad_id": censo_id,
                    "localidad_nombre": best["nombre"] if ok else None,
                    "localidad_km": km,
                    "localidad_match": match})
    return pd.DataFrame(out)


def main() -> None:
    ap = argparse.ArgumentParser(description="Resuelve lugares de nacimiento a unidades oficiales")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    cfg = load_config()
    p = paths()
    out_path = p.interim / "places_resolved.parquet"
    if out_path.exists() and not args.force:
        log.info("ya existe %s (usar --force)", out_path)
        return

    places = collapse_places(
        json.loads((p.raw / "wikidata" / "places.json").read_text(encoding="utf-8"))["bindings"])
    places["granularity"] = places["types"].apply(granularity)
    log.info("%d lugares; granularidad: %s", len(places),
             places["granularity"].value_counts().to_dict())

    geo = cfg["geography"]["geocoder"]
    resolved = reverse_geocode(places, geo["base_url"], cfg["ingest"]["georef"]["batch_size"])
    df = places.merge(resolved, on="place_qid", how="left")

    # Argentina = lo que Georef ubica dentro del país. Es más confiable que P17,
    # que a veces falta o trae la entidad histórica.
    df["en_argentina"] = df["prov_id"].notna()

    cw_path = p.interim / "crosswalk_localidades.parquet"
    if not cw_path.exists():
        raise SystemExit("falta el crosswalk; correr src.clean.crosswalk_localidades primero")
    cw = pd.read_parquet(cw_path)
    localidades = pd.DataFrame({
        "id": cw["georef_id"],
        "nombre": cw["georef_nombre"],
        "dept_id_raw": cw["dept_id_georef"],
        "lat": cw["lat"],
        "lon": cw["lon"],
        "censo_localidad_id": cw["localidad_id"],
    })

    df = df.merge(assign_localidad(df, localidades), on="place_qid", how="left")
    df["dept_id"] = df["dept_id_raw"].apply(collapse_caba)
    df["dept_nombre"] = np.where(df["dept_id"] == "02000",
                                 "Ciudad Autónoma de Buenos Aires", df["dept_nombre_raw"])

    # Un país o una región no tienen departamento: el centroide de "Argentina" o
    # de "Cuyo" cae en un partido cualquiera. Se anula el departamento para que
    # no se filtre al análisis geográfico.
    demasiado_grueso = df["granularity"].isin(["pais", "region"])
    df.loc[demasiado_grueso,
           ["dept_id", "dept_nombre", "dept_id_raw", "dept_nombre_raw"]] = None

    # Una provincia SÍ ubica bien la provincia —su centroide cae dentro de ella—
    # pero no el departamento. El centroide de Buenos Aires cae en Azul, el de
    # Córdoba en Tercero Arriba y el de San Juan en Ullum. Sin este corte, los
    # jugadores cuyo `P19` es una provincia entera se clavaban en un departamento
    # arbitrario y lo convertían en cuna: Ullum y Tumbaya entraban al top-12
    # nacional de tasa con jugadores que no nacieron ahí, y Azul quedaba inflado
    # un 222%. Es la misma trampa que «Argentina» → General Levalle, un nivel más
    # arriba.
    #
    # No se descartan: la provincia es dato válido y el análisis provincial los
    # usa. Se los deja sin departamento y sin localidad, y eso solo los excluye
    # del análisis departamental y del de tamaño de ciudad.
    solo_provincia = df["granularity"].eq("provincia")
    df.loc[solo_provincia,
           ["dept_id", "dept_nombre", "dept_id_raw", "dept_nombre_raw"]] = None

    df["geo_status"] = np.select(
        [df["lat"].isna(), ~df["en_argentina"], demasiado_grueso,
         solo_provincia, df["dept_id"].isna()],
        ["sin_coordenada", "fuera_de_argentina", "lugar_demasiado_generico",
         "ok", "sin_departamento"],
        default="ok")

    df.to_parquet(out_path, index=False)

    qa = (df.groupby(["geo_status", "granularity", "localidad_match"], dropna=False)
            .size().rename("n_lugares").reset_index()
            .sort_values("n_lugares", ascending=False))
    qa.to_csv(p.tables / "qa_geocoding.csv", index=False, encoding="utf-8")
    log.info("\n%s", qa.to_string(index=False))
    log.info("guardado: %s (%d lugares)", out_path, len(df))


if __name__ == "__main__":
    main()
