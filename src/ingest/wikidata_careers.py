"""Fase 1c — Ingesta de carreras: clubes, ligas y selección.

Sirve para dos cosas:

1. **H4 (nivel competitivo).** Permite derivar los tiers de `config.yaml`
   (selección mayor / liga top de UEFA / Primera argentina / resto). Es además
   el control del sesgo de cobertura de Wikidata: si el patrón geográfico se
   sostiene entre los jugadores de selección —donde la cobertura es
   prácticamente completa— no puede ser un artefacto de qué jugadores tienen
   artículo.

2. **H3 (flujo nacimiento → formación).** El calificador `P580` (fecha de
   inicio) de cada `P54` permite ordenar la carrera y quedarse con el club más
   temprano, que es el mejor proxy disponible de club formador sin tocar
   Transfermarkt. Es un proxy imperfecto y así se declara: Wikidata suele
   omitir las inferiores y a veces el primer club listado es el de debut
   profesional, no el de formación.

Uso:
    python -m src.ingest.wikidata_careers [--force] [--years MIN MAX]
"""

from __future__ import annotations

import argparse
import json

from src.common import get_logger, load_config, paths, utc_now, write_manifest
from src.ingest.sparql import WikidataClient

log = get_logger("ingest.careers")

QUERY = """
SELECT ?player ?team ?teamLabel ?start ?end ?league ?teamCountry
WHERE {{
  ?player wdt:P106/wdt:P279* wd:{occupation} ;
          wdt:P27 wd:{country} ;
          wdt:P569 ?dob .
  FILTER( YEAR(?dob) = {year} )
  ?player p:P54 ?st .
  ?st ps:P54 ?team .
  OPTIONAL {{ ?st pq:P580 ?start }}
  OPTIONAL {{ ?st pq:P582 ?end }}
  OPTIONAL {{ ?team wdt:P118 ?league }}
  OPTIONAL {{ ?team wdt:P17  ?teamCountry }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "es,en". }}
}}
"""


def main() -> None:
    ap = argparse.ArgumentParser(description="Ingesta de carreras desde Wikidata")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--years", nargs=2, type=int, metavar=("MIN", "MAX"))
    args = ap.parse_args()

    cfg = load_config()
    p = paths()
    out_dir = p.raw / "wikidata" / "careers"
    out_dir.mkdir(parents=True, exist_ok=True)

    y0, y1 = (args.years if args.years
              else (cfg["cohorts"]["ingest_min_year"], cfg["cohorts"]["ingest_max_year"]))
    client = WikidataClient(cfg)

    total, per_year = 0, {}
    for year in range(y0, y1 + 1):
        dest = out_dir / f"{year}.json"
        if dest.exists() and not args.force:
            n = len(json.loads(dest.read_text(encoding="utf-8"))["bindings"])
            per_year[str(year)] = n
            total += n
            continue
        bindings = client.query(QUERY.format(
            occupation=cfg["sample"]["occupation_qid"],
            country=cfg["project"]["country_qid"], year=year))
        dest.write_text(json.dumps({"year": year, "retrieved_at_utc": utc_now(),
                                    "bindings": bindings}, ensure_ascii=False),
                        encoding="utf-8")
        per_year[str(year)] = len(bindings)
        total += len(bindings)
        log.info("%d: %d filas", year, len(bindings))

    write_manifest(p.raw / "wikidata", {
        "source": "Wikidata Query Service — carreras (P54 con calificadores)",
        "license": "CC0",
        "query_template": QUERY,
        "years": [y0, y1],
        "rows_total": total,
        "rows_per_year": per_year,
        "note": ("P580 (fecha de inicio) falta en ~30% de los vínculos jugador-club; "
                 "el club más temprano es un proxy imperfecto del club formador."),
    }, name="_careers_snapshot.json")
    log.info("listo: %d filas -> %s", total, out_dir)


if __name__ == "__main__":
    main()
