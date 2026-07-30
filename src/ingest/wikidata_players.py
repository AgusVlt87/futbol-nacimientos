"""Fase 1 — Ingesta de jugadores desde Wikidata.

Pagina por año de nacimiento (el endpoint público hace timeout si se pide todo
junto) y guarda el JSON crudo de cada año en `data/raw/wikidata/players/`.
El crudo no se toca después: la normalización va en la Fase 3.

Uso:
    python -m src.ingest.wikidata_players
    python -m src.ingest.wikidata_players --force        # re-baja todo
    python -m src.ingest.wikidata_players --years 1990 1995
"""

from __future__ import annotations

import argparse
import json

from src.common import get_logger, load_config, paths, utc_now, write_manifest
from src.ingest.sparql import WikidataClient

log = get_logger("ingest.players")

# Una fila por (jugador × posición): Wikidata admite varias posiciones por
# jugador. Se desanida en la Fase 3, no acá.
QUERY = """
SELECT ?player ?playerLabel ?dob ?dobPrec ?gender ?birthplace ?position ?sitelinks
WHERE {{
  ?player wdt:P106/wdt:P279* wd:{occupation} ;
          wdt:P27 wd:{country} ;
          p:P569/psv:P569 ?dobNode .
  ?dobNode wikibase:timeValue ?dob ; wikibase:timePrecision ?dobPrec .
  FILTER( YEAR(?dob) = {year} )
  ?player wikibase:sitelinks ?sitelinks .
  OPTIONAL {{ ?player wdt:P19  ?birthplace }}
  OPTIONAL {{ ?player wdt:P21  ?gender }}
  OPTIONAL {{ ?player wdt:P413 ?position }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "es,en". }}
}}
"""


def build_query(cfg: dict, year: int) -> str:
    s = cfg["sample"]
    occupation = s["occupation_qid"]
    if not s.get("expand_occupation_subclasses", True):
        # Sin expansión: se reemplaza el path por la propiedad directa.
        return (QUERY
                .replace("wdt:P106/wdt:P279* wd:{occupation}", "wdt:P106 wd:{occupation}")
                .format(occupation=occupation, country=cfg["project"]["country_qid"], year=year))
    return QUERY.format(occupation=occupation,
                        country=cfg["project"]["country_qid"],
                        year=year)


def main() -> None:
    ap = argparse.ArgumentParser(description="Ingesta de jugadores argentinos desde Wikidata")
    ap.add_argument("--force", action="store_true", help="re-baja años ya cacheados")
    ap.add_argument("--years", nargs=2, type=int, metavar=("MIN", "MAX"),
                    help="sobrescribe la ventana de config.yaml")
    args = ap.parse_args()

    cfg = load_config()
    p = paths()
    out_dir = p.raw / "wikidata" / "players"
    out_dir.mkdir(parents=True, exist_ok=True)

    y0, y1 = (args.years if args.years
              else (cfg["cohorts"]["ingest_min_year"], cfg["cohorts"]["ingest_max_year"]))
    client = WikidataClient(cfg)

    total_rows = 0
    per_year: dict[str, int] = {}
    for year in range(y0, y1 + 1):
        dest = out_dir / f"{year}.json"
        if dest.exists() and not args.force:
            n = len(json.loads(dest.read_text(encoding="utf-8"))["bindings"])
            per_year[str(year)] = n
            total_rows += n
            continue
        bindings = client.query(build_query(cfg, year))
        dest.write_text(
            json.dumps({"year": year, "retrieved_at_utc": utc_now(), "bindings": bindings},
                       ensure_ascii=False),
            encoding="utf-8",
        )
        per_year[str(year)] = len(bindings)
        total_rows += len(bindings)
        log.info("%d: %d filas", year, len(bindings))

    write_manifest(
        p.raw / "wikidata",
        {
            "source": "Wikidata Query Service",
            "endpoint": cfg["ingest"]["wikidata"]["endpoint"],
            "license": "CC0",
            "query_template": QUERY,
            "occupation_qid": cfg["sample"]["occupation_qid"],
            "country_qid": cfg["project"]["country_qid"],
            "years": [y0, y1],
            "rows_total": total_rows,
            "rows_per_year": per_year,
            "note": ("Wikidata cambia a diario. Sin esta fecha de snapshot los "
                     "conteos no se reproducen."),
        },
        name="_snapshot.json",
    )
    log.info("listo: %d filas crudas en %s", total_rows, out_dir)


if __name__ == "__main__":
    main()
