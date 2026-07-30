"""Fase 3 — Tabla tidy de jugadores a partir del crudo de Wikidata.

Desanida el crudo (una fila por jugador × posición) a una fila por jugador,
aplica la regla de muestra de `config.yaml` y deja registro de cuántos casos
descarta cada filtro. El descarte se cuenta y se reporta: es parte del
resultado, no un detalle de implementación.

Salida: `data/interim/players.parquet`
        `outputs/tables/qa_players_filtros.csv`

Uso:
    python -m src.clean.build_players
"""

from __future__ import annotations

import json

import pandas as pd

from src.common import get_logger, load_config, paths

log = get_logger("clean.players")

# Wikidata codifica la precisión temporal en `timePrecision`:
#   11 = día, 10 = mes, 9 = año, 8 = década, 7 = siglo.
# Para este estudio alcanza con precisión de año: la cohorte es el año de
# nacimiento. Precisión 8 o peor no permite ubicar la cohorte.
MIN_DOB_PRECISION = 9

GENDER_QIDS = {
    "Q6581097": "male",
    "Q6581072": "female",
}


def _qid(uri: str | None) -> str | None:
    return uri.rsplit("/", 1)[-1] if uri else None


def load_raw(players_dir) -> pd.DataFrame:
    rows = []
    for f in sorted(players_dir.glob("*.json")):
        for b in json.loads(f.read_text(encoding="utf-8"))["bindings"]:
            rows.append({
                "player_qid": _qid(b["player"]["value"]),
                "nombre": b.get("playerLabel", {}).get("value"),
                "dob": b["dob"]["value"],
                "dob_precision": int(b["dobPrec"]["value"]),
                "gender_qid": _qid(b.get("gender", {}).get("value")),
                "birthplace_qid": _qid(b.get("birthplace", {}).get("value")),
                "position_qid": _qid(b.get("position", {}).get("value")),
                "sitelinks": int(b["sitelinks"]["value"]),
            })
    return pd.DataFrame(rows)


def collapse(df: pd.DataFrame) -> pd.DataFrame:
    """Una fila por jugador. Las posiciones múltiples se guardan como lista."""
    positions = (df.dropna(subset=["position_qid"])
                   .groupby("player_qid")["position_qid"]
                   .apply(lambda s: sorted(set(s)))
                   .rename("positions"))
    base = (df.sort_values(["player_qid", "dob_precision"], ascending=[True, False])
              .drop_duplicates("player_qid")
              .drop(columns=["position_qid"])
              .set_index("player_qid"))
    out = base.join(positions)
    out["positions"] = out["positions"].apply(lambda v: v if isinstance(v, list) else [])
    out["n_positions"] = out["positions"].apply(len)
    return out.reset_index()


def main() -> None:
    cfg = load_config()
    p = paths()

    raw = load_raw(p.raw / "wikidata" / "players")
    df = collapse(raw)
    log.info("crudo: %d filas -> %d jugadores", len(raw), len(df))

    df["birth_year"] = pd.to_datetime(df["dob"], format="ISO8601", utc=True).dt.year
    df["gender"] = df["gender_qid"].map(GENDER_QIDS).fillna("otro/desconocido")

    # --- filtros, contando el descarte en cada paso -------------------------
    qa: list[dict] = [{"paso": "jugadores en Wikidata", "n": len(df), "descartados": 0}]

    def step(mask: pd.Series, label: str) -> None:
        nonlocal df
        before = len(df)
        df = df[mask].copy()
        qa.append({"paso": label, "n": len(df), "descartados": before - len(df)})

    step(df["dob_precision"] >= MIN_DOB_PRECISION,
         f"precisión de fecha ≥ año (timePrecision ≥ {MIN_DOB_PRECISION})")

    gender = cfg["sample"]["gender_filter"]
    if gender != "all":
        step(df["gender"] == gender, f"género = {gender}")

    step(df["birthplace_qid"].notna(), "con lugar de nacimiento (P19)")

    qa_df = pd.DataFrame(qa)
    qa_df["pct_restante"] = (100 * qa_df["n"] / qa_df["n"].iloc[0]).round(1)

    out = p.interim / "players.parquet"
    df.to_parquet(out, index=False)
    qa_df.to_csv(p.tables / "qa_players_filtros.csv", index=False, encoding="utf-8")

    log.info("\n%s", qa_df.to_string(index=False))
    log.info("guardado: %s (%d jugadores)", out, len(df))


if __name__ == "__main__":
    main()
