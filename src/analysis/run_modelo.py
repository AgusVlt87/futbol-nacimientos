"""Fase 11b — Modelos con covariables y partición de varianza.

**Los dos huecos que tapa.**

1. El §4.1 interpretaba el patrón diciendo que el lugar de nacimiento mide
   «distancia a la infraestructura formativa». Esa variable no existía en ningún
   modelo. Ahora existe, junto con el confusor socioeconómico obvio (NBI), y se
   puede ver cuánto del efecto del tamaño sobrevive a controlarlos.

2. El trabajo reportaba un pseudo-$R^2$ de 0,011 como medida de ajuste. Es
   correcto y es poco informativo: la historia de estos datos no es la pendiente,
   es la **sobredispersión**. Dos ciudades del mismo tamaño, en la misma
   provincia y con el mismo NBI producen cantidades muy distintas de
   futbolistas. Un modelo multinivel con intercepto aleatorio por departamento
   permite decir cuánta de esa variación es entre departamentos y cuánta queda
   adentro.

**Cómo leer el resultado.** Si el coeficiente del tamaño se mantiene al agregar
distancia y NBI, el tamaño no es un proxy de ninguna de las dos. Si se desploma,
lo era. Y si la varianza entre departamentos es chica frente a la de adentro, el
mapa departamental —que es lo que el trabajo dibuja— explica menos de lo que
sugiere.

Salidas en `outputs/tables/modelo_*.csv`.

Uso:
    python -m src.analysis.run_modelo
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm


from src.common import get_logger, load_config, paths

log = get_logger("analysis.modelo")

ALPHA_NB = 1.0


def datos(p) -> pd.DataFrame:
    cov = pd.read_parquet(p.processed / "covariables_ciudad.parquet")
    den = pd.read_parquet(p.processed / "denom_cohorte_ciudad.parquet")
    pl = pd.read_parquet(p.processed / "analysis_players.parquet")
    k = pl.groupby("ciudad_id").size().rename("k")

    d = cov.merge(den, on="ciudad_id", how="inner").join(k, on="ciudad_id")
    d["k"] = d["k"].fillna(0.0)
    d = d[(d["nacimientos_cohorte"] > 0) & (d["pob_ciudad"] > 0)].copy()
    d["log_pob"] = np.log(d["pob_ciudad"])
    # +1 km porque hay ciudades que tienen el club adentro y log(0) no existe.
    d["log_km"] = np.log(d["km_club_formador"] + 1)
    d["offset"] = np.log(d["nacimientos_cohorte"])
    return d


def ajustar_nb(d: pd.DataFrame, terminos: list[str], etiqueta: str) -> dict:
    sub = d.dropna(subset=terminos + ["k", "offset"])
    X = sm.add_constant(sub[terminos])
    fam = sm.families.NegativeBinomial(alpha=ALPHA_NB)
    m = sm.GLM(sub["k"], X, family=fam, offset=sub["offset"]).fit()
    nulo = sm.GLM(sub["k"], np.ones((len(sub), 1)), family=fam,
                  offset=sub["offset"]).fit()
    ci = m.conf_int()
    return {
        "modelo": etiqueta, "n_ciudades": len(sub), "aic": m.aic,
        "pseudo_r2_mcfadden": 1 - m.llf / nulo.llf,
        "coeficientes": pd.DataFrame({
            "modelo": etiqueta,
            "termino": m.params.index,
            "coef": m.params.values,
            "IRR": np.exp(m.params.values),
            "IRR_ic_lo": np.exp(ci[0].values),
            "IRR_ic_hi": np.exp(ci[1].values),
            "p": m.pvalues.values,
        }),
    }


def multinivel(d: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Cuánta de la variación es ENTRE departamentos y cuánta adentro.

    **Por qué no es un GLMM.** El camino natural sería un Poisson con intercepto
    aleatorio por departamento, pero `PoissonBayesMixedGLM` de statsmodels no
    acepta *offset*, y sin la exposición —los nacidos vivos de cada ciudad— el
    modelo ajusta conteos crudos contra covariables y diverge: los coeficientes
    salen del orden de $10^{14}$ y el ajuste avisa que no convergió. Forzarlo
    habría dado una partición de varianza inventada.

    **Lo que se hace en cambio.** Una descomposición de varianza sobre los
    residuos de Pearson del modelo binomial negativo con covariables, que sí
    lleva offset y sí converge. El residuo de Pearson mide cuánto se aparta cada
    ciudad de lo que el modelo predice para ella; si esos desvíos se agrupan por
    departamento, hay señal departamental más allá del tamaño, la distancia y el
    NBI. Es una descomposición tipo ANOVA de un nivel, con los departamentos
    ponderados por su cantidad de ciudades:

        V_entre  = varianza de las medias departamentales de los residuos
        V_dentro = media de las varianzas dentro de cada departamento
        ICC      = V_entre / (V_entre + V_dentro)

    No es lo mismo que el ICC de un GLMM —no separa la varianza de muestreo
    Poisson de la varianza real entre departamentos— y por eso **sobreestima**
    el componente de adentro cuando las ciudades son chicas. Se declara como
    cota inferior del agrupamiento departamental, no como estimación puntual.
    """
    sub = d.dropna(subset=["log_pob", "log_km", "pct_nbi", "k", "offset"]).copy()
    terminos = ["log_pob", "log_km", "pct_nbi"]
    X = sm.add_constant(sub[terminos])
    fam = sm.families.NegativeBinomial(alpha=ALPHA_NB)
    m = sm.GLM(sub["k"], X, family=fam, offset=sub["offset"]).fit()
    ci = m.conf_int()

    sub["resid"] = m.resid_pearson
    # Solo departamentos con al menos dos ciudades: con una sola, la varianza
    # interna no está definida y el departamento no aporta información sobre el
    # agrupamiento.
    g = sub.groupby("dept_id")["resid"]
    tam = g.size()
    validos = tam[tam >= 2].index
    gv = sub[sub["dept_id"].isin(validos)].groupby("dept_id")["resid"]

    medias, varianzas, pesos = gv.mean(), gv.var(ddof=1), gv.size()
    v_entre = float(np.average((medias - np.average(medias, weights=pesos)) ** 2,
                               weights=pesos))
    v_dentro = float(np.average(varianzas, weights=pesos))
    icc = v_entre / (v_entre + v_dentro)

    fijos = pd.DataFrame({
        "termino": m.params.index,
        "coef": m.params.values,
        "IRR": np.exp(m.params.values),
        "IRR_ic_lo": np.exp(ci[0].values),
        "IRR_ic_hi": np.exp(ci[1].values),
        "p": m.pvalues.values,
    })
    varianza = pd.DataFrame([{
        "n_ciudades": len(sub),
        "n_departamentos": int(sub["dept_id"].nunique()),
        "n_departamentos_con_2_o_mas_ciudades": int(len(validos)),
        "var_entre_departamentos": v_entre,
        "var_dentro_de_departamento": v_dentro,
        "icc": icc,
        "metodo": ("descomposición de varianza sobre residuos de Pearson del "
                   "binomial negativo con offset; no es el ICC de un GLMM"),
        "lectura": ("fracción de la variación NO explicada por tamaño, distancia "
                    "y NBI que corresponde a diferencias entre departamentos. El "
                    "resto queda entre ciudades del mismo departamento: un ICC "
                    "bajo quiere decir que el mapa departamental resume mal el "
                    "fenómeno."),
    }])
    return fijos, varianza


def main() -> None:
    load_config()
    p = paths()
    d = datos(p)

    especificaciones = [
        (["log_pob"], "1. solo tamaño"),
        (["log_km"], "2. solo distancia al club formador"),
        (["pct_nbi"], "3. solo NBI"),
        (["log_pob", "log_km"], "4. tamaño + distancia"),
        (["log_pob", "log_km", "pct_nbi"], "5. tamaño + distancia + NBI"),
    ]
    resumen, coefs = [], []
    for terminos, etiqueta in especificaciones:
        r = ajustar_nb(d, terminos, etiqueta)
        coefs.append(r.pop("coeficientes"))
        resumen.append(r)

    res = pd.DataFrame(resumen)
    co = pd.concat(coefs, ignore_index=True)
    res.to_csv(p.tables / "modelo_comparacion.csv", index=False, encoding="utf-8")
    co.to_csv(p.tables / "modelo_coeficientes.csv", index=False, encoding="utf-8")

    log.info("\n%s", res.round(4).to_string(index=False))
    log.info("\n%s", co[co["termino"] != "const"].round(4).to_string(index=False))

    fijos, varianza = multinivel(d)
    fijos.to_csv(p.tables / "modelo_multinivel_fijos.csv", index=False, encoding="utf-8")
    varianza.to_csv(p.tables / "modelo_multinivel_varianza.csv",
                    index=False, encoding="utf-8")
    log.info("\n--- multinivel (intercepto aleatorio por departamento) ---")
    log.info("\n%s", fijos.round(4).to_string(index=False))
    v = varianza.iloc[0]
    log.info("var entre departamentos = %.3f | var dentro = %.3f | ICC = %.3f "
             "(%.0f%% de la variacion residual es ENTRE departamentos)",
             v["var_entre_departamentos"], v["var_dentro_de_departamento"],
             v["icc"], 100 * v["icc"])


if __name__ == "__main__":
    main()
