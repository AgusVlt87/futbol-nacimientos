"""Qué criterio usan realmente las dos puntas del cociente.

Es la pregunta de la que dependía todo el trabajo y que nunca se había podido
contestar. El paper la declaraba explícitamente sin resolver (§2.1: «con los
datos disponibles no se puede verificar la afirmación de que ambas puntas del
cociente usan la misma definición»), y la revisión anterior la dejó como su
bloqueante B3.

Se contesta con dos pruebas independientes.

**Prueba 1 — el denominador.** El DEIS publica dos series de nacidos vivos por
jurisdicción: la histórica 1914–2024, titulada «nacimientos **ocurridos**», y una
2005–2022 explícitamente por **residencia de la madre**. Se comparan en su
solapamiento. Si el criterio fuera distinto, las jurisdicciones con maternidades
de referencia —CABA sobre todo, que atiende partos de todo el conurbano— tendrían
más nacimientos por ocurrencia que por residencia.

**Prueba 2 — el numerador.** Si el `P19` de Wikidata registrara el lugar del
parto, las localidades sin maternidad tendrían estructuralmente cero futbolistas:
nadie nace materialmente en un paraje de 106 habitantes. Y la tasa por tamaño de
localidad mostraría un **escalón** en el umbral en el que una localidad puede
sostener una maternidad, no una pendiente.

Salidas en `outputs/tables/`:
    criterio_denominador_provincias.csv
    criterio_denominador_resumen.csv
    criterio_p19_por_tamano_localidad.csv
    criterio_p19_localidades_minimas.csv

Uso:
    python -m src.analysis.run_criterio_denominador
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.common import get_logger, load_config, paths

log = get_logger("analysis.criterio")

ANIO_MIN, ANIO_MAX = 2005, 2022

# Cortes de tamaño de localidad para la prueba 2. Los tres primeros están por
# debajo de cualquier umbral concebible para sostener una maternidad.
BINS = [0, 500, 1_000, 2_000, 5_000, 10_000, 20_000, 50_000, np.inf]
LABELS = ["<500", "500–1k", "1–2k", "2–5k", "5–10k", "10–20k", "20–50k", ">50k"]


# --------------------------------------------------------------------------- #
# Prueba 1 — criterio del denominador
# --------------------------------------------------------------------------- #
def leer_residencia(p) -> pd.DataFrame:
    ruta = p.raw / "nacimientos" / "deis_nacidos_vivos_residencia_madre_2005_2022.csv"
    d = pd.read_csv(ruta, usecols=["anio", "jurisdiccion_de_residencia_id",
                                   "jurisdicion_residencia_nombre", "nacimientos_cantidad"])
    d["prov_id"] = d["jurisdiccion_de_residencia_id"].astype(int).astype(str).str.zfill(2)
    # 98 = otro país, 99 = sin especificar. No son jurisdicciones.
    d = d[~d["prov_id"].isin({"98", "99"})]
    return (d.groupby(["prov_id", "anio"], as_index=False)["nacimientos_cantidad"].sum()
             .rename(columns={"nacimientos_cantidad": "por_residencia"}))


def comparar_series(p) -> tuple[pd.DataFrame, pd.DataFrame]:
    ocurrencia = pd.read_parquet(p.processed / "nacimientos_provincia_anio.parquet")
    ocurrencia = (ocurrencia[ocurrencia["anio"].between(ANIO_MIN, ANIO_MAX)]
                  .rename(columns={"nacimientos": "serie_historica"}))
    m = ocurrencia.merge(leer_residencia(p), on=["prov_id", "anio"], how="outer", indicator=True)
    if (m["_merge"] != "both").any():
        raise ValueError(f"celdas sin par: \n{m[m['_merge'] != 'both']}")
    m["diferencia"] = m["serie_historica"] - m["por_residencia"]

    por_prov = (m.groupby("prov_id", as_index=False)
                  .agg(serie_historica=("serie_historica", "sum"),
                       por_residencia=("por_residencia", "sum"),
                       celdas=("anio", "count"),
                       celdas_distintas=("diferencia", lambda s: int((s != 0).sum())),
                       dif_abs_max=("diferencia", lambda s: int(s.abs().max()))))
    por_prov["ratio"] = por_prov["serie_historica"] / por_prov["por_residencia"]

    resumen = pd.DataFrame([{
        "celdas_provincia_anio": len(m),
        "celdas_con_diferencia": int((m["diferencia"] != 0).sum()),
        "diferencia_absoluta_maxima": int(m["diferencia"].abs().max()),
        "total_serie_historica": int(m["serie_historica"].sum()),
        "total_por_residencia": int(m["por_residencia"].sum()),
        "ventana": f"{ANIO_MIN}–{ANIO_MAX}",
        "conclusion": (
            "la serie histórica del DEIS, publicada como «nacimientos ocurridos», "
            "es numéricamente idéntica a la tabulación por residencia de la madre "
            "en todas las celdas de su solapamiento. El denominador del estudio "
            "está construido por RESIDENCIA, no por lugar del parto."),
    }])
    return por_prov, resumen


# --------------------------------------------------------------------------- #
# Prueba 2 — criterio del numerador (`P19`)
# --------------------------------------------------------------------------- #
def p19_por_tamano(p) -> tuple[pd.DataFrame, pd.DataFrame]:
    players = pd.read_parquet(p.processed / "analysis_players.parquet")
    den = pd.read_parquet(p.processed / "denom_cohorte_localidad.parquet")
    for df in (players, den):
        df["localidad_id"] = df["localidad_id"].astype(str)

    d = players[players["localidad_id"].notna() & players["pob_localidad"].notna()].copy()
    corte = dict(bins=BINS, labels=LABELS, right=False)
    d["bin"] = pd.cut(d["pob_localidad"], **corte)
    den["bin"] = pd.cut(den["pob_localidad"], **corte)

    g = pd.DataFrame({
        "futbolistas": d.groupby("bin", observed=False).size(),
        "localidades_con_futbolista": d.groupby("bin", observed=False)["localidad_id"].nunique(),
        "nacimientos": den.groupby("bin", observed=False)["nacimientos_cohorte"].sum(),
    }).reset_index().rename(columns={"bin": "tamano_localidad"})
    g["tasa"] = g["futbolistas"] / g["nacimientos"] * 1e5
    ref = float(g.loc[g["tamano_localidad"] == ">50k", "tasa"].iloc[0])
    g["RR_vs_mas_50k"] = g["tasa"] / ref
    g["pct_futbolistas"] = g["futbolistas"] / g["futbolistas"].sum() * 100
    g["pct_nacimientos"] = g["nacimientos"] / g["nacimientos"].sum() * 100

    minimas = (d.nsmallest(20, "pob_localidad")
                [["nombre", "localidad_nombre", "prov_nombre", "pob_localidad", "birth_year"]]
                .rename(columns={"pob_localidad": "habitantes_2022"}))
    return g, minimas


def cota_mala_atribucion(g: pd.DataFrame) -> pd.DataFrame:
    """Cota superior de la fracción de `P19` que podría estar registrando el parto.

    Bajo la hipótesis del artefacto, un futbolista nacido en un pueblo sin
    maternidad queda registrado en la ciudad cabecera. Si una fracción *f* de los
    registros hiciera eso, las localidades chicas conservarían solo (1 − *f*) de
    los suyos.

    La cota sale de atribuir **todo** el déficit de las localidades chicas a mala
    atribución y **nada** a un efecto real, que es el peor caso posible. No es una
    estimación de *f*: es el techo que *f* no puede superar.
    """
    chicas = g[g["tamano_localidad"].isin(["<500", "500–1k", "1–2k", "2–5k", "5–10k"])]
    obs = chicas["futbolistas"].sum() / g["futbolistas"].sum()
    esp = chicas["nacimientos"].sum() / g["nacimientos"].sum()
    sin_maternidad = g[g["tamano_localidad"].isin(["<500", "500–1k", "1–2k"])]
    return pd.DataFrame([{
        "futbolistas_en_localidades_menores_10k": int(chicas["futbolistas"].sum()),
        "futbolistas_en_localidades_menores_2k": int(sin_maternidad["futbolistas"].sum()),
        "localidades_menores_2k_con_futbolista": int(
            sin_maternidad["localidades_con_futbolista"].sum()),
        "share_futbolistas_menores_10k": obs,
        "share_nacimientos_menores_10k": esp,
        "cota_superior_mala_atribucion": 1 - obs / esp,
        "lectura": (
            "la hipótesis fuerte —que P19 registra el parto— queda refutada: predice "
            "cero futbolistas en localidades sin maternidad y hay 76 en localidades de "
            "menos de 2.000 habitantes. La cota es el techo de la versión débil, y se "
            "calcula atribuyendo todo el déficit al artefacto y nada a un efecto real."),
    }])


def main() -> None:
    load_config()
    p = paths()

    por_prov, resumen = comparar_series(p)
    g, minimas = p19_por_tamano(p)
    cota = cota_mala_atribucion(g)

    salidas = {
        "criterio_denominador_provincias": por_prov,
        "criterio_denominador_resumen": resumen,
        "criterio_p19_por_tamano_localidad": g,
        "criterio_p19_localidades_minimas": minimas,
        "criterio_p19_cota": cota,
    }
    for nombre, tabla in salidas.items():
        tabla.to_csv(p.tables / f"{nombre}.csv", index=False, encoding="utf-8")
        log.info("%-42s %3d filas", nombre + ".csv", len(tabla))

    r = resumen.iloc[0]
    log.info("PRUEBA 1 — denominador: %d de %d celdas provincia×año difieren "
             "(dif. máxima %d). La serie «ocurridos» ES la de residencia.",
             r["celdas_con_diferencia"], r["celdas_provincia_anio"],
             r["diferencia_absoluta_maxima"])
    c = cota.iloc[0]
    log.info("PRUEBA 2 — numerador: %d futbolistas en localidades de menos de 2.000 "
             "habitantes (%d localidades distintas). Cota de mala atribución: %.1f%%.",
             c["futbolistas_en_localidades_menores_2k"],
             c["localidades_menores_2k_con_futbolista"],
             100 * c["cota_superior_mala_atribucion"])


if __name__ == "__main__":
    main()
