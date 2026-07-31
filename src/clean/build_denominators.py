"""Fase 3b — Denominadores por cohorte de nacimiento.

**El problema que resuelve.** La versión anterior comparaba futbolistas nacidos
en 1970 contra la población censada en 2022. Eso no mide nacimientos: mide
quiénes seguían vivos y residiendo en el mismo lugar cincuenta años después, y
está contaminado por mortalidad y sobre todo por migración interna, que en
Argentina va justamente del interior al centro.

**La solución.** El denominador es ahora el número de **nacidos vivos** de esa
cohorte en ese lugar.

    Provincia   dato real, DEIS 1914–2024, por año de nacimiento.
    Departamento / ciudad
                estimado: se reparten los nacimientos provinciales reales entre
                los departamentos según la participación de cada uno en la
                población de su provincia, tomada del censo más cercano al año
                de nacimiento (1991, 2001, 2010 o 2022).

El reparto intraprovincial es un supuesto —que la distribución de nacimientos
dentro de una provincia se parece a la de la población—, y por eso se valida
contra los nacimientos departamentales reales del RENAPER (2012–2022) en
`qa_validacion_denominador.csv`. No se interpola entre censos: se usa el más
cercano, sin suavizar.

Un detalle que hace válida la comparación: la serie del DEIS cuenta nacimientos
**ocurridos**, por lugar del parto, que es la misma definición que usa el `P19`
de Wikidata. Si alguien nació en una maternidad de la Capital, aparece en la
Capital en las dos puntas del cociente.

Salidas en `data/processed/`:
    nacimientos_provincia_anio.parquet
    denom_cohorte_provincia.parquet
    denom_cohorte_departamento.parquet
    denom_cohorte_ciudad.parquet
    outputs/tables/qa_validacion_denominador.csv

Uso:
    python -m src.clean.build_denominators
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.clean.geo_units import collapse_caba, region_of
from src.common import get_logger, load_config, paths

log = get_logger("clean.denominadores")

# Columnas de la serie del DEIS -> código INDEC de provincia.
# Los nombres vienen con erratas en la fuente («medoza», «santiengo»); se
# respetan tal cual están para que el mapeo no dependa de una corrección
# silenciosa río arriba.
DEIS_A_INDEC = {
    "capital_federal": "02", "buenos_aires": "06", "catamarca": "10",
    "cordoba": "14", "corrientes": "18", "chaco": "22", "chubut": "26",
    "entre_rios": "30", "formosa": "34", "jujuy": "38", "la_pampa": "42",
    "la_rioja": "46", "medoza": "50", "misiones": "54", "neuquen": "58",
    "rio_negro": "62", "salta": "66", "san_juan": "70", "san_luis": "74",
    "santa_cruz": "78", "santa_fe": "82", "santiengo_del_estero": "86",
    "tucuman": "90", "tierra del fuego-antártida-islas-atlántico sud": "94",
}

CENSOS = [1991, 2001, 2010, 2022]


def censo_mas_cercano(anio: int) -> int:
    return min(CENSOS, key=lambda c: abs(c - anio))


def leer_nacimientos_provincia(p) -> pd.DataFrame:
    """Serie del DEIS en formato largo: provincia × año × nacimientos."""
    ruta = p.raw / "nacimientos" / "deis_nacidos_vivos_jurisdiccion_1914_2024.xlsx"
    ancho = pd.read_excel(ruta)
    ancho["anio"] = pd.to_datetime(ancho["anio"]).dt.year
    faltan = set(DEIS_A_INDEC) - set(ancho.columns)
    if faltan:
        raise ValueError(f"la serie del DEIS cambió de columnas: faltan {sorted(faltan)}")
    largo = (ancho.melt(id_vars="anio", value_vars=list(DEIS_A_INDEC),
                        var_name="col", value_name="nacimientos")
                  .assign(prov_id=lambda d: d["col"].map(DEIS_A_INDEC))
                  .drop(columns="col")
                  .dropna(subset=["nacimientos"]))
    largo["nacimientos"] = largo["nacimientos"].astype(int)
    return largo[["prov_id", "anio", "nacimientos"]]


def verificar_cobertura(nac: pd.DataFrame, y0: int, y1: int) -> None:
    """Falla si la serie tiene huecos dentro de la ventana de análisis.

    No es paranoia: la serie del DEIS **no trae 1971–1974**. Sin este chequeo,
    la cohorte 1970–1974 quedaba con un denominador de un solo año y su tasa
    salía cinco veces más alta, sin que nada fallara.
    """
    presentes = set(nac["anio"].unique())
    faltan = [y for y in range(y0, y1 + 1) if y not in presentes]
    if faltan:
        raise ValueError(
            f"la serie de nacimientos no cubre {faltan} dentro de la ventana "
            f"{y0}–{y1}. Corregir `cohorts.analysis_min_year` en config.yaml: "
            f"un denominador incompleto infla la tasa de esa cohorte en silencio.")
    esperado = len(set(nac["prov_id"])) * (y1 - y0 + 1)
    celdas = len(nac[nac["anio"].between(y0, y1)])
    if celdas != esperado:
        raise ValueError(f"faltan celdas provincia×año: {celdas} de {esperado}")


def participacion_departamental(p) -> pd.DataFrame:
    """Participación de cada departamento en la población de su provincia, por censo."""
    hist = pd.read_parquet(p.processed / "pop_dept_historica.parquet")
    hist["prov_id"] = hist["dept_id"].str[:2]
    total_prov = hist.groupby(["censo", "prov_id"])["pob"].transform("sum")
    hist["share"] = hist["pob"] / total_prov
    return hist[["censo", "prov_id", "dept_id", "pob", "share"]]


def estimar_por_departamento(nac: pd.DataFrame, shares: pd.DataFrame,
                             y0: int, y1: int) -> pd.DataFrame:
    """Nacimientos estimados por departamento acumulados en la ventana [y0, y1]."""
    ventana = nac[nac["anio"].between(y0, y1)].copy()
    ventana["censo"] = ventana["anio"].map(censo_mas_cercano)
    por_censo = ventana.groupby(["prov_id", "censo"], as_index=False)["nacimientos"].sum()
    est = por_censo.merge(shares, on=["prov_id", "censo"], how="left")
    est["nacimientos_est"] = est["nacimientos"] * est["share"]
    return (est.groupby("dept_id", as_index=False)["nacimientos_est"].sum()
               .rename(columns={"nacimientos_est": "nacimientos_cohorte"}))


def validar_contra_renaper(p, nac: pd.DataFrame, shares: pd.DataFrame) -> pd.DataFrame:
    """¿Cuánto se parece el reparto estimado al reparto real de nacimientos?

    RENAPER publica nacimientos por departamento 2012–2022. Son cohortes
    demasiado recientes para tener futbolistas profesionales, pero sirven para
    medir el error del supuesto de reparto intraprovincial, que es lo único que
    este módulo asume.
    """
    real = pd.read_csv(p.raw / "nacimientos" / "renaper_nacimientos_departamento_2012_2022.csv")
    real = real.dropna(subset=["departamento_id"])
    real["dept_id_raw"] = real["departamento_id"].astype(int).astype(str).str.zfill(5)
    real["dept_id"] = real["dept_id_raw"].map(collapse_caba)
    real = (real.groupby("dept_id", as_index=False)["nacimientos_cantidad"].sum()
                .rename(columns={"nacimientos_cantidad": "nacimientos_reales"}))

    est = estimar_por_departamento(nac, shares, 2012, 2022)
    comp = est.merge(real, on="dept_id", how="inner")
    comp["prov_id"] = comp["dept_id"].str[:2]
    comp["error_rel"] = (comp["nacimientos_cohorte"] - comp["nacimientos_reales"]) / \
                        comp["nacimientos_reales"].replace(0, np.nan)

    # La correlación relevante es la del reparto DENTRO de cada provincia: los
    # totales provinciales coinciden por construcción.
    r_global = float(np.corrcoef(comp["nacimientos_cohorte"], comp["nacimientos_reales"])[0, 1])
    resumen = pd.DataFrame([{
        "departamentos_comparados": len(comp),
        "correlacion_pearson": r_global,
        "error_relativo_mediano_abs": float(comp["error_rel"].abs().median()),
        "pct_dentro_del_20": float(100 * (comp["error_rel"].abs() <= 0.20).mean()),
        "cohortes_usadas": "2012–2022 (RENAPER)",
        "lectura": ("mide el error del supuesto de reparto intraprovincial, "
                    "que es lo único que se asume para bajar de provincia a "
                    "departamento; los totales por provincia son dato real"),
    }])
    return resumen, comp


def main() -> None:
    cfg = load_config()
    p = paths()
    c = cfg["cohorts"]
    y0, y1 = c["analysis_min_year"], c["analysis_max_year"]

    nac = leer_nacimientos_provincia(p)
    verificar_cobertura(nac, y0, y1)
    nac.to_parquet(p.processed / "nacimientos_provincia_anio.parquet", index=False)
    log.info("serie DEIS: %d–%d, %s nacimientos en total",
             nac["anio"].min(), nac["anio"].max(), f"{nac['nacimientos'].sum():,}")

    # --- provincia: dato real ------------------------------------------------
    prov = (nac[nac["anio"].between(y0, y1)]
            .groupby("prov_id", as_index=False)["nacimientos"].sum()
            .rename(columns={"nacimientos": "nacimientos_cohorte"}))
    prov.to_parquet(p.processed / "denom_cohorte_provincia.parquet", index=False)
    log.info("ventana %d–%d: %s nacimientos reales", y0, y1,
             f"{prov['nacimientos_cohorte'].sum():,}")

    # --- departamento: estimado ---------------------------------------------
    shares = participacion_departamental(p)
    dept = estimar_por_departamento(nac, shares, y0, y1)
    dept["prov_id"] = dept["dept_id"].str[:2]
    dept["region"] = dept["dept_id"].map(lambda d: region_of(d, cfg))
    dept.to_parquet(p.processed / "denom_cohorte_departamento.parquet", index=False)

    # --- ciudad: estimado, repartiendo el departamento por localidad --------
    # Dentro del departamento solo hay un reparto por localidad disponible, el
    # del censo 2022. Se declara: es el eslabón más débil de la cadena.
    tamano = pd.read_parquet(p.processed / "tamano_localidad.parquet")
    tamano["dept_id"] = tamano["dept_id"].astype(str)
    share_loc = tamano.copy()
    share_loc["share_loc"] = share_loc["pob_localidad"] / \
        share_loc.groupby("dept_id")["pob_localidad"].transform("sum")
    ciudad = share_loc.merge(dept[["dept_id", "nacimientos_cohorte"]], on="dept_id", how="left")
    ciudad["nac_localidad"] = ciudad["nacimientos_cohorte"] * ciudad["share_loc"]
    ciudad["ciudad_id"] = np.where(ciudad["aglomerado_id"].notna(),
                                   "AGLO_" + ciudad["aglomerado_id"].astype(str),
                                   "LOC_" + ciudad["localidad_id"].astype(str))
    por_ciudad = (ciudad.groupby("ciudad_id", as_index=False)["nac_localidad"].sum()
                        .rename(columns={"nac_localidad": "nacimientos_cohorte"}))
    por_ciudad.to_parquet(p.processed / "denom_cohorte_ciudad.parquet", index=False)

    # La misma estimación sin agrupar por aglomerado: la necesita el análisis de
    # robustez de H1, que usa la localidad censal aislada como unidad.
    (ciudad[["localidad_id", "localidad_nombre", "dept_id", "pob_localidad",
             "nac_localidad"]]
     .rename(columns={"nac_localidad": "nacimientos_cohorte"})
     .to_parquet(p.processed / "denom_cohorte_localidad.parquet", index=False))

    # --- validación ----------------------------------------------------------
    resumen, detalle = validar_contra_renaper(p, nac, shares)
    resumen.to_csv(p.tables / "qa_validacion_denominador.csv", index=False, encoding="utf-8")
    detalle.to_csv(p.tables / "qa_validacion_denominador_detalle.csv",
                   index=False, encoding="utf-8")
    log.info("\n%s", resumen.drop(columns="lectura").to_string(index=False))
    log.info("departamentos: %d | ciudades: %d", len(dept), len(por_ciudad))


if __name__ == "__main__":
    main()
