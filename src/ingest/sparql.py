"""Cliente SPARQL para el endpoint público de Wikidata.

Con reintentos, backoff y pausa cortés. El endpoint público es un recurso
compartido: los parámetros salen de `config.yaml` (`ingest.wikidata`), no se
tocan acá.
"""

from __future__ import annotations

import time
from typing import Any

import requests

from src.common import get_logger

log = get_logger("sparql")


class SparqlError(RuntimeError):
    pass


class WikidataClient:
    def __init__(self, cfg: dict[str, Any]):
        c = cfg["ingest"]["wikidata"]
        self.endpoint = c["endpoint"]
        self.timeout = c["timeout_seconds"]
        self.max_retries = c["max_retries"]
        self.backoff = c["backoff_seconds"]
        self.delay = c["polite_delay_seconds"]
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": c["user_agent"],
            "Accept": "application/sparql-results+json",
        })
        self._last_call = 0.0

    def _wait(self) -> None:
        elapsed = time.monotonic() - self._last_call
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)

    def query(self, sparql: str) -> list[dict[str, Any]]:
        """Devuelve los bindings crudos. Reintenta ante 429/5xx y timeouts."""
        last_exc: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            self._wait()
            try:
                r = self.session.post(
                    self.endpoint,
                    data={"query": sparql, "format": "json"},
                    timeout=self.timeout,
                )
                self._last_call = time.monotonic()
                if r.status_code == 200:
                    return r.json()["results"]["bindings"]
                if r.status_code in (429, 500, 502, 503, 504):
                    wait = self.backoff * attempt
                    retry_after = r.headers.get("Retry-After")
                    if retry_after and retry_after.isdigit():
                        wait = max(wait, int(retry_after))
                    log.warning("HTTP %s, reintento %d/%d en %ss",
                                r.status_code, attempt, self.max_retries, wait)
                    time.sleep(wait)
                    continue
                raise SparqlError(f"HTTP {r.status_code}: {r.text[:500]}")
            except (requests.Timeout, requests.ConnectionError) as exc:
                self._last_call = time.monotonic()
                last_exc = exc
                wait = self.backoff * attempt
                log.warning("%s, reintento %d/%d en %ss",
                            type(exc).__name__, attempt, self.max_retries, wait)
                time.sleep(wait)
        raise SparqlError(f"agotados {self.max_retries} reintentos") from last_exc


def qid(uri: str | None) -> str | None:
    """http://www.wikidata.org/entity/Q123 -> Q123"""
    if not uri:
        return None
    return uri.rsplit("/", 1)[-1]


def value(binding: dict[str, Any], key: str) -> str | None:
    v = binding.get(key)
    return v["value"] if v else None


def values_clause(qids: list[str], var: str = "item") -> str:
    """Bloque VALUES para consultar entidades en lote."""
    body = " ".join(f"wd:{q}" for q in qids)
    return f"VALUES ?{var} {{ {body} }}"
