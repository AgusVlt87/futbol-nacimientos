"""Fase 7 — Ubica cada club en su departamento y provincia.

Mismo criterio que con los lugares de nacimiento: se resuelve por coordenada
contra Georef, nunca por nombre. Los clubes fuera de Argentina quedan marcados
como tales — para el flujo interno importa distinguir «se fue a Rosario» de
«se fue a Italia».

Salida: `data/interim/clubs_resolved.parquet`

Uso:
    python -m src.clean.geocode_clubs [--force]
"""

from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

from src.clean.geo_units import collapse_caba, region_of
from src.clean.geocode_places import reverse_geocode
from src.common import get_logger, load_config, paths

log = get_logger("clean.clubs")


def main() -> None:
    ap = argparse.ArgumentParser(description="Geocodifica los clubes")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    cfg = load_config()
    p = paths()
    dest = p.interim / "clubs_resolved.parquet"
    if dest.exists() and not args.force:
        log.info("ya existe %s (usar --force)", dest)
        return

    car = pd.read_parquet(p.processed / "careers.parquet")
    clubs = car[["team_qid", "team_label", "club_lat", "club_lon", "club_country_qid"]]

    # Los clubes que solo salen del `equipo_debut` de una ficha no aparecen en
    # ninguna carrera, así que no están en `careers.parquet`. Sin ubicarlos, el
    # jugador entra a la muestra de H3 y se cae de la matriz origen→destino.
    nivel = p.processed / "player_level.parquet"
    if nivel.exists():
        lv = pd.read_parquet(nivel)
        if "primer_club_fuente" in lv.columns:
            solo_ficha = (lv[lv["primer_club_fuente"].eq("wikipedia")
                             & lv["primer_club_qid"].notna()]
                          [["primer_club_qid", "primer_club", "club_lat",
                            "club_lon", "club_country_qid"]]
                          .rename(columns={"primer_club_qid": "team_qid",
                                           "primer_club": "team_label"}))
            nuevos = set(solo_ficha["team_qid"]) - set(clubs["team_qid"])
            if nuevos:
                clubs = pd.concat(
                    [clubs, solo_ficha[solo_ficha["team_qid"].isin(nuevos)]],
                    ignore_index=True)
                log.info("clubes que solo aparecen en fichas: %d", len(nuevos))

    clubs = clubs.drop_duplicates("team_qid").reset_index(drop=True)
    log.info("%d equipos, %d con coordenada", len(clubs), clubs["club_lat"].notna().sum())

    # `reverse_geocode` espera las columnas place_qid/lat/lon.
    entrada = clubs.rename(columns={"team_qid": "place_qid", "club_lat": "lat",
                                    "club_lon": "lon"})
    geo = reverse_geocode(entrada, cfg["geography"]["geocoder"]["base_url"],
                          cfg["ingest"]["georef"]["batch_size"])
    out = clubs.merge(geo.rename(columns={"place_qid": "team_qid"}), on="team_qid", how="left")

    out["club_dept_id"] = out["dept_id_raw"].map(collapse_caba)
    out["club_prov_id"] = out["prov_id"]
    out["club_region"] = out["club_dept_id"].map(lambda d: region_of(d, cfg))
    out["club_en_argentina"] = out["club_prov_id"].notna()
    out["club_dept_nombre"] = np.where(out["club_dept_id"] == "02000",
                                       "Ciudad Autónoma de Buenos Aires",
                                       out["dept_nombre_raw"])

    out.to_parquet(dest, index=False)
    log.info("clubes en Argentina: %d de %d", int(out["club_en_argentina"].sum()), len(out))
    log.info("guardado: %s", dest)


if __name__ == "__main__":
    main()
