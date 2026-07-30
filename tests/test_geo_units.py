"""Tests de las funciones críticas de normalización geográfica.

Son críticas porque las comparten numerador y denominador: si `collapse_caba`
agrupa distinto en un lado que en el otro, las tasas per cápita quedan mal sin
que nada falle ruidosamente.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from src.clean.geo_units import (
    CABA_DEPT_ID,
    city_size_bin,
    city_size_series,
    collapse_caba,
    haversine_km,
    normalize_name,
    region_of,
)
from src.common import load_config

CFG = load_config()
SCHEME = CFG["city_size"]["schemes"]["principal"]


# --------------------------------------------------------------------------- #
# normalize_name
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("raw, esperado", [
    ("Gualeguaychú", "gualeguaychu"),
    ("SAN MIGUEL DE TUCUMÁN", "san miguel de tucuman"),
    ("  Villa   Ángela  ", "villa angela"),
    ("Ciudad Autónoma de Buenos Aires", "ciudad autonoma de buenos aires"),
    ("Coronel Suárez", "coronel suarez"),
    ("Concepción del Uruguay", "concepcion del uruguay"),
    (None, ""),
])
def test_normalize_name(raw, esperado):
    assert normalize_name(raw) == esperado


def test_normalize_name_puntuacion():
    # Los homónimos con y sin puntuación tienen que colapsar al mismo string.
    assert normalize_name("Gral. Pico") == normalize_name("Gral  Pico")
    assert normalize_name("25 de Mayo") == "25 de mayo"


# --------------------------------------------------------------------------- #
# collapse_caba
# --------------------------------------------------------------------------- #
def test_collapse_caba_agrupa_comunas():
    for comuna in ["02007", "02014", "02105"]:
        assert collapse_caba(comuna) == CABA_DEPT_ID


def test_collapse_caba_no_toca_el_resto():
    assert collapse_caba("06427") == "06427"      # La Matanza
    assert collapse_caba("82084") == "82084"      # Rosario
    assert collapse_caba(None) is None


# --------------------------------------------------------------------------- #
# city_size_bin
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("pob, esperado", [
    (0, "<10k"),
    (9_999, "<10k"),
    (10_000, "10–50k"),        # el borde pertenece al tramo de arriba
    (43_909, "10–50k"),        # Gualeguay
    (50_000, "50–100k"),
    (99_999, "50–100k"),
    (115_982, "100–500k"),     # Santa Rosa, La Pampa
    (500_000, ">500k"),
    (16_224_751, ">500k"),     # Gran Buenos Aires
])
def test_city_size_bin(pob, esperado):
    assert city_size_bin(pob, SCHEME) == esperado


def test_city_size_bin_faltante():
    assert math.isnan(city_size_bin(None, SCHEME))
    assert math.isnan(city_size_bin(np.nan, SCHEME))


def test_city_size_bins_no_dejan_huecos():
    """Todo valor no negativo cae en exactamente un tramo."""
    for scheme in CFG["city_size"]["schemes"].values():
        for pob in [0, 1, 999, 1_000, 9_999, 29_999, 100_000, 249_999, 3_000_000]:
            assert not pd.isna(city_size_bin(pob, scheme)), (scheme["labels"], pob)


def test_city_size_scheme_mal_formado():
    malo = {"bins": [0, 100], "labels": ["a", "b"]}   # sobra una etiqueta
    with pytest.raises(ValueError):
        city_size_bin(50, malo)


def test_city_size_series_es_ordenada():
    s = city_size_series(pd.Series([500, 60_000, 2_000_000]), SCHEME)
    assert list(s) == ["<10k", "50–100k", ">500k"]
    assert s.ordered
    assert list(s.categories) == SCHEME["labels"]


# --------------------------------------------------------------------------- #
# region_of
# --------------------------------------------------------------------------- #
def test_region_amba_gana_sobre_provincia():
    # La Matanza es provincia de Buenos Aires pero es AMBA, no Pampeana.
    assert region_of("06427", CFG) == "AMBA"
    assert region_of(CABA_DEPT_ID, CFG) == "AMBA"
    assert region_of("02007", CFG) == "AMBA"


def test_region_interior():
    assert region_of("06056", CFG) == "Pampeana"      # Bahía Blanca
    assert region_of("82084", CFG) == "Pampeana"      # Rosario
    assert region_of("90084", CFG) == "NOA"           # Tucumán
    assert region_of("54028", CFG) == "NEA"           # Misiones
    assert region_of("50007", CFG) == "Cuyo"          # Mendoza
    assert region_of("58042", CFG) == "Patagonia"     # Neuquén
    assert pd.isna(region_of(None, CFG))


def test_todas_las_provincias_tienen_region():
    """Ninguna provincia puede quedar sin región: sería un agujero en H2."""
    provincias = {f"{p:02d}" for p in
                  [2, 6, 10, 14, 18, 22, 26, 30, 34, 38, 42, 46, 50,
                   54, 58, 62, 66, 70, 74, 78, 82, 86, 90, 94]}
    for prov in provincias:
        assert not pd.isna(region_of(prov + "999", CFG)), prov


# --------------------------------------------------------------------------- #
# haversine_km
# --------------------------------------------------------------------------- #
def test_haversine_distancia_conocida():
    # Obelisco (CABA) -> Monumento a la Bandera (Rosario): ~278 km.
    d = haversine_km(-34.6037, -58.3816, -32.9468, -60.6393)
    assert 270 < float(d) < 290


def test_haversine_cero_y_vectorizado():
    assert float(haversine_km(-34.6, -58.4, -34.6, -58.4)) == pytest.approx(0.0, abs=1e-9)
    d = haversine_km(-34.6, -58.4, np.array([-34.6, -32.9468]), np.array([-58.4, -60.6393]))
    assert d.shape == (2,)
    assert d[0] < d[1]
