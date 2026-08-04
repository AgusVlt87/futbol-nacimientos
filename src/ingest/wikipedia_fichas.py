"""Fase 13a — Las fichas de Wikipedia, para el club de debut que Wikidata no tiene.

**El problema que resuelve.** El `primer_club` sale de `P54` con fecha de inicio
(`P580`), y solo 2.254 de 5.511 jugadores la tienen: el 41 %. La cobertura por
nivel lo explica —99 % en la selección, 13 % en el resto— y la consecuencia es
que H3 corre sobre una muestra seleccionada por el desenlace.

**Por qué Wikipedia y no otra cosa.** El dato existe, pero en el texto en prosa,
no en el grafo. La ficha `{{Ficha de deportista}}` de es.wikipedia tiene un campo
`equipo_debut` que ningún bot volcó a Wikidata. Es la misma comunidad, el mismo
artículo y la misma licencia (CC BY-SA); solo que la parte estructurada del
proyecto quedó atrás de la parte redactada.

**Por qué esta fuente y no Transfermarkt**, que tiene el dato mucho mejor: sus
términos de uso prohíben la extracción automatizada, y espaciar los pedidos no
cambia eso. La API de Wikimedia, al revés, está publicada para uso programático
y su política de etiqueta pide exactamente lo que se hace acá: un User-Agent
identificable con contacto, lotes en vez de pedidos sueltos, y una pausa entre
llamadas. Los 5.511 jugadores salen en ~120 pedidos.

**Lo que baja**, en dos pasos:

    1. QID -> título del artículo, vía `wbgetentities` sobre Wikidata (50 por
       pedido). Se prefiere es.wikipedia; si no hay, en.wikipedia.
    2. título -> wikitext, vía `prop=revisions` (50 por pedido).

Se guarda el wikitext **crudo**, sin parsear: `data/raw/` es intocable y la
extracción es una decisión revisable que vive en `src/clean/`. Se registra el id
de revisión de cada artículo, que es lo que hace la bajada citable y repetible.

Uso:
    python -m src.ingest.wikipedia_fichas [--force] [--limite N]
"""

from __future__ import annotations

import argparse
import json
import time
from typing import Any

import pandas as pd
import requests

from src.common import get_logger, load_config, paths, utc_now, write_manifest

log = get_logger("ingest.wikipedia")

WIKIDATA_API = "https://www.wikidata.org/w/api.php"
BATCH_QIDS = 50


class WikipediaClient:
    """Cliente cortés para la API de acción de Wikimedia."""

    def __init__(self, cfg: dict[str, Any]):
        c = cfg["ingest"]["wikipedia"]
        self.api_url = c["api_url"]
        self.wikis = c["wikis"]
        self.batch = c["batch_titles"]
        self.delay = c["polite_delay_seconds"]
        self.timeout = c["timeout_seconds"]
        self.max_retries = c["max_retries"]
        self.backoff = c["backoff_seconds"]
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": cfg["ingest"]["wikidata"]["user_agent"]})
        self._last = 0.0
        self.pedidos = 0

    def _wait(self) -> None:
        elapsed = time.monotonic() - self._last
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)

    def get(self, url: str, params: dict[str, Any]) -> dict[str, Any]:
        for intento in range(1, self.max_retries + 1):
            self._wait()
            try:
                r = self.session.get(url, params=params, timeout=self.timeout)
                self._last = time.monotonic()
                self.pedidos += 1
                if r.status_code == 200:
                    return r.json()
                if r.status_code in (429, 500, 502, 503, 504):
                    espera = self.backoff * intento
                    log.warning("HTTP %d, reintento %d en %ds",
                                r.status_code, intento, espera)
                    time.sleep(espera)
                    continue
                r.raise_for_status()
            except requests.RequestException as e:
                if intento == self.max_retries:
                    raise
                log.warning("%s — reintento %d", e, intento)
                time.sleep(self.backoff * intento)
        raise RuntimeError(f"sin respuesta tras {self.max_retries} intentos")


def titulos_por_qid(cli: WikipediaClient, qids: list[str]) -> dict[str, tuple[str, str]]:
    """QID -> (wiki, título). Prefiere el primer wiki de la lista configurada."""
    out: dict[str, tuple[str, str]] = {}
    for i in range(0, len(qids), BATCH_QIDS):
        lote = qids[i:i + BATCH_QIDS]
        j = cli.get(WIKIDATA_API, {"action": "wbgetentities", "ids": "|".join(lote),
                                   "props": "sitelinks", "format": "json"})
        for q, ent in j.get("entities", {}).items():
            sl = ent.get("sitelinks", {})
            for w in cli.wikis:
                if f"{w}wiki" in sl:
                    out[q] = (w, sl[f"{w}wiki"]["title"])
                    break
        if (i // BATCH_QIDS) % 20 == 0:
            log.info("  sitelinks: %d/%d", min(i + BATCH_QIDS, len(qids)), len(qids))
    return out


def wikitext(cli: WikipediaClient, wiki: str,
             titulos: list[str]) -> dict[str, dict[str, Any]]:
    """título -> {revid, texto}. Resuelve redirecciones y las deja anotadas."""
    out: dict[str, dict[str, Any]] = {}
    url = cli.api_url.format(wiki=wiki)
    for i in range(0, len(titulos), cli.batch):
        lote = titulos[i:i + cli.batch]
        j = cli.get(url, {"action": "query", "prop": "revisions",
                          "rvprop": "content|ids", "rvslots": "main",
                          "titles": "|".join(lote), "redirects": 1,
                          "format": "json", "formatversion": 2})
        q = j.get("query", {})
        for pg in q.get("pages", []):
            revs = pg.get("revisions")
            if revs:
                out[pg["title"]] = {
                    "revid": revs[0].get("revid"),
                    "texto": revs[0]["slots"]["main"]["content"]}
        # El título pedido puede diferir del devuelto: hay que poder volver.
        for rd in q.get("redirects", []):
            if rd["to"] in out:
                out[rd["from"]] = out[rd["to"]]
        if (i // cli.batch) % 10 == 0:
            log.info("  %s.wikipedia: %d/%d", wiki,
                     min(i + cli.batch, len(titulos)), len(titulos))
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Fichas de Wikipedia")
    ap.add_argument("--force", action="store_true",
                    help="rebaja aunque el crudo ya exista")
    ap.add_argument("--limite", type=int, default=None,
                    help="solo los primeros N jugadores (para probar)")
    args = ap.parse_args()

    cfg = load_config()
    p = paths()
    destino = p.raw / "wikipedia"
    salida = destino / "fichas.jsonl"

    if salida.exists() and not args.force:
        n = sum(1 for _ in open(salida, encoding="utf-8"))
        log.info("ya existe %s con %d fichas — usar --force para rebajar",
                 salida.name, n)
        return

    jugadores = pd.read_parquet(p.processed / "analysis_players.parquet")
    qids = list(jugadores["player_qid"])
    if args.limite:
        qids = qids[:args.limite]
    log.info("jugadores a resolver: %d", len(qids))

    cli = WikipediaClient(cfg)

    log.info("paso 1/2 — sitelinks desde Wikidata")
    titulos = titulos_por_qid(cli, qids)
    log.info("con artículo: %d de %d (%.1f%%)", len(titulos), len(qids),
             100 * len(titulos) / len(qids))
    por_wiki: dict[str, list[str]] = {}
    for q, (w, t) in titulos.items():
        por_wiki.setdefault(w, []).append(t)
    for w, ts in por_wiki.items():
        log.info("   %s.wikipedia: %d", w, len(ts))

    log.info("paso 2/2 — wikitext")
    textos: dict[str, dict[str, dict[str, Any]]] = {}
    for w, ts in por_wiki.items():
        textos[w] = wikitext(cli, w, sorted(set(ts)))
        log.info("   %s.wikipedia: %d artículos", w, len(textos[w]))

    destino.mkdir(parents=True, exist_ok=True)
    n_escritas = 0
    faltantes = 0
    with open(salida, "w", encoding="utf-8") as fh:
        for q in qids:
            wt = titulos.get(q)
            if wt is None:
                faltantes += 1
                continue
            w, t = wt
            art = textos.get(w, {}).get(t)
            if art is None:
                faltantes += 1
                continue
            fh.write(json.dumps({"player_qid": q, "wiki": w, "titulo": t,
                                 "revid": art["revid"], "wikitext": art["texto"]},
                                ensure_ascii=False) + "\n")
            n_escritas += 1

    write_manifest(destino, {
        "fuente": "API de acción de Wikimedia (es/en.wikipedia.org)",
        "licencia_contenido": "CC BY-SA 4.0",
        "motivo": "campo equipo_debut de la ficha, ausente en Wikidata",
        "jugadores_consultados": len(qids),
        "con_articulo": len(titulos),
        "fichas_guardadas": n_escritas,
        "sin_ficha": faltantes,
        "pedidos_http": cli.pedidos,
        "snapshot_utc": utc_now(),
    }, name="_fichas_manifest.json")

    log.info("=== %d fichas en %s ===", n_escritas, salida)
    log.info("pedidos HTTP totales: %d", cli.pedidos)


if __name__ == "__main__":
    main()
