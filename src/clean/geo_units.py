"""Funciones críticas de normalización geográfica.

Las usan tanto el numerador (jugadores) como el denominador (población): si
numerador y denominador no se agrupan con la misma regla, las tasas per cápita
mienten. Por eso viven en un solo lugar y tienen tests (`tests/test_geo_units.py`).
"""

from __future__ import annotations

import math
import re
import unicodedata

import numpy as np
import pandas as pd

# CABA se divide en 15 comunas, que el INDEC codifica como departamentos
# (02007, 02014, …). Asignar a un jugador la comuna donde cae el centroide de
# "Buenos Aires" no significa nada, así que a nivel departamento la ciudad se
# trata como una unidad sola.
CABA_PROV = "02"
CABA_DEPT_ID = "02000"
CABA_DEPT_NAME = "Ciudad Autónoma de Buenos Aires"

_PUNCT = re.compile(r"[^\w\s]", flags=re.UNICODE)
_SPACES = re.compile(r"\s+")


def normalize_name(name: str | None) -> str:
    """Nombre comparable: sin tildes, sin puntuación, minúsculas, sin dobles espacios.

    Solo para *comparar*, nunca para mostrar. La resolución geográfica se hace
    por coordenada; esto es el chequeo cruzado y el fallback.
    """
    if name is None or (isinstance(name, float) and math.isnan(name)):
        return ""
    s = unicodedata.normalize("NFKD", str(name))
    # Se descartan los diacríticos y también los caracteres invisibles de
    # formato/control (Cf, Cc). Los padrones oficiales traen guiones blandos
    # (U+00AD) sueltos que rompen el matching sin que se vean.
    s = "".join(c for c in s
                if not unicodedata.combining(c)
                and unicodedata.category(c) not in {"Cf", "Cc"})
    s = _PUNCT.sub(" ", s.lower())
    return _SPACES.sub(" ", s).strip()


def collapse_caba(dept_id: str | None) -> str | None:
    """Colapsa las comunas de CABA en una sola unidad de análisis."""
    if dept_id is None or (isinstance(dept_id, float) and math.isnan(dept_id)):
        return None
    dept_id = str(dept_id)
    return CABA_DEPT_ID if dept_id.startswith(CABA_PROV) else dept_id


def haversine_km(lat1, lon1, lat2, lon2):
    """Distancia en km sobre la esfera. Vectorizado."""
    r = 6371.0088
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dphi = p2 - p1
    dlam = np.radians(np.asarray(lon2) - np.asarray(lon1))
    a = np.sin(dphi / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dlam / 2) ** 2
    return 2 * r * np.arcsin(np.sqrt(a))


def city_size_bin(pop, scheme: dict) -> str | float:
    """Etiqueta de tramo de tamaño para una población.

    `scheme` viene de `config.yaml` (`city_size.schemes.<nombre>`): `bins` son
    los límites inferiores, con `null` final como infinito, y `labels` las
    etiquetas. Intervalos cerrados a izquierda: [inf, sup).
    """
    if pop is None or (isinstance(pop, float) and math.isnan(pop)):
        return np.nan
    edges = [b if b is not None else math.inf for b in scheme["bins"]]
    labels = scheme["labels"]
    if len(edges) != len(labels) + 1:
        raise ValueError("city_size: `bins` debe tener un elemento más que `labels`")
    pop = float(pop)
    for i in range(len(labels)):
        if edges[i] <= pop < edges[i + 1]:
            return labels[i]
    return np.nan


def city_size_series(pops: pd.Series, scheme: dict) -> pd.Series:
    """`city_size_bin` sobre una serie, devolviendo un Categorical ordenado."""
    values = pops.map(lambda v: city_size_bin(v, scheme))
    return pd.Categorical(values, categories=scheme["labels"], ordered=True)


def region_of(dept_id: str | None, cfg: dict) -> str | float:
    """Región del análisis descriptivo (AMBA, Pampeana, NOA, NEA, Cuyo, Patagonia).

    AMBA gana sobre la región de la provincia: un partido del Gran Buenos Aires
    es AMBA, no Pampeana. Es justamente el contraste que plantea H2.

    Los partidos del GBA se declaran por nombre en `config.yaml` y se resuelven
    contra el padrón del INDEC. Ver `padron_departamentos.codigos_amba`: la lista
    de códigos escrita a mano que había acá estaba doce códigos mal.
    """
    # Import diferido: `padron_departamentos` importa de este módulo, así que
    # traerlo arriba cerraría el ciclo. `codigos_amba` está cacheada.
    from src.clean.padron_departamentos import codigos_amba

    if dept_id is None or (isinstance(dept_id, float) and math.isnan(dept_id)):
        return np.nan
    dept_id = str(dept_id)
    amba = cfg["geography"]["amba"]
    if dept_id.startswith(amba["caba_province_code"]):
        return "AMBA"
    if dept_id in codigos_amba(cfg):
        return "AMBA"
    prov = dept_id[:2]
    for region, provs in cfg["geography"]["regiones"].items():
        if region == "AMBA":
            continue
        if prov in provs:
            return region
    return np.nan
