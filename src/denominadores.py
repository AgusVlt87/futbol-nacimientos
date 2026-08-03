"""Carga de denominadores, con verificación de que no se pierda masa al unirlos.

**Por qué existe.** El join entre la tabla de unidades (`denom_ciudad_unica`,
`denom_departamento`) y la de nacidos vivos por cohorte estaba copiado en seis
módulos —`run_all`, `run_futbol`, `run_levels_and_flow`, `run_seleccion`,
`make_figures`, `make_figures_extra`—, siempre con `how="left"` y sin verificar
nada. Seis copias del mismo join es como se separan entre sí, y un `how="left"`
sin verificar es exactamente la forma que tenía el error que borró 1.049.301
nacimientos del denominador por ciudad.

Acá el join se hace una sola vez y se verifica que el total de nacimientos del
resultado sea el de la tabla de nacimientos, salvo las excepciones declaradas.
"""

from __future__ import annotations

import pandas as pd

from src.clean.padron_departamentos import SIN_LOCALIDAD_CENSAL, verificar_conservacion
from src.common import get_logger

log = get_logger("denominadores")


def _unir(unidades: pd.DataFrame, cohorte: pd.DataFrame, clave: str,
          contexto: str, excepciones: dict[str, str] | None = None) -> pd.DataFrame:
    excepciones = excepciones or {}
    huerfanos = set(cohorte[clave]) - set(unidades[clave])
    inesperados = huerfanos - set(excepciones)
    if inesperados:
        perdidos = cohorte[cohorte[clave].isin(inesperados)]["nacimientos_cohorte"].sum()
        raise ValueError(
            f"{contexto}: {len(inesperados)} unidad(es) tienen nacimientos pero no "
            f"figuran en la tabla de unidades, así que el join las descartaría "
            f"({perdidos:,.0f} nacimientos): {sorted(inesperados)[:20]}")

    out = unidades.merge(cohorte, on=clave, how="left")
    esperado = float(cohorte.loc[~cohorte[clave].isin(excepciones),
                                 "nacimientos_cohorte"].sum())
    verificar_conservacion(esperado, float(out["nacimientos_cohorte"].sum()),
                           contexto=contexto)
    if huerfanos:
        log.info("%s: excluidas por no tener población censada -> %s", contexto,
                 ", ".join(f"{k} ({excepciones[k]})" for k in sorted(huerfanos)))
    return out


def cargar_ciudades(p) -> pd.DataFrame:
    """Una fila por ciudad (aglomerado o localidad aislada) con su denominador."""
    return _unir(pd.read_parquet(p.processed / "denom_ciudad_unica.parquet"),
                 pd.read_parquet(p.processed / "denom_cohorte_ciudad.parquet"),
                 clave="ciudad_id", contexto="denominador por ciudad")


def cargar_departamentos(p, columnas: list[str] | None = None) -> pd.DataFrame:
    """Una fila por departamento con su denominador de nacidos vivos.

    Los dos departamentos sin población censada (Islas del Atlántico Sur y
    Antártida Argentina) no están en `denom_departamento`; se declaran como
    excepción en lugar de desaparecer en silencio.
    """
    cohorte = pd.read_parquet(p.processed / "denom_cohorte_departamento.parquet")
    if columnas:
        cohorte = cohorte[["dept_id", *columnas]]
    return _unir(pd.read_parquet(p.processed / "denom_departamento.parquet"),
                 cohorte, clave="dept_id", contexto="denominador por departamento",
                 excepciones=SIN_LOCALIDAD_CENSAL)
