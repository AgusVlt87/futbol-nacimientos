"""Fase 13b — Del wikitext al club de debut, con QID.

Lee las fichas crudas y saca dos cosas: el **club de debut** y el **lugar de
nacimiento** que declara el artículo. La segunda no se usa para reemplazar el
`P19` —sería circular, las dos salen del mismo proyecto— sino como una segunda
lectura independiente del mismo hecho, útil para acotar la tasa de error.

**De dónde sale el club**, en orden, deteniéndose en el primero que da algo:

    1. `|equipo_debut =` de la ficha `{{Ficha de deportista}}`
    2. `|club_debut =` / `|equipo debut =`, que usan las fichas viejas
    3. la primera fila de la tabla «== Clubes ==»

Los tres se anotan con su origen para poder mirarlos por separado: la ficha y la
tabla no son la misma calidad de dato y no hay razón para creer que se equivocan
igual.

**Por qué se resuelve por enlace y no por nombre.** El wikitext trae
`[[Instituto Atlético Central Córdoba|Instituto]]`: el destino del enlace es un
título de artículo, y un título de artículo mapea a un QID de forma exacta vía
`wbgetentities`. Comparar «Instituto» contra un padrón de clubes por string es
el tipo de matcheo que este proyecto ya documentó como fuente de errores
silenciosos (trampa 2). El enlace evita todo eso.

Salidas:
    data/interim/club_debut_wiki.parquet
    outputs/tables/qa_club_debut_wiki.csv

Uso:
    python -m src.clean.build_club_debut
"""

from __future__ import annotations

import json
import re
import time

import pandas as pd
import requests

from src.common import get_logger, load_config, paths, write_run_manifest

log = get_logger("clean.club_debut")

WIKIDATA_API = "https://www.wikidata.org/w/api.php"

# Campos de ficha que declaran el club de debut, de más a menos específico.
CAMPOS_DEBUT = ("equipo_debut", "club_debut", "equipo debut", "debut_club")

# Enlaces que nunca son un club: aparecen dentro de las celdas de la tabla.
NO_ES_CLUB = re.compile(
    r"^(archivo|file|imagen|image|categor[ií]a|category|anexo|"
    r"[0-9]{4}|temporada|liga|copa|primera divisi[óo]n)", re.I)


def campo(texto: str, nombre: str) -> str:
    """Valor de un campo de ficha, hasta el próximo `|` o el cierre."""
    m = re.search(rf"^\s*\|\s*{re.escape(nombre)}\s*=([^\n]*(?:\n(?!\s*[|}}])[^\n]*)*)",
                  texto, re.M | re.I)
    return m.group(1).strip() if m else ""


def enlaces(v: str) -> list[tuple[str, str]]:
    """`[[Destino|Texto]]` -> (destino, texto), en orden de aparición."""
    return [(m.group(1).strip(), (m.group(2) or m.group(1)).strip())
            for m in re.finditer(r"\[\[([^\]|#]+)(?:\|([^\]]+))?\]\]", v)]


def extraer_club(texto: str) -> tuple[str | None, str | None, str]:
    """(destino_del_enlace, texto_visible, origen)."""
    for f in CAMPOS_DEBUT:
        v = campo(texto, f)
        if not v:
            continue
        e = [x for x in enlaces(v) if not NO_ES_CLUB.match(x[0])]
        if e:
            return e[0][0], e[0][1], f"ficha:{f}"
        # Sin enlace: el nombre en texto pelado sigue sirviendo, pero no se puede
        # resolver a QID. Se guarda igual y se marca.
        limpio = re.sub(r"\{\{[^}]*\}\}", "", v).strip()
        if limpio and len(limpio) > 2:
            return None, limpio, f"ficha:{f}:sin_enlace"

    m = re.search(r"==+\s*Clubes?\s*==+(.*?)(?=\n==[^=]|\Z)", texto, re.S | re.I)
    if m:
        for linea in m.group(1).split("\n"):
            if not linea.startswith("|") or "[[" not in linea:
                continue
            e = [x for x in enlaces(linea) if not NO_ES_CLUB.match(x[0])]
            if e:
                return e[0][0], e[0][1], "tabla_clubes"
    return None, None, "sin_dato"


def extraer_anio(texto: str) -> int | None:
    """Año de debut (`|inicio =`).

    Sin él, un club sacado de la ficha no pasa el filtro de edad plausible
    (14–20) que usa `run_seleccion`, y el dato nuevo entraría al análisis por una
    puerta distinta que el viejo — que es exactamente cómo se cuelan los sesgos
    de comparación.
    """
    for f in ("inicio", "debut", "año debut"):
        v = campo(texto, f)
        if not v:
            continue
        m = re.search(r"\b(1[89]\d{2}|20[0-4]\d)\b", v)
        if m:
            return int(m.group(1))
    return None


def extraer_lugar(texto: str) -> tuple[str | None, str | None]:
    """(destino_del_enlace, texto_visible) del campo `lugar nacimiento`."""
    for f in ("lugar nacimiento", "lugar_nacimiento", "lugar de nacimiento"):
        v = campo(texto, f)
        if not v:
            continue
        e = [x for x in enlaces(v) if not NO_ES_CLUB.match(x[0])]
        if e:
            return e[0][0], e[0][1]
        limpio = re.sub(r"\{\{[^}]*\}\}", "", v).strip(" ,\n")
        if limpio:
            return None, limpio
    return None, None


def titulo_canonico(t: str) -> str:
    """Forma con la que MediaWiki guarda un título.

    `wbgetentities` no acepta `normalize` con más de un título por pedido, así
    que la normalización se hace acá: guión bajo por espacio y mayúscula
    inicial, que es lo único que separa un enlace de wikitext de su forma
    canónica en la gran mayoría de los casos.
    """
    t = t.replace("_", " ").strip()
    return t[:1].upper() + t[1:] if t else t


def resolver_redirecciones(pares: list[tuple[str, str]], user_agent: str,
                           delay: float = 1.0) -> dict[tuple[str, str], str]:
    """(wiki, título) -> título canónico, para los que son redirección.

    **Por qué no es opcional.** `wbgetentities` no sigue redirecciones, y en
    es.wikipedia los enlaces a clubes usan casi siempre el nombre corto —
    «Rosario Central», «Boca Juniors», «Newell's Old Boys»— que redirige a la
    razón social completa. Sin este paso se pierden 608 jugadores, y no al azar:
    los que se pierden son los de **los clubes más grandes**, que son los que
    tienen nombre corto de uso corriente. Justo el sesgo que rompería H3.
    """
    s = requests.Session()
    s.headers.update({"User-Agent": user_agent})
    out: dict[tuple[str, str], str] = {}
    por_wiki: dict[str, list[str]] = {}
    for w, t in pares:
        por_wiki.setdefault(w, []).append(t)

    for wiki, ts in por_wiki.items():
        ts = sorted(set(ts))
        api = f"https://{wiki}.wikipedia.org/w/api.php"
        for i in range(0, len(ts), 50):
            r = s.get(api, timeout=90, params={
                "action": "query", "titles": "|".join(ts[i:i + 50]),
                "redirects": 1, "format": "json", "formatversion": 2})
            if r.status_code != 200:
                log.warning("redirecciones HTTP %d — lote salteado", r.status_code)
                continue
            q = r.json().get("query", {})
            for rd in q.get("redirects", []):
                out[(wiki, rd["from"])] = rd["to"]
            for nz in q.get("normalized", []):
                if (wiki, nz["to"]) in out:
                    out[(wiki, nz["from"])] = out[(wiki, nz["to"])]
            time.sleep(delay)
    return out


def titulos_a_qid(titulos: list[tuple[str, str]], user_agent: str,
                  delay: float = 1.0) -> dict[tuple[str, str], str]:
    """(wiki, título) -> QID, exacto, vía `wbgetentities`.

    Lo que no resuelve queda afuera del diccionario; el llamador lo cuenta.
    """
    s = requests.Session()
    s.headers.update({"User-Agent": user_agent})
    out: dict[tuple[str, str], str] = {}
    por_wiki: dict[str, list[str]] = {}
    for w, t in titulos:
        por_wiki.setdefault(w, []).append(titulo_canonico(t))

    for wiki, ts in por_wiki.items():
        ts = sorted(set(ts))
        for i in range(0, len(ts), 50):
            lote = ts[i:i + 50]
            r = s.get(WIKIDATA_API, timeout=90, params={
                "action": "wbgetentities", "sites": f"{wiki}wiki",
                "titles": "|".join(lote), "props": "info|sitelinks",
                "format": "json"})
            if r.status_code != 200:
                log.warning("wbgetentities HTTP %d — lote salteado", r.status_code)
                time.sleep(5)
                continue
            for ent in r.json().get("entities", {}).values():
                q = ent.get("id")
                if not q or q.startswith("-") or "missing" in ent:
                    continue
                t = ent.get("sitelinks", {}).get(f"{wiki}wiki", {}).get("title")
                if t:
                    out[(wiki, t)] = q
            time.sleep(delay)
            if (i // 50) % 10 == 0:
                log.info("  %s: %d/%d títulos consultados", wiki,
                         min(i + 50, len(ts)), len(ts))
    return out


def main() -> None:
    cfg = load_config()
    p = paths()
    crudo = p.raw / "wikipedia" / "fichas.jsonl"
    if not crudo.exists():
        raise SystemExit(
            "falta data/raw/wikipedia/fichas.jsonl — correr "
            "`python -m src.ingest.wikipedia_fichas` primero")

    filas = []
    with open(crudo, encoding="utf-8") as fh:
        for linea in fh:
            r = json.loads(linea)
            dest, vis, origen = extraer_club(r["wikitext"])
            lug_dest, lug_vis = extraer_lugar(r["wikitext"])
            filas.append({
                "player_qid": r["player_qid"], "wiki": r["wiki"],
                "titulo": r["titulo"], "revid": r["revid"],
                "club_wiki_titulo": dest, "club_wiki_nombre": vis,
                "club_wiki_origen": origen,
                "club_wiki_anio": extraer_anio(r["wikitext"]),
                "lugar_wiki_titulo": lug_dest, "lugar_wiki_nombre": lug_vis})
    d = pd.DataFrame(filas)
    log.info("fichas leídas: %d", len(d))
    log.info("\n%s", d["club_wiki_origen"].value_counts().to_string())

    # --- club: título -> QID ---------------------------------------------------
    pares = [(r.wiki, r.club_wiki_titulo) for r in d.itertuples()
             if r.club_wiki_titulo]
    log.info("resolviendo %d títulos de club (%d únicos) a QID",
             len(pares), len(set(pares)))
    ua = cfg["ingest"]["wikidata"]["user_agent"]
    delay = cfg["ingest"]["wikipedia"]["polite_delay_seconds"]
    mapa = titulos_a_qid(pares, ua, delay)

    def qid_de(wiki, titulo):
        return mapa.get((wiki, titulo_canonico(titulo))) if titulo else None

    d["club_wiki_qid"] = [qid_de(r.wiki, r.club_wiki_titulo) for r in d.itertuples()]

    # Segunda pasada: los que no resolvieron son, casi siempre, redirecciones.
    faltan = sorted({(r.wiki, titulo_canonico(r.club_wiki_titulo))
                     for r in d.itertuples()
                     if r.club_wiki_titulo and r.club_wiki_qid is None})
    if faltan:
        log.info("sin QID en la primera pasada: %d títulos — resolviendo "
                 "redirecciones", len(faltan))
        redir = resolver_redirecciones(faltan, ua, delay)
        log.info("son redirección: %d de %d", len(redir), len(faltan))

        destinos = sorted({(wiki, destino) for (wiki, _), destino in redir.items()})
        mapa.update(titulos_a_qid(destinos, ua, delay))
        # El título original hereda el QID de aquel al que redirige.
        for (wiki, origen), destino in redir.items():
            q = mapa.get((wiki, titulo_canonico(destino)))
            if q:
                mapa[(wiki, origen)] = q

        d["club_wiki_qid"] = [qid_de(r.wiki, r.club_wiki_titulo)
                              for r in d.itertuples()]

    con_nombre = d["club_wiki_nombre"].notna()
    con_qid = d["club_wiki_qid"].notna()
    log.info("=== cobertura ===")
    log.info("con nombre de club : %d de %d (%.1f%%)",
             con_nombre.sum(), len(d), 100 * con_nombre.mean())
    log.info("con QID de club    : %d de %d (%.1f%%)",
             con_qid.sum(), len(d), 100 * con_qid.mean())
    log.info("con año de debut   : %d de %d (%.1f%%)",
             d["club_wiki_anio"].notna().sum(), len(d),
             100 * d["club_wiki_anio"].notna().mean())
    log.info("con lugar de nac.  : %d de %d (%.1f%%)",
             d["lugar_wiki_nombre"].notna().sum(), len(d),
             100 * d["lugar_wiki_nombre"].notna().mean())

    p.interim.mkdir(parents=True, exist_ok=True)
    salida = p.interim / "club_debut_wiki.parquet"
    d.to_parquet(salida, index=False)

    qa = (d.groupby("club_wiki_origen")
          .agg(n=("player_qid", "size"), con_qid=("club_wiki_qid", "count"))
          .assign(pct_con_qid=lambda x: (100 * x["con_qid"] / x["n"]).round(1)))
    qa.to_csv(p.tables / "qa_club_debut_wiki.csv", encoding="utf-8")
    log.info("\n%s", qa.to_string())

    write_run_manifest(p.interim, "clean.build_club_debut",
                       {"club_debut_wiki.parquet": len(d)})
    log.info("=== %s ===", salida)


if __name__ == "__main__":
    main()
