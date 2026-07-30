"""Descarga de archivos con registro de procedencia.

Toda descarga deja constancia (URL, tamaño, SHA-256, fecha) para que
`data/raw/` sea auditable. Es idempotente: si el archivo ya está, no lo repite.
"""

from __future__ import annotations

import csv
import gzip
from pathlib import Path

import requests

from src.common import get_logger, sha256

log = get_logger("ingest.download")

# Los radios censales traen la geometría como WKT en una sola celda: un
# MULTIPOLYGON puede pasar los 10 MB y revienta el límite por defecto del
# módulo csv (128 KB). 2^31-1 es el máximo que acepta el C long en Windows.
csv.field_size_limit(2**31 - 1)

UA = "futbol-geografia-arg/0.1 (investigación académica; contacto: aviullet@gmail.com)"


def fetch(url: str, dest: Path, force: bool = False, timeout: int = 600) -> dict:
    """Descarga `url` a `dest`. Devuelve el registro de procedencia."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and not force:
        log.info("ya está: %s", dest.name)
    else:
        log.info("bajando %s", dest.name)
        with requests.get(url, headers={"User-Agent": UA}, timeout=timeout, stream=True) as r:
            r.raise_for_status()
            tmp = dest.with_suffix(dest.suffix + ".part")
            with open(tmp, "wb") as fh:
                for chunk in r.iter_content(1 << 20):
                    fh.write(chunk)
            tmp.replace(dest)
    return {"url": url, "file": dest.name, "bytes": dest.stat().st_size, "sha256": sha256(dest)}


def fetch_csv_drop_columns(url: str, dest_gz: Path, drop: set[str],
                           force: bool = False, timeout: int = 900) -> dict:
    """Descarga un CSV grande descartando columnas al vuelo, y lo guarda .csv.gz.

    Se usa para los radios censales: el 95% del peso es la geometría WKT, que no
    se usa (los mapas salen de las capas del IGN). El descarte queda anotado en
    el manifiesto: es una transformación en la ingesta, no un dato perdido en
    silencio.
    """
    dest_gz.parent.mkdir(parents=True, exist_ok=True)
    if dest_gz.exists() and not force:
        log.info("ya está: %s", dest_gz.name)
        return {"url": url, "file": dest_gz.name, "bytes": dest_gz.stat().st_size,
                "sha256": sha256(dest_gz), "columns_dropped": sorted(drop)}

    log.info("bajando (streaming, sin %s): %s", ",".join(sorted(drop)), dest_gz.name)
    rows = 0
    with requests.get(url, headers={"User-Agent": UA}, timeout=timeout, stream=True) as r:
        r.raise_for_status()
        lines = (ln.decode("utf-8-sig", "replace") for ln in r.iter_lines())
        reader = csv.reader(lines)
        header = next(reader)
        keep = [i for i, c in enumerate(header) if c not in drop]
        tmp = dest_gz.with_suffix(dest_gz.suffix + ".part")
        with gzip.open(tmp, "wt", encoding="utf-8", newline="") as out:
            w = csv.writer(out)
            w.writerow([header[i] for i in keep])
            for row in reader:
                if not row:
                    continue
                w.writerow([row[i] for i in keep])
                rows += 1
        tmp.replace(dest_gz)

    return {"url": url, "file": dest_gz.name, "bytes": dest_gz.stat().st_size,
            "sha256": sha256(dest_gz), "rows": rows, "columns_dropped": sorted(drop),
            "note": "columnas descartadas en la descarga; ver docstring de fetch_csv_drop_columns"}
