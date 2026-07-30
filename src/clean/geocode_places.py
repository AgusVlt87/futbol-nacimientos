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
            out.append({"place_qid": row.place_qid, "localidad_id": None,
                        "localidad_nombre": None, "localidad_km": np.nan,
                        "localidad_match": ("no_aplica_por_granularidad"
                                            if row.granularity != "localidad"
                                            else "sin_departamento")})
            continue
        if str(row.dept_id_raw).startswith("02"):
            # CABA: una sola localidad. Cualquier barrio cae en ella.
            out.append({"place_qid": row.place_qid, "localidad_id": CABA_LOCALIDAD_ID,
                        "localidad_nombre": CABA_LOCALIDAD_NOMBRE, "localidad_km": 0.0,
                        "localidad_match": "caba_unidad_unica"})
            continue
        cand = by_dept.get(row.dept_id_raw)
        if cand is None or cand.empty:
            out.append({"place_qid": row.place_qid, "localidad_id": None,
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
        out.append({"place_qid": row.place_qid,
                    "localidad_id": best["id"] if match != "descartado_por_distancia" else None,
                    "localidad_nombre": best["nombre"] if match != "descartado_por_distancia" else None,
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

    loc = pd.DataFrame(
        json.loads((p.raw / "georef" / "localidades_censales.json").read_text(encoding="utf-8"))["items"])
    localidades = pd.DataFrame({
        "id": loc["id"],
        "nombre": loc["nombre"],
        "dept_id_raw": loc["departamento"].apply(lambda d: d["id"]),
        "lat": loc["centroide"].apply(lambda c: c["lat"]),
        "lon": loc["centroide"].apply(lambda c: c["lon"]),
    })

    df = df.merge(assign_localidad(df, localidades), on="place_qid", how="left")
    df["dept_id"] = df["dept_id_raw"].apply(collapse_caba)
    df["dept_nombre"] = np.where(df["dept_id"] == "02000",
                                 "Ciudad Autónoma de Buenos Aires", df["dept_nombre_raw"])

    # Una región no tiene departamento: el centroide de "Cuyo" cae en un partido
    # cualquiera. Se anula para que no se filtre al análisis por departamento.
    es_region = df["granularity"] == "region"
    df.loc[es_region, ["dept_id", "dept_nombre", "dept_id_raw", "dept_nombre_raw"]] = None

    df["geo_status"] = np.select(
        [df["lat"].isna(), ~df["en_argentina"], es_region, df["dept_id"].isna()],
        ["sin_coordenada", "fuera_de_argentina", "region_sin_departamento",
         "sin_departamento"],
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
