"""Fase 10 — Control positivo: el efecto de la edad relativa.

**Para qué sirve.** El test placebo entre deportes muestra que el corpus no
fabrica el patrón geográfico. Pero un placebo solo demuestra que el instrumento
no inventa señal donde no la hay; no demuestra que sepa **recuperar** una señal
que sí está. Para eso hace falta un control positivo: un efecto conocido,
replicado y grande, que el mismo pipeline tenga que encontrar sin ayuda.

El *relative age effect* es exactamente eso. Es el hallazgo más replicado de la
literatura sobre desarrollo deportivo: los nacidos justo después de la fecha de
corte de las categorías juveniles son mayores que sus compañeros de camada, y
quedan sobrerrepresentados entre los profesionales. En Argentina la AFA usa el
**año calendario**, así que el corte es el 1 de enero y la ventaja corresponde al
primer trimestre.

Si el corpus recupera este efecto con la magnitud que reporta la literatura,
entonces sirve para medir sesgos de selección deportiva. Si no lo recupera, el
resultado nulo del gradiente por tamaño de ciudad podría ser falta de potencia
del instrumento y no ausencia de fenómeno.

**El denominador correcto.** No es «un cuarto por trimestre»: los nacimientos
argentinos no se reparten parejo a lo largo del año. Se usa la distribución real
de nacimientos por mes del período, de modo que el baseline es el dato y no la
uniformidad —la misma regla que el resto del estudio.

Salidas en `outputs/tables/edad_relativa_*.csv`.

Uso:
    python -m src.analysis.run_edad_relativa
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from src.analysis.stats import chi2_gof, odds_ratio_ci
from src.common import get_logger, load_config, paths

log = get_logger("analysis.edad_relativa")

# Wikidata codifica la precisión de la fecha con el esquema de Wikibase:
# 11 = día, 10 = mes, 9 = año. Para trimestre hace falta al menos el mes.
PRECISION_DIA = 11
PRECISION_MES = 10

TRIMESTRES = ["Q1 (ene-mar)", "Q2 (abr-jun)", "Q3 (jul-sep)", "Q4 (oct-dic)"]


def nacimientos_por_trimestre(p, y0: int, y1: int) -> pd.Series | None:
    """Distribución real de nacimientos por trimestre, si la fuente la trae.

    La serie del DEIS que usa el estudio es anual por jurisdicción y no tiene
    apertura mensual. Si no hay una fuente mensual, se devuelve `None` y el
    análisis cae en el baseline uniforme, **declarándolo**: es peor, pero es
    honesto decir cuál se usó.
    """
    ruta = p.raw / "nacimientos" / "deis_nacidos_vivos_mes.csv"
    if not ruta.exists():
        return None
    m = pd.read_csv(ruta)
    m = m[m["anio"].between(y0, y1)]
    m["trimestre"] = ((m["mes"] - 1) // 3).map(dict(enumerate(TRIMESTRES)))
    return m.groupby("trimestre")["nacimientos"].sum().reindex(TRIMESTRES)


def main() -> None:
    cfg = load_config()
    p = paths()
    c = cfg["cohorts"]
    y0, y1 = c["analysis_min_year"], c["analysis_max_year"]

    players = pd.read_parquet(p.interim / "players.parquet")
    lv = pd.read_parquet(p.processed / "player_level.parquet")

    d = players[players["birth_year"].between(y0, y1)].copy()
    d = d[d["dob_precision"] >= PRECISION_MES]
    d["mes"] = pd.to_datetime(d["dob"], format="ISO8601", utc=True).dt.month
    d["trimestre"] = ((d["mes"] - 1) // 3).map(dict(enumerate(TRIMESTRES)))

    # --- baseline -----------------------------------------------------------
    real = nacimientos_por_trimestre(p, y0, y1)
    if real is not None:
        esperado = (real / real.sum()).values
        origen = "nacimientos reales por mes (DEIS)"
    else:
        # Sin apertura mensual, el reparto por días de cada trimestre es mejor
        # que un cuarto exacto: los trimestres no tienen la misma cantidad de
        # días. Es una aproximación y se declara como tal.
        dias = np.array([90.25, 91, 92, 92])
        esperado = dias / dias.sum()
        origen = "proporcional a los días de cada trimestre (sin apertura mensual disponible)"

    obs = d.groupby("trimestre").size().reindex(TRIMESTRES, fill_value=0)
    g = chi2_gof(obs.values, esperado)

    tabla = pd.DataFrame({
        "trimestre": TRIMESTRES,
        "futbolistas": obs.values,
        "pct_observado": 100 * obs.values / obs.sum(),
        "pct_esperado": 100 * esperado,
        "obs_sobre_esp": obs.values / (esperado * obs.sum()),
    })

    # Contraste clásico: primer trimestre contra el último.
    a, b = int(obs.iloc[0]), int(obs.sum() - obs.iloc[0])
    n_esp = esperado * obs.sum()
    c_, e_ = float(n_esp[0]), float(n_esp.sum() - n_esp[0])
    or_, lo_, hi_ = odds_ratio_ci(a, b, c_, e_, cfg["stats"]["ci_level"])
    razon_q1_q4 = float(obs.iloc[0] / obs.iloc[3]) if obs.iloc[3] else np.nan

    # --- ¿se intensifica con el nivel? --------------------------------------
    # La literatura reporta que el efecto crece con el nivel competitivo. Es una
    # predicción adicional que el control positivo puede verificar.
    niveles = []
    lv2 = lv.merge(d[["player_qid", "trimestre"]], on="player_qid", how="inner")
    for tier in ["T1_seleccion", "T2_europa_top", "T3_primera_ar", "T4_resto"]:
        s = lv2[lv2["tier"] == tier]
        if len(s) < cfg["cohorts"]["min_n_subgroup"]:
            continue
        o = s.groupby("trimestre").size().reindex(TRIMESTRES, fill_value=0)
        niveles.append({
            "tier": tier, "n": int(o.sum()),
            "pct_Q1": 100 * o.iloc[0] / o.sum(),
            "pct_Q4": 100 * o.iloc[3] / o.sum(),
            "razon_Q1_Q4": float(o.iloc[0] / o.iloc[3]) if o.iloc[3] else np.nan,
        })

    resumen = pd.DataFrame([{
        "n": int(obs.sum()),
        "baseline": origen,
        "pct_Q1_observado": float(tabla["pct_observado"].iloc[0]),
        "pct_Q1_esperado": float(tabla["pct_esperado"].iloc[0]),
        "razon_Q1_sobre_Q4": razon_q1_q4,
        "OR_Q1_vs_resto": or_, "OR_ic_lo": lo_, "OR_ic_hi": hi_,
        "chi2": g.chi2, "df": g.df, "p": g.p, "cohens_w": g.cohens_w,
        "lectura": ("control POSITIVO: el efecto de la edad relativa es el "
                    "hallazgo más replicado del área. Si el pipeline lo "
                    "recupera, sabe encontrar sesgos de selección deportiva "
                    "cuando existen, y el gradiente plano por tamaño de ciudad "
                    "no se explica por falta de potencia."),
    }])

    tabla.to_csv(p.tables / "edad_relativa_trimestres.csv", index=False, encoding="utf-8")
    resumen.to_csv(p.tables / "edad_relativa_resumen.csv", index=False, encoding="utf-8")
    pd.DataFrame(niveles).to_csv(p.tables / "edad_relativa_por_nivel.csv",
                                 index=False, encoding="utf-8")

    log.info("baseline: %s", origen)
    log.info("\n%s", tabla.round(2).to_string(index=False))
    log.info("Q1/Q4 = %.2f | OR Q1 vs resto = %.2f (IC %.2f-%.2f) | chi2(%d) = %.1f, p = %.2e",
             razon_q1_q4, or_, lo_, hi_, g.df, g.chi2, g.p)
    if niveles:
        log.info("\n%s", pd.DataFrame(niveles).round(2).to_string(index=False))


if __name__ == "__main__":
    main()
