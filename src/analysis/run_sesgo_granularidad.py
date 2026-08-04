"""Fase 10b — El sesgo del NUMERADOR: la granularidad del `P19` no es aleatoria.

**El hueco que tapa este módulo.** El estudio le dedicó tres revisiones al
denominador —criterio de registro, reparto intraprovincial, geografía histórica—
y ninguna al numerador más allá del geocoding. Pero el numerador tiene un sesgo
propio, y empuja en la misma dirección que el hallazgo principal.

El razonamiento: la **precisión** con la que Wikidata registra el lugar de
nacimiento depende de cuán documentado esté el jugador. A un futbolista nacido en
la Capital le ponen la ciudad; a uno nacido en un pueblo de Santiago del Estero
es más probable que le pongan la provincia, o directamente «Argentina». Esos
casos se excluyen del análisis de tamaño de ciudad —correctamente, porque el
centroide de una provincia no ubica a nadie (§2.4)— pero si los excluidos vienen
desproporcionadamente del interior, **la exclusión le saca futbolistas justo a
los tramos chicos** y deprime su tasa.

Es la contracara honesta de la cota que se calculó para el artefacto de las
maternidades: aquel acota cuánto del déficit del interior puede ser un artefacto
del sistema de salud; éste acota cuánto puede ser un artefacto de la cobertura
del corpus.

Se hacen dos cosas:

**1. Probar que el sesgo existe.** Los jugadores con `P19` a nivel provincia sí
tienen provincia conocida —es lo único que se sabe de ellos—, así que se puede
comparar su distribución regional contra la de los jugadores con `P19` a nivel
localidad. Si la exclusión fuera aleatoria, las dos distribuciones coincidirían.

**2. Acotar cuánto puede mover.** Se recalcula la tasa del tramo `<10k`
atribuyéndole **todos** los excluidos. Es un techo deliberadamente inverosímil
—nadie cree que los 365 hayan nacido en pueblos— y por eso es una cota: el efecto
real está entre la tasa publicada y ésta.

Salidas en `outputs/tables/granularidad_*.csv`.

Uso:
    python -m src.analysis.run_sesgo_granularidad
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from src.analysis.stats import rate_ratio_ci
from src.clean.geo_units import region_of
from src.common import get_logger, load_config, paths

log = get_logger("analysis.granularidad")


def main() -> None:
    cfg = load_config()
    p = paths()
    c = cfg["cohorts"]

    pl = pd.read_parquet(p.processed / "analysis_players.parquet")
    players = pd.read_parquet(p.interim / "players.parquet")
    places = pd.read_parquet(p.interim / "places_resolved.parquet")
    den = (pd.read_parquet(p.processed / "denom_cohorte_ciudad.parquet")
           .merge(pd.read_parquet(p.processed / "denom_ciudad_unica.parquet")
                  [["ciudad_id", "tramo"]], on="ciudad_id", how="left"))

    # --- 1. ¿el sesgo existe? ------------------------------------------------
    # Se compara la región de los jugadores cuyo `P19` es una provincia entera
    # contra la de aquellos cuyo `P19` es una localidad. La provincia de los
    # primeros es dato válido: es lo único que Wikidata dice de ellos.
    pl = pl.copy()
    pl["region_prov"] = pl["prov_id"].map(
        lambda x: region_of(f"{x}000", cfg) if pd.notna(x) else np.nan)
    grueso = pl[pl["granularity"] == "provincia"]
    fino = pl[pl["granularity"] == "localidad"]

    regiones = sorted(set(pl["region_prov"].dropna()))
    obs_g = grueso["region_prov"].value_counts().reindex(regiones, fill_value=0)
    obs_f = fino["region_prov"].value_counts().reindex(regiones, fill_value=0)
    comp = pd.DataFrame({
        "region": regiones,
        "n_P19_provincia": obs_g.values,
        "pct_P19_provincia": 100 * obs_g.values / max(obs_g.sum(), 1),
        "n_P19_localidad": obs_f.values,
        "pct_P19_localidad": 100 * obs_f.values / max(obs_f.sum(), 1),
    })
    comp["sobrerrepresentacion"] = comp["pct_P19_provincia"] / comp["pct_P19_localidad"]
    chi2, p_val, dof, _ = stats.chi2_contingency(
        np.vstack([obs_g.values, obs_f.values])[:, obs_f.values > 0])

    # --- 2. la cota ----------------------------------------------------------
    excluidos_provincia = int((pl["granularity"] == "provincia").sum())
    excluidos_depto = int((pl["granularity"] == "departamento").sum())
    # Los que tienen «Argentina» como lugar de nacimiento ni siquiera llegan a la
    # muestra: se descartan en el geocoding por granularidad de país.
    en_ventana = players[players["birth_year"].between(
        c["analysis_min_year"], c["analysis_max_year"])]
    m = en_ventana.merge(places[["place_qid", "geo_status", "granularity"]],
                         left_on="birthplace_qid", right_on="place_qid", how="left")
    excluidos_pais = int((m["geo_status"].eq("lugar_demasiado_generico")
                          & m["granularity"].eq("pais")).sum())

    total_excluidos = excluidos_provincia + excluidos_depto + excluidos_pais

    obs_tramo = pl.dropna(subset=["tramo"]).groupby("tramo", observed=True).size()
    nac_tramo = den.groupby("tramo", observed=True)["nacimientos_cohorte"].sum()
    ref = cfg["city_size"]["schemes"][cfg["city_size"]["default_scheme"]]["reference_label"]

    k_chico, n_chico = int(obs_tramo["<10k"]), float(nac_tramo["<10k"])
    k_ref, n_ref = int(obs_tramo[ref]), float(nac_tramo[ref])
    rr, rr_lo, rr_hi = rate_ratio_ci(k_chico, n_chico, k_ref, n_ref)
    rr_c, rrc_lo, rrc_hi = rate_ratio_ci(k_chico + total_excluidos, n_chico, k_ref, n_ref)

    cota = pd.DataFrame([{
        "excluidos_P19_pais": excluidos_pais,
        "excluidos_P19_provincia": excluidos_provincia,
        "excluidos_P19_departamento": excluidos_depto,
        "excluidos_total": total_excluidos,
        "pct_de_la_ventana": 100 * total_excluidos / len(en_ventana),
        "tasa_menos_10k_publicada": 1e5 * k_chico / n_chico,
        "tasa_menos_10k_cota": 1e5 * (k_chico + total_excluidos) / n_chico,
        "RR_publicado": rr, "RR_ic_lo": rr_lo, "RR_ic_hi": rr_hi,
        "RR_cota": rr_c, "RR_cota_ic_lo": rrc_lo, "RR_cota_ic_hi": rrc_hi,
        "chi2_region": chi2, "df_region": dof, "p_region": p_val,
        "lectura": ("cota superior: atribuye TODOS los excluidos por granularidad "
                    "al tramo <10k, que es inverosímil por construcción. El valor "
                    "real está entre la tasa publicada y esta cota. Es la "
                    "contracara, del lado del numerador, de la cota que se "
                    "calculó para el artefacto de las maternidades."),
    }])

    comp.to_csv(p.tables / "granularidad_por_region.csv", index=False, encoding="utf-8")
    cota.to_csv(p.tables / "granularidad_cota.csv", index=False, encoding="utf-8")

    log.info("\n%s", comp.round(2).to_string(index=False))
    log.info("chi2(%d) = %.1f, p = %.2e  ->  la granularidad del P19 NO es "
             "independiente de la region", dof, chi2, p_val)
    log.info("excluidos por granularidad: %d pais + %d provincia + %d departamento = %d "
             "(%.1f%% de la ventana)", excluidos_pais, excluidos_provincia,
             excluidos_depto, total_excluidos, 100 * total_excluidos / len(en_ventana))
    log.info("tasa <10k: publicada %.1f  ->  cota superior %.1f por 100.000",
             1e5 * k_chico / n_chico, 1e5 * (k_chico + total_excluidos) / n_chico)
    log.info("RR <10k vs %s: publicado %.2f  ->  cota %.2f", ref, rr, rr_c)


if __name__ == "__main__":
    main()
