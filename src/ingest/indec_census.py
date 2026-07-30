"""Fase 2 — Ingesta del baseline poblacional (INDEC).

Tres piezas:

1. **Censo 2022, tabulados por radio censal** (24 zips, uno por provincia). Cada
   zip trae `persona`, `hogar` y `vivienda` con conteos por radio × variable ×
   categoría. De acá salen:
     - `PERSONA_EDAD`  → población por edad simple (0–109) → denominador por cohorte
     - `PERSONA_P02`   → sexo
     - `PERSONA_P14`   → provincia de nacimiento (¡el denominador correcto para H2!)
     - `VIVIENDA_CODLOC` → mapeo radio → localidad censal (define el tamaño de ciudad)
     - `VIVIENDA_URP`  → urbano / rural agrupado / rural disperso

2. **Radios censales 1991, 2001, 2010 y 2022** con población total por radio.
   Permiten reconstruir la población por departamento en cuatro momentos y elegir
   el censo más cercano al año de nacimiento de cada cohorte. La geometría (WKT)
   se descarta en la descarga: pesa el 95% y los mapas salen del IGN.

3. **Códigos geográficos oficiales** (xlsx) para etiquetar y validar los códigos.

Uso:
    python -m src.ingest.indec_census [--force] [--skip-tabulados] [--skip-radios]
"""

from __future__ import annotations

import argparse

import requests

from src.common import get_logger, load_config, paths, write_manifest
from src.ingest.download import UA, fetch, fetch_csv_drop_columns

log = get_logger("ingest.indec")

CKAN = "https://datos.gob.ar/api/3/action/package_show"
CENSO_PKG = "censo-nacional-de-poblacion-hogares-y-viviendas-2022"

# Radios censales con población total por radio (dataset 50 de INDEC).
RADIOS = {
    2022: "https://infra.datos.gob.ar/catalog/indec/dataset/50/distribution/50.1/download/radios-censales-2022.csv",
    2010: "https://infra.datos.gob.ar/catalog/indec/dataset/50/distribution/50.4/download/radios-censales-2010.csv",
    2001: "https://infra.datos.gob.ar/catalog/indec/dataset/50/distribution/50.7/download/radios-censales-2001.csv",
    1991: "https://infra.datos.gob.ar/catalog/indec/dataset/50/distribution/50.10/download/radios-censales-1991.csv",
}

CODIGOS = {
    "departamentos": "https://www.indec.gob.ar/ftp/cuadros/geoestadistica/c2022_codigos_departamentos.xlsx",
    "localidades": "https://www.indec.gob.ar/ftp/cuadros/geoestadistica/c2022_codigos_localidades.xlsx",
    "gobiernos_locales": "https://www.indec.gob.ar/ftp/cuadros/geoestadistica/c2022_codigos_gobiernos_locales.xlsx",
    "jurisdicciones": "https://www.indec.gob.ar/ftp/cuadros/geoestadistica/c2022_codigos_jurisdicciones.xlsx",
}


def census_2022_resources() -> list[dict]:
    """Los 24 zips provinciales, resueltos vía la API de datos.gob.ar (no hardcodeados)."""
    r = requests.get(CKAN, params={"id": CENSO_PKG}, headers={"User-Agent": UA}, timeout=120)
    r.raise_for_status()
    return [res for res in r.json()["result"]["resources"]
            if res.get("format") == "CSV" and res["url"].endswith(".zip")]


def main() -> None:
    ap = argparse.ArgumentParser(description="Ingesta del baseline poblacional del INDEC")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--skip-tabulados", action="store_true")
    ap.add_argument("--skip-radios", action="store_true")
    args = ap.parse_args()

    load_config()  # valida que config.yaml esté bien formado
    p = paths()
    base = p.raw / "indec"
    records: dict[str, list] = {"tabulados_2022": [], "radios": [], "codigos": []}

    if not args.skip_tabulados:
        resources = census_2022_resources()
        log.info("censo 2022: %d provincias", len(resources))
        for res in resources:
            fname = res["url"].rsplit("/", 1)[-1]
            records["tabulados_2022"].append(
                fetch(res["url"], base / "censo2022" / fname, force=args.force))

    if not args.skip_radios:
        for year, url in RADIOS.items():
            records["radios"].append(
                fetch_csv_drop_columns(url, base / "radios" / f"radios-{year}.csv.gz",
                                       drop={"wkt"}, force=args.force))

    for name, url in CODIGOS.items():
        records["codigos"].append(
            fetch(url, base / "codigos" / f"c2022_codigos_{name}.xlsx", force=args.force))

    write_manifest(base, {
        "source": "INDEC vía datos.gob.ar y indec.gob.ar",
        "license": "Datos abiertos de la Administración Pública Nacional",
        "package": CENSO_PKG,
        "contenido": {
            "tabulados_2022": ("conteos por radio censal × variable × categoría; "
                               "no es microdato: solo marginales por radio"),
            "radios": ("población total por radio en 1991, 2001, 2010 y 2022; "
                       "geometría WKT descartada en la descarga"),
            "codigos": "códigos geográficos oficiales 2022",
        },
        "files": records,
    })
    n = sum(len(v) for v in records.values())
    log.info("listo: %d archivos en %s", n, base)


if __name__ == "__main__":
    main()
