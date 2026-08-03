"""Fase 2b — Nacidos vivos: el denominador que realmente corresponde.

**Por qué existe este módulo.** Contar futbolistas nacidos en 1970 contra la
población censada en 2022 mide otra cosa: los que siguen vivos y en el país
cincuenta años después. El denominador correcto para una cohorte de nacimiento
son los **nacimientos** de esa cohorte en ese lugar.

Dos fuentes, y una detalla algo importante:

1. **DEIS — serie histórica de nacidos vivos por jurisdicción, 1914–2024.**
   Nacimientos **ocurridos**, es decir por el lugar donde ocurrió el parto. Esa
   es exactamente la definición que usa el `P19` de Wikidata: si alguien nació
   en una maternidad de la Capital, su lugar de nacimiento es la Capital, tanto
   en el registro civil como en Wikidata. Numerador y denominador quedan
   definidos igual, que es lo que hace válida la tasa. (La alternativa, «por
   residencia de la madre», mediría otra cosa y no coincidiría con el numerador.)

2. **RENAPER — nacimientos por departamento, 2012–2022.** Demasiado reciente
   para las cohortes de futbolistas, pero permite **validar** cuánto se parece
   el reparto de nacimientos dentro de una provincia al reparto de población
   censal, que es el supuesto que hace falta para bajar a departamento.

Uso:
    python -m src.ingest.nacimientos [--force]
"""

from __future__ import annotations

import argparse

from src.common import get_logger, load_config, paths, write_manifest
from src.ingest.download import fetch

log = get_logger("ingest.nacimientos")

DEIS_SERIE = ("https://datos.salud.gob.ar/dataset/01ede118-2c3e-4f92-b943-cec5770ad83e/"
              "resource/8e46c92b-c0ab-4e99-b967-0f1a5f2dc9f6/download/"
              "nacidos-vivos-jurisdiccion-2022-1914.csv")
RENAPER_DEP = ("https://datosabiertos.renaper.gob.ar/"
               "nacimientos_por_departamento_y_anio_2012_2022.csv")
# Serie por RESIDENCIA DE LA MADRE, 2005-2022. Es la contrafáctica que permite
# saber qué criterio usa realmente la serie histórica. Ver `src.analysis.run_criterio_denominador`.
DEIS_RESIDENCIA = ("https://datos.salud.gob.ar/dataset/d1350588-d8bb-4892-b21c-48738311e218/"
                   "resource/5a68ea36-03fe-4b38-b590-d7cf2a13b821/download/"
                   "nacidos-vivos-registrados-en-la-republica-argentina-entre-los-anos-2005-2022.csv")


def main() -> None:
    ap = argparse.ArgumentParser(description="Ingesta de nacidos vivos")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    load_config()
    p = paths()
    base = p.raw / "nacimientos"

    registros = [
        # El recurso se publica con extensión .csv pero el archivo es xlsx.
        fetch(DEIS_SERIE, base / "deis_nacidos_vivos_jurisdiccion_1914_2024.xlsx",
              force=args.force),
        fetch(RENAPER_DEP, base / "renaper_nacimientos_departamento_2012_2022.csv",
              force=args.force),
        fetch(DEIS_RESIDENCIA, base / "deis_nacidos_vivos_residencia_madre_2005_2022.csv",
              force=args.force),
    ]

    write_manifest(base, {
        "fuentes": [
            {"nombre": ("DEIS — Dirección de Estadística e Información en Salud. "
                        "Serie histórica de nacidos vivos por jurisdicción, 1914–2024"),
             "portal": ("https://datos.gob.ar/dataset/"
                        "serie-historica-de-nacimientos-ocurridos-en-argentina-por-jurisdiccion"),
             "criterio": "nacimientos OCURRIDOS (lugar del parto), no residencia de la madre",
             "nota": "el recurso se publica como .csv pero el archivo es xlsx"},
            {"nombre": "RENAPER — Nacimientos por departamento, 2012–2022",
             "portal": "https://datos.gob.ar/dataset/nacimientos-en-argentina",
             "uso": ("validación del supuesto de reparto intraprovincial; no entra "
                     "como denominador porque no cubre las cohortes de la muestra")},
            {"nombre": ("DEIS — Nacidos vivos registrados por jurisdicción de "
                        "RESIDENCIA DE LA MADRE, 2005–2022"),
             "portal": ("https://datos.gob.ar/dataset/nacidos-vivos-registrados-por-"
                        "jurisdiccion-de-residencia-de-la-madre-republica-argentina"),
             "licencia": "CC-BY 4.0",
             "uso": ("serie contrafáctica: permite determinar qué criterio usa "
                     "realmente la serie histórica, que se publica como «ocurridos». "
                     "Resultado: son el mismo dato (432 de 432 celdas "
                     "provincia×año idénticas). Ver run_criterio_denominador.")},
        ],
        "files": registros,
    })
    log.info("listo: %d archivos en %s", len(registros), base)


if __name__ == "__main__":
    main()
