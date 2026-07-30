"""Fase 2 — Ingesta del nomenclador oficial (API Georef, datos.gob.ar).

Baja el padrón completo de provincias, departamentos y **localidades censales**
(con centroide y con el id del INDEC, que es el mismo `CODLOC` del censo). Es la
base de la normalización de la Fase 3: el lugar de nacimiento de Wikidata se
resuelve por coordenada contra este padrón, no por matching de nombres.

Uso:
    python -m src.ingest.georef [--force]
"""

from __future__ import annotations

import argparse
import json

import requests

from src.common import get_logger, load_config, paths, utc_now, write_manifest
from src.ingest.download import UA

log = get_logger("ingest.georef")

CAPAS = {
    "provincias": "id,nombre,centroide.lat,centroide.lon",
    "departamentos": "id,nombre,provincia.id,provincia.nombre,centroide.lat,centroide.lon",
    "localidades_censales": ("id,nombre,categoria,provincia.id,provincia.nombre,"
                             "departamento.id,departamento.nombre,municipio.id,"
                             "municipio.nombre,centroide.lat,centroide.lon"),
}
PAGE = 1000


def fetch_capa(base_url: str, capa: str, campos: str) -> list[dict]:
    """Pagina la capa completa. El endpoint tope es 1000 registros por request."""
    endpoint = f"{base_url}/{capa.replace('_', '-')}"
    out: list[dict] = []
    offset = 0
    while True:
        r = requests.get(endpoint,
                         params={"max": PAGE, "inicio": offset, "campos": campos},
                         headers={"User-Agent": UA}, timeout=180)
        r.raise_for_status()
        payload = r.json()
        batch = payload[capa]
        out.extend(batch)
        total = payload.get("total", len(out))
        offset += PAGE
        if offset >= total or not batch:
            break
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Ingesta del nomenclador Georef")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    cfg = load_config()
    base_url = cfg["geography"]["geocoder"]["base_url"]
    p = paths()
    out_dir = p.raw / "georef"
    out_dir.mkdir(parents=True, exist_ok=True)

    counts = {}
    for capa, campos in CAPAS.items():
        dest = out_dir / f"{capa}.json"
        if dest.exists() and not args.force:
            counts[capa] = len(json.loads(dest.read_text(encoding="utf-8"))["items"])
            log.info("ya está: %s (%d)", capa, counts[capa])
            continue
        items = fetch_capa(base_url, capa, campos)
        dest.write_text(json.dumps({"retrieved_at_utc": utc_now(), "capa": capa,
                                    "items": items}, ensure_ascii=False),
                        encoding="utf-8")
        counts[capa] = len(items)
        log.info("%s: %d", capa, len(items))

    write_manifest(out_dir, {
        "source": "API Georef — Servicio de Normalización de Datos Geográficos (datos.gob.ar)",
        "base_url": base_url,
        "license": "Datos abiertos de la Administración Pública Nacional",
        "counts": counts,
        "note": ("El id de `localidades_censales` coincide con el CODLOC del "
                 "Censo 2022: es la bisagra entre el padrón geográfico y el "
                 "denominador poblacional."),
    })
    log.info("listo: %s", counts)


if __name__ == "__main__":
    main()
