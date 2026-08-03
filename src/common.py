"""Utilidades compartidas: config, rutas, logging y manifiestos de procedencia.

Todo módulo del pipeline arranca con `cfg = load_config()` y usa las rutas de
`paths()`. No hay constantes de diseño hardcodeadas fuera de `config.yaml`.
"""

from __future__ import annotations

import hashlib
import json
import logging
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]


# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #
def load_config(path: Path | str | None = None) -> dict[str, Any]:
    """Carga config.yaml. Es la única fuente de decisiones de diseño."""
    path = Path(path) if path else ROOT / "config.yaml"
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


@dataclass(frozen=True)
class Paths:
    root: Path
    raw: Path
    interim: Path
    processed: Path
    figures: Path
    tables: Path
    reports: Path


def paths() -> Paths:
    p = Paths(
        root=ROOT,
        raw=ROOT / "data" / "raw",
        interim=ROOT / "data" / "interim",
        processed=ROOT / "data" / "processed",
        figures=ROOT / "outputs" / "figures",
        tables=ROOT / "outputs" / "tables",
        reports=ROOT / "reports",
    )
    for d in (p.raw, p.interim, p.processed, p.figures, p.tables, p.reports):
        d.mkdir(parents=True, exist_ok=True)
    return p


# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        h = logging.StreamHandler(sys.stdout)
        h.setFormatter(logging.Formatter("%(asctime)s  %(levelname)-7s  %(name)s  %(message)s",
                                         datefmt="%H:%M:%S"))
        logger.addHandler(h)
        logger.setLevel(logging.INFO)
    return logger


# --------------------------------------------------------------------------- #
# Procedencia
# --------------------------------------------------------------------------- #
def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while block := fh.read(chunk):
            h.update(block)
    return h.hexdigest()


def write_manifest(directory: Path, payload: dict[str, Any], name: str = "_manifest.json") -> Path:
    """Deja constancia fechada de qué se bajó, de dónde y con qué hash.

    `data/raw/` es intocable: el manifiesto es lo que hace auditable el crudo.
    """
    directory.mkdir(parents=True, exist_ok=True)
    payload = {"generated_at_utc": utc_now(), **payload}
    out = directory / name
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    return out


# --------------------------------------------------------------------------- #
# Procedencia de cada corrida
# --------------------------------------------------------------------------- #
def write_run_manifest(directory: Path, modulo: str, salidas: dict[str, int]) -> Path:
    """Deja constancia de qué produjo esta corrida y con qué configuración.

    `outputs/` está en `.gitignore`, así que git no puede decir si las tablas de
    disco corresponden al código de disco. Sin esto, «el pipeline reproduce» no
    es verificable: `git diff outputs/` sale vacío siempre, incluso cuando las
    salidas quedaron viejas.
    """
    ROOT_CFG = ROOT / "config.yaml"
    try:
        import subprocess
        commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                                capture_output=True, text=True, timeout=15).stdout.strip()
    except Exception:                                     # noqa: BLE001
        commit = None
    payload = {
        "modulo": modulo,
        "generado_utc": utc_now(),
        "commit": commit or "desconocido",
        "config_sha256": sha256(ROOT_CFG) if ROOT_CFG.exists() else None,
        "salidas": salidas,
    }
    directory.mkdir(parents=True, exist_ok=True)
    out = directory / "_run.json"
    previo = {}
    if out.exists():
        try:
            previo = json.loads(out.read_text(encoding="utf-8"))
        except Exception:                                 # noqa: BLE001
            previo = {}
    previo[modulo] = payload
    out.write_text(json.dumps(previo, ensure_ascii=False, indent=2), encoding="utf-8")
    return out
