"""Fase 1b — Enriquecimiento de los lugares de nacimiento.

Toma los QID distintos de `P19` que salieron de `wikidata_players` y les pide a
Wikidata coordenada (`P625`), país (`P17`), tipo (`P31`), unidad administrativa
(`P131`) y población (`P1082`, con su fecha).

La coordenada es lo importante: la normalización a departamento/provincia se
hace geográficamente contra Georef en la Fase 3, no por nombre. La población de
Wikidata NO se usa como denominador (es de fechas heterogéneas y cobertura
irregular); queda solo como chequeo cruzado contra el censo.

Uso:
    python -m src.ingest.wikidata_places [--force]
"""

from __future__ import annotations

import argparse
import json

from src.common import get_logger, load_config, paths, utc_now, write_manifest
from src.ingest.sparql import WikidataClient, qid, values_clause

log = get_logger("ingest.places")

BATCH = 120

QUERY = """
SELECT ?item ?itemLabel ?coord ?country ?type ?typeLabel ?admin ?adminLabel ?pop ?popDate
WHERE {{
  {values}
  OPTIONAL {{ ?item wdt:P625 ?coord }}
  OPTIONAL {{ ?item wdt:P17  ?country }}
  OPTIONAL {{ ?item wdt:P31  ?type }}
  OPTIONAL {{ ?item wdt:P131 ?admin }}
  OPTIONAL {{
    ?item p:P1082 ?popSt .
    ?popSt ps:P1082 ?pop .
    OPTIONAL {{ ?popSt pq:P585 ?popDate }}
  }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "es,en". }}
}}
"""


def birthplace_qids(players_dir) -> list[str]:
    seen: set[str] = set()
    for f in sorted(players_dir.glob("*.json")):
        for b in json.loads(f.read_text(encoding="utf-8"))["bindings"]:
            if "birthplace" in b:
                seen.add(qid(b["birthplace"]["value"]))
    return sorted(seen)


def main() -> None:
    ap = argparse.ArgumentParser(description="Enriquece los lugares de nacimiento")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    cfg = load_config()
    p = paths()
    players_dir = p.raw / "wikidata" / "players"
    if not any(players_dir.glob("*.json")):
        raise SystemExit("no hay jugadores ingestados; correr src.ingest.wikidata_players primero")

    dest = p.raw / "wikidata" / "places.json"
    if dest.exists() and not args.force:
        log.info("ya existe %s (usar --force para rehacer)", dest)
        return

    qids = birthplace_qids(players_dir)
    log.info("%d lugares de nacimiento distintos", len(qids))

    client = WikidataClient(cfg)
    bindings: list[dict] = []
    for i in range(0, len(qids), BATCH):
        chunk = qids[i:i + BATCH]
        bindings.extend(client.query(QUERY.format(values=values_clause(chunk))))
        log.info("lote %d/%d — %d filas acumuladas",
                 i // BATCH + 1, (len(qids) + BATCH - 1) // BATCH, len(bindings))

    dest.write_text(
        json.dumps({"retrieved_at_utc": utc_now(), "n_places": len(qids), "bindings": bindings},
                   ensure_ascii=False),
        encoding="utf-8",
    )
    write_manifest(
        p.raw / "wikidata",
        {
            "source": "Wikidata Query Service — enriquecimiento de lugares (P19)",
            "license": "CC0",
            "query_template": QUERY,
            "n_places": len(qids),
            "rows": len(bindings),
            "note": ("P1082 de Wikidata NO se usa como denominador: fechas "
                     "heterogéneas y cobertura irregular. Solo chequeo cruzado."),
        },
        name="_places_manifest.json",
    )
    log.info("listo: %d lugares, %d filas -> %s", len(qids), len(bindings), dest)


if __name__ == "__main__":
    main()
