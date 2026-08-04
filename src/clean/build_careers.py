"""Fase 3/7 — Carreras: nivel competitivo (H4) y club formador (H3).

Dos productos:

**Nivel competitivo (H4).** Tiers derivados de señales verificables, según
`config.yaml`. Gana el más alto que aplique. Sirve además como control del
sesgo de cobertura de Wikidata: entre los jugadores de la selección mayor la
cobertura es prácticamente censal, así que si el patrón geográfico se sostiene
ahí, no puede ser un artefacto de qué jugadores tienen artículo.

**Club formador (H3).** Wikidata no tiene un campo «club formador». El proxy es
el vínculo `P54` con la fecha de inicio (`P580`) más temprana. Es imperfecto y
se declara así:
  · falta `P580` en buena parte de los vínculos → esos jugadores quedan sin proxy;
  · Wikidata suele omitir las inferiores, con lo cual el primer club listado
    muchas veces es el de **debut profesional**, no el de formación;
  · los equipos juveniles de selección se excluyen: no son clubes.
El análisis de flujo lo dice en cada tabla. Es un piso, no una medición.

Salidas: `data/processed/careers.parquet`, `data/processed/player_level.parquet`

Uso:
    python -m src.clean.build_careers
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from src.common import get_logger, load_config, paths

log = get_logger("clean.careers")


def _qid(uri):
    return uri.rsplit("/", 1)[-1] if uri else None


def load_careers(careers_dir) -> pd.DataFrame:
    filas = []
    for f in sorted(careers_dir.glob("*.json")):
        for b in json.loads(f.read_text(encoding="utf-8"))["bindings"]:
            filas.append({
                "player_qid": _qid(b["player"]["value"]),
                "team_qid": _qid(b["team"]["value"]),
                "team_label": b.get("teamLabel", {}).get("value"),
                "start": b.get("start", {}).get("value"),
                "end": b.get("end", {}).get("value"),
                "league_qid": _qid(b.get("league", {}).get("value")),
                "team_country_qid": _qid(b.get("teamCountry", {}).get("value")),
            })
    df = pd.DataFrame(filas).drop_duplicates()
    df["start_year"] = pd.to_datetime(df["start"], format="ISO8601", utc=True,
                                      errors="coerce").dt.year
    return df


def load_clubs(path) -> pd.DataFrame:
    b = json.loads(path.read_text(encoding="utf-8"))["bindings"]
    acc: dict[str, dict] = {}
    for x in b:
        q = _qid(x["item"]["value"])
        rec = acc.setdefault(q, {"team_qid": q, "club_lat": None, "club_lon": None,
                                 "club_sede": None, "club_country_qid": None})
        for clave in ("coord", "sedeCoord"):
            if rec["club_lat"] is None and clave in x:
                raw = x[clave]["value"]
                if raw.startswith("Point("):
                    lon, lat = raw.removeprefix("Point(").removesuffix(")").split()
                    rec["club_lat"], rec["club_lon"] = float(lat), float(lon)
        if "sedeLabel" in x and rec["club_sede"] is None:
            rec["club_sede"] = x["sedeLabel"]["value"]
        if "country" in x and rec["club_country_qid"] is None:
            rec["club_country_qid"] = _qid(x["country"]["value"])
    return pd.DataFrame(acc.values())


def asignar_tiers(car: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    t = cfg["competitive_level"]["tiers"]
    seleccion = set(t["T1_seleccion"]["national_team_qids"])
    juveniles = set(t["T1_seleccion"].get("youth_team_qids") or [])
    elite = set(t["T2_europa_top"]["elite_league_qids"])
    primera_ar = set(t["T3_primera_ar"]["league_qids"])

    g = car.groupby("player_qid")
    out = pd.DataFrame({
        "seleccion_mayor": g["team_qid"].apply(lambda s: bool(set(s) & seleccion)),
        "seleccion_juvenil": g["team_qid"].apply(lambda s: bool(set(s) & juveniles)),
        "liga_elite_uefa": g["league_qid"].apply(lambda s: bool(set(s.dropna()) & elite)),
        "primera_argentina": g["league_qid"].apply(lambda s: bool(set(s.dropna()) & primera_ar)),
        "n_clubes": g["team_qid"].nunique(),
    }).reset_index()

    out["tier"] = np.select(
        [out["seleccion_mayor"], out["liga_elite_uefa"], out["primera_argentina"]],
        ["T1_seleccion", "T2_europa_top", "T3_primera_ar"], default="T4_resto")
    return out


def completar_con_ficha(out: pd.DataFrame, p, clubs: pd.DataFrame) -> pd.DataFrame:
    """Rellena `primer_club` con el `equipo_debut` de la ficha de Wikipedia.

    **Por qué hace falta.** `P54`+`P580` cubre el 41 % de la muestra, y la
    cobertura sube con el nivel del jugador: 99 % en la selección, 13 % en el
    resto. H3 corría, entonces, sobre una muestra seleccionada por el desenlace.

    **Por qué se puede.** Contra los 106 clubes que se verificaron a mano en
    BDFA, y en los 45 casos donde las dos fuentes tienen dato, aciertan **igual**:
    88,9 % cada una (McNemar p=1,00). La ficha no es un dato de peor calidad; es
    el mismo dato, escrito en prosa en vez de en el grafo. Y su error **no es
    diferencial por estrato de nacimiento** (83,7 % metrópoli vs 80,5 % resto,
    Fisher p=0,78), que es la condición para que no sesgue el contraste de H3.

    **Por qué Wikidata igual va primero** donde está: trae `P580`, o sea el año
    real del vínculo, mientras que la ficha trae `|inicio =`, que es lo que el
    editor entendió por debut. Empatando en precisión, gana el que tiene la
    fecha mejor definida. Queda registrado en `primer_club_fuente` para que
    cualquier análisis pueda cortar por procedencia — o excluir la ficha entera.
    """
    origen = p.interim / "club_debut_wiki.parquet"
    if not origen.exists():
        log.warning("sin club_debut_wiki.parquet: H3 queda con la cobertura de "
                    "Wikidata sola (correr src.clean.build_club_debut)")
        out["primer_club_fuente"] = np.where(out["primer_club_qid"].notna(),
                                             "wikidata", None)
        return out

    w = (pd.read_parquet(origen)
         .loc[lambda d: d["club_wiki_qid"].notna(),
              ["player_qid", "club_wiki_qid", "club_wiki_nombre",
               "club_wiki_anio"]])
    antes = int(out["primer_club_qid"].notna().sum())

    out = out.merge(w, on="player_qid", how="left")
    hueco = out["primer_club_qid"].isna() & out["club_wiki_qid"].notna()
    out["primer_club_fuente"] = np.select(
        [out["primer_club_qid"].notna(), hueco], ["wikidata", "wikipedia"],
        default=None)
    out.loc[hueco, "primer_club_qid"] = out.loc[hueco, "club_wiki_qid"]
    out.loc[hueco, "primer_club"] = out.loc[hueco, "club_wiki_nombre"]
    out.loc[hueco, "primer_club_anio"] = out.loc[hueco, "club_wiki_anio"]

    # Las coordenadas del club también hay que traerlas: sin ellas el jugador
    # entra a la muestra pero desaparece de la matriz origen→destino de H3.
    faltan_coord = hueco & out["club_lat"].isna()
    coords = clubs.set_index("team_qid")
    for col in ("club_lat", "club_lon", "club_sede", "club_country_qid"):
        if col in coords.columns:
            out.loc[faltan_coord, col] = (
                out.loc[faltan_coord, "primer_club_qid"].map(coords[col]))

    out = out.drop(columns=["club_wiki_qid", "club_wiki_nombre", "club_wiki_anio"])
    log.info("primer_club: %d de Wikidata + %d de la ficha = %d (%.1f%% de %d)",
             antes, int(hueco.sum()), antes + int(hueco.sum()),
             100 * (antes + hueco.sum()) / len(out), len(out))
    return out


def primer_club(car: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Club más temprano con fecha de inicio. Excluye selecciones."""
    t = cfg["competitive_level"]["tiers"]
    no_clubes = set(t["T1_seleccion"]["national_team_qids"]) | set(
        t["T1_seleccion"].get("youth_team_qids") or [])
    c = car[~car["team_qid"].isin(no_clubes) & car["start_year"].notna()]
    c = c.sort_values(["player_qid", "start_year"]).drop_duplicates("player_qid")
    return c[["player_qid", "team_qid", "team_label", "start_year"]].rename(columns={
        "team_qid": "primer_club_qid", "team_label": "primer_club",
        "start_year": "primer_club_anio"})


def main() -> None:
    cfg = load_config()
    p = paths()

    car = load_careers(p.raw / "wikidata" / "careers")
    clubs = load_clubs(p.raw / "wikidata" / "clubs.json")
    # Los clubes que solo aparecen en un `equipo_debut` de ficha no están en
    # ninguna carrera `P54`, así que su sede se pidió por separado.
    extra = p.raw / "wikidata" / "clubs_wiki.json"
    if extra.exists():
        clubs = (pd.concat([clubs, load_clubs(extra)], ignore_index=True)
                 .drop_duplicates("team_qid"))
        log.info("clubes ubicados: %d (incluye los de las fichas)", len(clubs))
    car = car.merge(clubs, on="team_qid", how="left")
    car.to_parquet(p.processed / "careers.parquet", index=False)
    log.info("carreras: %d vínculos, %d jugadores, %d equipos",
             len(car), car["player_qid"].nunique(), car["team_qid"].nunique())
    log.info("con fecha de inicio: %.1f%%", 100 * car["start_year"].notna().mean())

    players = pd.read_parquet(p.processed / "analysis_players.parquet")
    nivel = asignar_tiers(car, cfg)
    primero = primer_club(car, cfg).merge(
        clubs, left_on="primer_club_qid", right_on="team_qid", how="left").drop(
        columns=["team_qid"])

    out = (players.merge(nivel, on="player_qid", how="left")
                  .merge(primero, on="player_qid", how="left"))
    out["tier"] = out["tier"].fillna("T4_resto")
    for col in ["seleccion_mayor", "seleccion_juvenil", "liga_elite_uefa",
                "primera_argentina"]:
        out[col] = out[col].fillna(False).astype(bool)
    out["n_clubes"] = out["n_clubes"].fillna(0).astype(int)
    out = completar_con_ficha(out, p, clubs)
    out.to_parquet(p.processed / "player_level.parquet", index=False)

    qa = (out.groupby("tier").agg(jugadores=("player_qid", "size"),
                                  con_primer_club=("primer_club_qid", "count"))
             .assign(pct_con_primer_club=lambda d:
                     (100 * d["con_primer_club"] / d["jugadores"]).round(1)))
    qa.to_csv(p.tables / "qa_niveles_y_primer_club.csv", encoding="utf-8")
    log.info("\n%s", qa.to_string())
    log.info("guardado: %s", p.processed / "player_level.parquet")


if __name__ == "__main__":
    main()
