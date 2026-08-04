"""Fase 13d — Ubicación de los clubes que aparecen solo en las fichas.

`wikidata_clubs.py` pide la sede de los clubes que salen de `P54`. Los clubes que
aparecen en el `equipo_debut` de una ficha y en ninguna carrera no están ahí, y
sin coordenada no entran a H3, que es un análisis de flujo geográfico: un club
sin ubicar es un jugador que desaparece de la matriz origen→destino.

Se reutiliza la misma consulta que `wikidata_clubs`, sobre el complemento: los
QID nuevos y nada más. Sale a un archivo aparte para no tocar el crudo anterior.

Uso:
    python -m src.ingest.wikidata_clubs_wiki [--force]
"""

from __future__ import annotations

import argparse
import json

import pandas as pd

from src.common import get_logger, load_config, paths, utc_now, write_manifest
from src.ingest.sparql import WikidataClient, qid, values_clause
from src.ingest.wikidata_clubs import BATCH, QUERY

log = get_logger("ingest.clubs_wiki")


def main() -> None:
    ap = argparse.ArgumentParser(description="Ubicación de los clubes de las fichas")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    cfg = load_config()
    p = paths()
    dest = p.raw / "wikidata" / "clubs_wiki.json"
    if dest.exists() and not args.force:
        log.info("ya existe %s (usar --force)", dest)
        return

    origen = p.interim / "club_debut_wiki.parquet"
    if not origen.exists():
        raise SystemExit("falta club_debut_wiki.parquet — correr "
                         "`python -m src.clean.build_club_debut` primero")

    nuevos = set(pd.read_parquet(origen)["club_wiki_qid"].dropna())
    ya = json.loads((p.raw / "wikidata" / "clubs.json").read_text(encoding="utf-8"))
    conocidos = {qid(b["item"]["value"]) for b in ya["bindings"]}
    faltan = sorted(nuevos - conocidos)
    log.info("clubes en fichas: %d — ya ubicados: %d — a pedir: %d",
             len(nuevos), len(nuevos & conocidos), len(faltan))
    if not faltan:
        log.info("no hay clubes nuevos")
        return

    client = WikidataClient(cfg)
    bindings: list[dict] = []
    for i in range(0, len(faltan), BATCH):
        bindings.extend(client.query(
            QUERY.format(values=values_clause(faltan[i:i + BATCH]))))
        log.info("lote %d/%d — %d filas", i // BATCH + 1,
                 (len(faltan) + BATCH - 1) // BATCH, len(bindings))

    dest.write_text(json.dumps({"retrieved_at_utc": utc_now(),
                                "n_clubs": len(faltan), "bindings": bindings},
                               ensure_ascii=False), encoding="utf-8")
    write_manifest(p.raw / "wikidata", {
        "source": "Wikidata Query Service — sede de los clubes de las fichas",
        "license": "CC0",
        "motivo": "clubes que aparecen en equipo_debut y en ninguna carrera P54",
        "n_clubs": len(faltan), "rows": len(bindings),
    }, name="_clubs_wiki_manifest.json")
    log.info("listo: %d clubes -> %s", len(faltan), dest)


if __name__ == "__main__":
    main()
