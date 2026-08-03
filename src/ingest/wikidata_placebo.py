"""Fase 10 — Deportistas de otros deportes, para el test placebo.

**Qué contesta.** Todo el trabajo mide la geografía del fútbol contra los
nacimientos. Lo que no puede contestar por sí solo es si esa geografía es
**del fútbol** o es la del país: dónde hay hospitales, dónde hay registro civil
prolijo, dónde hay clase media con tiempo para llevar chicos a entrenar, dónde
Wikipedia tiene editores.

El placebo separa las dos cosas. Si el mapa del básquet —donde el corredor Bahía
Blanca–Junín–Córdoba es folklore conocido y distinto del fútbol— sale igual al
del fútbol, lo que se está midiendo es infraestructura general o cobertura, y eso
reescribe el paper. Si sale distinto, hay algo específicamente futbolístico.

**Los QID están verificados contra el endpoint** (2026-08-02): se consultó la
etiqueta de cada uno antes de fijarlo. Un QID equivocado no rompe nada,
simplemente devuelve cero filas.

Uso:
    python -m src.ingest.wikidata_placebo [--force]
"""

from __future__ import annotations

import argparse
import json

from src.common import get_logger, load_config, paths, utc_now, write_manifest
from src.ingest.sparql import WikidataClient

log = get_logger("ingest.placebo")

# Deporte -> (QID de la ocupación, etiqueta para los informes).
DEPORTES = {
    "basquet": ("Q3665646", "jugador de baloncesto"),
    "rugby": ("Q13415036", "jugador de rugby"),
    "voley": ("Q15117302", "jugador de voleibol"),
    "hockey": ("Q18515558", "jugador de hockey sobre césped"),
}

# Una sola consulta por deporte: la muestra es chica (cientos, no miles) y no
# hace falta paginar por año como en el fútbol.
QUERY = """
SELECT ?player ?playerLabel ?dob ?dobPrec ?gender ?birthplace ?sitelinks
WHERE {{
  ?player wdt:P106/wdt:P279* wd:{occupation} ;
          wdt:P27 wd:{country} ;
          p:P569/psv:P569 ?dobNode .
  ?dobNode wikibase:timeValue ?dob ; wikibase:timePrecision ?dobPrec .
  FILTER( YEAR(?dob) >= {y0} && YEAR(?dob) <= {y1} )
  ?player wikibase:sitelinks ?sitelinks .
  ?player wdt:P19 ?birthplace .
  OPTIONAL {{ ?player wdt:P21 ?gender }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "es,en". }}
}}
"""

# Los lugares de nacimiento nuevos se resuelven con la misma consulta que usa
# `wikidata_places`, para que la cadena de geocoding sea idéntica a la del fútbol.
QUERY_LUGARES = """
SELECT ?item ?itemLabel ?coord ?country ?type ?typeLabel ?admin ?adminLabel ?pop ?popDate
WHERE {{
  VALUES ?item {{ {values} }}
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


def qid(uri: str) -> str:
    return uri.rsplit("/", 1)[-1]


def main() -> None:
    ap = argparse.ArgumentParser(description="Ingesta de deportistas para el placebo")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    cfg = load_config()
    p = paths()
    base = p.raw / "wikidata" / "placebo"
    base.mkdir(parents=True, exist_ok=True)
    cli = WikidataClient(cfg)
    c = cfg["cohorts"]
    y0, y1 = c["analysis_min_year"], c["analysis_max_year"]

    lugares: set[str] = set()
    resumen = []
    for deporte, (occ, etiqueta) in DEPORTES.items():
        destino = base / f"{deporte}.json"
        if destino.exists() and not args.force:
            log.info("%s: ya existe (usar --force)", deporte)
            bindings = json.loads(destino.read_text(encoding="utf-8"))["bindings"]
        else:
            bindings = cli.query(QUERY.format(occupation=occ,
                                              country=cfg["project"]["country_qid"],
                                              y0=y0, y1=y1))
            destino.write_text(json.dumps(
                {"deporte": deporte, "occupation_qid": occ, "etiqueta": etiqueta,
                 "ventana": [y0, y1], "retrieved_at_utc": utc_now(),
                 "bindings": bindings}, ensure_ascii=False), encoding="utf-8")
        n = len({b["player"]["value"] for b in bindings})
        lugares |= {qid(b["birthplace"]["value"]) for b in bindings}
        log.info("%-8s %4d deportistas con P19 en %d–%d", deporte, n, y0, y1)
        resumen.append({"deporte": deporte, "occupation_qid": occ, "n": n})

    # Lugares de nacimiento: solo los que no resolvió ya el pipeline del fútbol.
    ya = set()
    resueltos = p.interim / "places_resolved.parquet"
    if resueltos.exists():
        import pandas as pd
        ya = set(pd.read_parquet(resueltos)["place_qid"])
    faltan = sorted(lugares - ya)
    log.info("lugares de nacimiento: %d en total, %d ya resueltos, %d nuevos",
             len(lugares), len(lugares & ya), len(faltan))

    destino_lugares = base / "places.json"
    if faltan and (not destino_lugares.exists() or args.force):
        bindings = []
        for i in range(0, len(faltan), 300):
            chunk = faltan[i:i + 300]
            bindings += cli.query(QUERY_LUGARES.format(
                values=" ".join(f"wd:{q}" for q in chunk)))
            log.info("lugares nuevos %d/%d", min(i + 300, len(faltan)), len(faltan))
        destino_lugares.write_text(json.dumps(
            {"retrieved_at_utc": utc_now(), "bindings": bindings}, ensure_ascii=False),
            encoding="utf-8")
    elif not faltan:
        destino_lugares.write_text(json.dumps(
            {"retrieved_at_utc": utc_now(), "bindings": []}, ensure_ascii=False),
            encoding="utf-8")

    write_manifest(base, {
        "fuente": "Wikidata (CC0), endpoint público",
        "uso": ("test placebo: contrastar la geografía del fútbol contra la de "
                "otros deportes con la misma cadena de geocoding y el mismo "
                "denominador de nacidos vivos"),
        "ventana": [y0, y1],
        "deportes": resumen,
        "lugares_de_nacimiento": {"total": len(lugares), "nuevos": len(faltan)},
    })
    log.info("listo -> %s", base)


if __name__ == "__main__":
    main()
