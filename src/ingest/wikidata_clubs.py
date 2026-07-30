"""Fase 1d — Ubicación de los clubes.

Para H3 hace falta saber dónde está cada club: el flujo nacimiento → formación
es un flujo geográfico. Se piden `P159` (sede), `P131` (unidad administrativa)
y `P625` (coordenada), en ese orden de preferencia — muchos clubes tienen la
coordenada directa y otros solo la ciudad sede.

Uso:
    python -m src.ingest.wikidata_clubs [--force]
"""

from __future__ import annotations

import argparse
import json

from src.common import get_logger, load_config, paths, utc_now, write_manifest
from src.ingest.sparql import WikidataClient, qid, values_clause

log = get_logger("ingest.clubs")

BATCH = 100

QUERY = """
SELECT ?item ?itemLabel ?coord ?sede ?sedeLabel ?sedeCoord ?admin ?country
WHERE {{
  {values}
  OPTIONAL {{ ?item wdt:P625 ?coord }}
  OPTIONAL {{
    ?item wdt:P159 ?sede .
    OPTIONAL {{ ?sede wdt:P625 ?sedeCoord }}
  }}
  OPTIONAL {{ ?item wdt:P131 ?admin }}
  OPTIONAL {{ ?item wdt:P17  ?country }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "es,en". }}
}}
"""


def team_qids(careers_dir) -> list[str]:
    seen: set[str] = set()
    for f in sorted(careers_dir.glob("*.json")):
        for b in json.loads(f.read_text(encoding="utf-8"))["bindings"]:
            seen.add(qid(b["team"]["value"]))
    return sorted(seen)


def main() -> None:
    ap = argparse.ArgumentParser(description="Ubicación de los clubes")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    cfg = load_config()
    p = paths()
    careers_dir = p.raw / "wikidata" / "careers"
    if not any(careers_dir.glob("*.json")):
        raise SystemExit("faltan las carreras; correr src.ingest.wikidata_careers primero")

    dest = p.raw / "wikidata" / "clubs.json"
    if dest.exists() and not args.force:
        log.info("ya existe %s (usar --force)", dest)
        return

    qids = team_qids(careers_dir)
    log.info("%d clubes/equipos distintos", len(qids))

    client = WikidataClient(cfg)
    bindings: list[dict] = []
    for i in range(0, len(qids), BATCH):
        bindings.extend(client.query(QUERY.format(values=values_clause(qids[i:i + BATCH]))))
        log.info("lote %d/%d — %d filas", i // BATCH + 1,
                 (len(qids) + BATCH - 1) // BATCH, len(bindings))

    dest.write_text(json.dumps({"retrieved_at_utc": utc_now(), "n_clubs": len(qids),
                                "bindings": bindings}, ensure_ascii=False),
                    encoding="utf-8")
    write_manifest(p.raw / "wikidata", {
        "source": "Wikidata Query Service — ubicación de clubes",
        "license": "CC0",
        "query_template": QUERY,
        "n_clubs": len(qids),
        "rows": len(bindings),
    }, name="_clubs_manifest.json")
    log.info("listo: %d clubes -> %s", len(qids), dest)


if __name__ == "__main__":
    main()
