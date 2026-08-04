"""Fase 12b — De la planilla codificada a la estimación corregida.

Consume el CSV que exporta `outputs/validacion/codificar.html`, estima la matriz
de mala clasificación del `P19` y produce el RR corregido con su intervalo.
Diseño completo en `docs/plan-validacion-p19.md`.

La planilla trae además el **club de debut** verificado a mano, que valida la
otra variable floja del estudio: el `primer_club` con el que se construye H3.
Su corrección no está implementada acá porque H3 no se resume en un solo RR;
el dato queda registrado para cuando se rehaga esa sección.

**Por qué una matriz y no una tasa.** Un error uniforme del `P19` atenúa el
efecto hacia el nulo: el hallazgo publicado sería una cota inferior y el trabajo
quedaría del lado seguro. Lo que puede fabricar el gradiente es un error
**diferencial**, que a los nacidos en pueblos se les asigne mal el lugar más
seguido que a los nacidos en metrópolis. Eso no se resume en un número: se
resume en la probabilidad de que un jugador realmente nacido en el estrato *i*
aparezca clasificado en el estrato *j*.

Con esa matriz el estudio deja de acotar y pasa a corregir. El vector de conteos
reales sale de resolver `Mᵀ · n_real = n_obs`, y la incertidumbre de la matriz se
propaga por bootstrap hasta el intervalo del RR.

**Modo simulación.** `--simular` genera una planilla ficticia con una tasa de
error conocida y verifica que la corrección la recupere. Sirve para dos cosas:
probar la cadena antes de gastar veinte horas de codificación humana, y mostrar
cuánta corrección haría falta para que el hallazgo se caiga.

Uso:
    python -m src.analysis.run_correccion_p19
    python -m src.analysis.run_correccion_p19 --simular 0.05 0.25
"""

from __future__ import annotations

import argparse

import numpy as np
import pandas as pd
from scipy import stats

from src.common import get_logger, load_config, paths

log = get_logger("analysis.correccion")

ESTRATOS = ["resto", "metropoli"]
N_BOOTSTRAP = 4000



def simular(clave: pd.DataFrame, err_metro: float, err_resto: float,
            semilla: int) -> pd.DataFrame:
    """Planilla ficticia con mala clasificación conocida.

    **Ojo con la dirección, que es fácil de invertir y cambia la conclusión.**
    Los dos parámetros se definen sobre el estrato **observado**, no sobre el
    real:

        err_metro = P(el jugador nació fuera de una metrópoli | figura en una)
        err_resto = P(el jugador nació en una metrópoli | figura fuera de una)

    El artefacto que preocupa al estudio —el chico de pueblo que nace en la
    maternidad de la cabecera y queda registrado ahí— es **`err_metro` alto**:
    gente que figura en la metrópoli y en realidad viene del interior.
    Corregirlo devuelve casos al interior, sube su tasa y **acerca el RR a 1**.

    Subir `err_resto` hace lo contrario: aleja el RR de 1 y refuerza el hallazgo.
    Es el escenario benigno y no hace falta simularlo para preocuparse.
    """
    rng = np.random.default_rng(semilla)
    d = clave.copy()
    p = np.where(d["estrato"] == "metropoli", err_metro, err_resto)
    mal = rng.random(len(d)) < p
    d["estrato_real"] = np.where(
        mal, np.where(d["estrato"] == "metropoli", "resto", "metropoli"), d["estrato"])
    d["tipo"] = np.where(mal, "otro_tramo", "exacto")
    return d[["caso", "estrato", "estrato_real", "tipo"]]


def matriz_mala_clasificacion(cod: pd.DataFrame) -> pd.DataFrame:
    """P(observado = j | real = i). Filas: real. Columnas: observado."""
    m = pd.crosstab(pd.Categorical(cod["estrato_real"], ESTRATOS),
                    pd.Categorical(cod["estrato"], ESTRATOS), dropna=False).astype(float)
    return m.div(m.sum(axis=1).replace(0, np.nan), axis=0)


def corregir(n_obs: np.ndarray, M: np.ndarray) -> np.ndarray:
    """Resuelve Mᵀ · n_real = n_obs, sin permitir conteos negativos."""
    try:
        real = np.linalg.solve(M.T, n_obs)
    except np.linalg.LinAlgError:
        real = np.linalg.lstsq(M.T, n_obs, rcond=None)[0]
    return np.clip(real, 0, None)


def rr(n: np.ndarray, denom: np.ndarray) -> float:
    """Razón de tasas resto / metrópoli."""
    return float((n[0] / denom[0]) / (n[1] / denom[1]))


def _conteos_del_estudio(cfg, p) -> tuple[np.ndarray, np.ndarray]:
    """Jugadores y nacimientos observados, colapsados a los dos estratos."""
    pl = pd.read_parquet(p.processed / "analysis_players.parquet")
    den = (pd.read_parquet(p.processed / "denom_cohorte_ciudad.parquet")
           .merge(pd.read_parquet(p.processed / "denom_ciudad_unica.parquet")
                  [["ciudad_id", "tramo"]], on="ciudad_id", how="left"))
    ref = cfg["city_size"]["schemes"][cfg["city_size"]["default_scheme"]]["reference_label"]
    pl = pl[pl["tramo"].notna()].copy()
    pl["estrato"] = np.where(pl["tramo"].eq(ref), "metropoli", "resto")
    den["estrato"] = np.where(den["tramo"].eq(ref), "metropoli", "resto")
    n_obs = np.array([float((pl["estrato"] == e).sum()) for e in ESTRATOS])
    denom = np.array([float(den.loc[den["estrato"] == e, "nacimientos_cohorte"].sum())
                      for e in ESTRATOS])
    return n_obs, denom


def curva_de_sensibilidad(semilla: int) -> None:
    """¿Cuánta mala clasificación haría falta para que el hallazgo se caiga?

    Es la pregunta que hay que poder contestar **antes** de gastar veinte horas
    de codificación humana, porque calibra cuánto preocuparse. Se barre el
    escenario del artefacto —jugadores del interior registrados en la metrópoli—
    y se busca el valor a partir del cual el intervalo del RR corregido toca el 1.
    """
    cfg = load_config()
    p = paths()
    n_obs, denom = _conteos_del_estudio(cfg, p)
    clave = pd.read_csv(p.root / "outputs" / "validacion" / "muestra_p19_clave.csv")

    filas = []
    for err in np.arange(0.0, 0.51, 0.05):
        cod = simular(clave, float(err), 0.05, semilla)
        M = matriz_mala_clasificacion(cod)
        if M.isna().to_numpy().any():
            continue
        rng = np.random.default_rng(semilla)
        sims = []
        for _ in range(1500):
            b = cod.sample(len(cod), replace=True,
                           random_state=int(rng.integers(1 << 31)))
            Mb = matriz_mala_clasificacion(b)
            if not Mb.isna().to_numpy().any():
                sims.append(rr(corregir(n_obs, Mb.values), denom))
        lo, hi = np.percentile(sims, [2.5, 97.5])
        filas.append({"err_metropoli": float(err),
                      "RR_corregido": rr(corregir(n_obs, M.values), denom),
                      "ic_lo": lo, "ic_hi": hi, "sigue_distinguible_de_1": bool(hi < 1)})

    d = pd.DataFrame(filas)
    d.to_csv(p.tables / "correccion_p19_curva.csv", index=False, encoding="utf-8")

    rompe = d[~d["sigue_distinguible_de_1"]]
    log.info("\n%s", d.round(3).to_string(index=False))
    log.info("\nRR observado sin corregir: %.3f", rr(n_obs, denom))
    if len(rompe):
        log.info("PUNTO DE QUIEBRE: con %.0f%% de los registrados en metropoli "
                 "viniendo en realidad del interior, el intervalo toca el 1",
                 100 * rompe["err_metropoli"].iloc[0])
    else:
        log.info("el efecto sobrevive en todo el rango barrido")


def main() -> None:
    ap = argparse.ArgumentParser(description="Corrección del P19")
    ap.add_argument("--simular", nargs=2, type=float, metavar=("ERR_METRO", "ERR_RESTO"),
                    help="corre con una planilla ficticia de error conocido")
    ap.add_argument("--curva", action="store_true",
                    help="barre el error diferencial y busca el punto de quiebre")
    ap.add_argument("--semilla", type=int, default=20260802)
    args = ap.parse_args()

    if args.curva:
        curva_de_sensibilidad(args.semilla)
        return

    cfg = load_config()
    p = paths()
    val = p.root / "outputs" / "validacion"
    clave = pd.read_csv(val / "muestra_p19_clave.csv")

    if args.simular:
        cod = simular(clave, args.simular[0], args.simular[1], args.semilla)
        log.info("MODO SIMULACIÓN: error metrópoli %.0f%%, error resto %.0f%%",
                 100 * args.simular[0], 100 * args.simular[1])
    else:
        ruta = val / "validacion_resuelta.csv"
        if not ruta.exists():
            raise SystemExit(
                f"falta {ruta.name}.\n"
                "Codificá con outputs/validacion/codificar.html, dejá el CSV en esa\n"
                "carpeta y corré:  python -m src.analysis.resolver_validacion\n\n"
                "Para probar la cadena sin datos reales:\n"
                "    python -m src.analysis.run_correccion_p19 --simular 0.25 0.05\n"
                "    python -m src.analysis.run_correccion_p19 --curva")
        todo = pd.read_csv(ruta)
        cod = todo[todo["estrato_real"].notna()][["caso", "estrato", "estrato_real"]].copy()
        log.info("codificados: %d | con lugar verificado: %d | resueltos a tramo: %d",
                 len(todo), int((todo["encontrado"] == 1).sum()), len(cod))
        if len(cod) < 30:
            raise SystemExit("menos de 30 casos resueltos: la matriz no es estimable.")

    # --- matriz -------------------------------------------------------------
    M = matriz_mala_clasificacion(cod)
    log.info("\nmatriz de mala clasificación  P(observado | real):\n%s",
             M.round(3).to_string())

    # --- conteos observados del estudio -------------------------------------
    pl = pd.read_parquet(p.processed / "analysis_players.parquet")
    den = (pd.read_parquet(p.processed / "denom_cohorte_ciudad.parquet")
           .merge(pd.read_parquet(p.processed / "denom_ciudad_unica.parquet")
                  [["ciudad_id", "tramo"]], on="ciudad_id", how="left"))
    ref = cfg["city_size"]["schemes"][cfg["city_size"]["default_scheme"]]["reference_label"]
    pl = pl[pl["tramo"].notna()].copy()
    pl["estrato"] = np.where(pl["tramo"].eq(ref), "metropoli", "resto")
    den["estrato"] = np.where(den["tramo"].eq(ref), "metropoli", "resto")

    n_obs = np.array([int((pl["estrato"] == e).sum()) for e in ESTRATOS], dtype=float)
    denom = np.array([float(den.loc[den["estrato"] == e, "nacimientos_cohorte"].sum())
                      for e in ESTRATOS])

    rr_obs = rr(n_obs, denom)
    n_cor = corregir(n_obs, M.values)
    rr_cor = rr(n_cor, denom)

    # --- bootstrap sobre la muestra de validación ---------------------------
    rng = np.random.default_rng(args.semilla)
    sims = []
    for _ in range(N_BOOTSTRAP):
        b = cod.sample(len(cod), replace=True, random_state=int(rng.integers(1 << 31)))
        Mb = matriz_mala_clasificacion(b)
        if Mb.isna().to_numpy().any():
            continue
        sims.append(rr(corregir(n_obs, Mb.values), denom))
    lo, hi = np.percentile(sims, [2.5, 97.5])

    salida = pd.DataFrame([{
        "modo": "simulacion" if args.simular else "codificacion_real",
        "n_validacion": len(cod),
        "err_observado_metropoli": float((cod["estrato"] != cod["estrato_real"])
                                         [cod["estrato"] == "metropoli"].mean()),
        "err_observado_resto": float((cod["estrato"] != cod["estrato_real"])
                                     [cod["estrato"] == "resto"].mean()),
        "RR_observado": rr_obs, "RR_corregido": rr_cor,
        "RR_corregido_ic_lo": lo, "RR_corregido_ic_hi": hi,
        "conclusion": ("el efecto sobrevive a la corrección" if hi < 1
                       else "la corrección hace que el efecto deje de ser distinguible de 1"),
    }])
    salida.to_csv(p.tables / "correccion_p19.csv", index=False, encoding="utf-8")

    log.info("\nRR observado  = %.3f", rr_obs)
    log.info("RR corregido  = %.3f  (IC 95%% bootstrap %.3f–%.3f)", rr_cor, lo, hi)
    log.info("%s", salida["conclusion"].iloc[0])


if __name__ == "__main__":
    main()
