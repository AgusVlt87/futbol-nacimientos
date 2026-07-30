"""Fase 2 — Capas SIG del IGN (límites de país, provincias y departamentos).

Son la base cartográfica de los mapas coropléticos. Se bajan del dataset
"Unidades Territoriales" del IGN publicado en datos.gob.ar.

Uso:
    python -m src.ingest.ign_boundaries [--force]
"""

from __future__ import annotations

import argparse

from src.common import get_logger, load_config, paths, write_manifest
from src.ingest.download import fetch

log = get_logger("ingest.ign")

CAPAS = {
    "pais": "https://www.ign.gob.ar/descargas/geodatos/SHAPES/ign_pais.zip",
    "provincia": "https://www.ign.gob.ar/descargas/geodatos/SHAPES/ign_provincia.zip",
    "departamento": "https://www.ign.gob.ar/descargas/geodatos/SHAPES/ign_departamento.zip",
}


def main() -> None:
    ap = argparse.ArgumentParser(description="Capas SIG del IGN")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    load_config()
    p = paths()
    out_dir = p.raw / "ign"

    records = [fetch(url, out_dir / f"ign_{name}.zip", force=args.force)
               for name, url in CAPAS.items()]

    write_manifest(out_dir, {
        "source": "IGN — Instituto Geográfico Nacional, dataset «Unidades Territoriales»",
        "portal": "https://datos.gob.ar/dataset/unidades-territoriales",
        "license": "Datos abiertos de la Administración Pública Nacional",
        "files": records,
        "note": ("Los códigos de departamento del IGN siguen la codificación "
                 "INDEC (2 dígitos provincia + 3 departamento); se valida el "
                 "join contra el padrón Georef en la Fase 3."),
    })
    log.info("listo: %d capas en %s", len(records), out_dir)


if __name__ == "__main__":
    main()
