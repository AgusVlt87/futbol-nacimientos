"""Tests de las funciones estadísticas.

Se contrastan contra valores que scipy calcula por otra vía o contra casos con
respuesta analítica conocida.
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy import stats

from src.analysis.stats import (
    chi2_gof,
    fdr_bh,
    odds_ratio_ci,
    poisson_rate_ci,
    rate_ratio_ci,
    standardized_residuals,
)


# --------------------------------------------------------------------------- #
# chi2_gof
# --------------------------------------------------------------------------- #
def test_chi2_gof_coincide_con_scipy():
    obs = [30, 20, 50]
    props = [0.25, 0.25, 0.50]
    r = chi2_gof(obs, props)
    esperado = np.array(props) * sum(obs)
    ref = stats.chisquare(obs, f_exp=esperado)
    assert r.chi2 == pytest.approx(float(ref.statistic))
    assert r.p == pytest.approx(float(ref.pvalue))
    assert r.df == 2
    assert r.n == 100


def test_chi2_gof_ajuste_perfecto():
    r = chi2_gof([25, 25, 50], [0.25, 0.25, 0.50])
    assert r.chi2 == pytest.approx(0.0)
    assert r.p == pytest.approx(1.0)
    assert r.cohens_w == pytest.approx(0.0)


def test_chi2_gof_renormaliza_proporciones():
    """Da igual pasar proporciones o conteos poblacionales crudos."""
    a = chi2_gof([30, 70], [0.4, 0.6])
    b = chi2_gof([30, 70], [400_000, 600_000])
    assert a.chi2 == pytest.approx(b.chi2)


def test_chi2_gof_valida_entrada():
    with pytest.raises(ValueError):
        chi2_gof([10, 20], [0.5, 0.3, 0.2])
    with pytest.raises(ValueError):
        chi2_gof([10, 20], [0.0, 0.0])


def test_cohens_w_conocido():
    # chi2 = n * w^2  =>  con n=100 y w=0.3, chi2 = 9.
    obs = [65, 35]
    props = [0.5, 0.5]
    r = chi2_gof(obs, props)
    assert r.cohens_w == pytest.approx(np.sqrt(r.chi2 / 100))
    assert r.cramers_v == pytest.approx(r.cohens_w)  # k=2 => V = w


def test_residuos_marcan_la_celda_desviada():
    res = standardized_residuals([90, 10], [0.5, 0.5])
    assert res[0] > 2 and res[1] < -2
    assert res[0] == pytest.approx(-res[1])


# --------------------------------------------------------------------------- #
# poisson_rate_ci
# --------------------------------------------------------------------------- #
def test_poisson_rate_valor_puntual():
    rate, lo, hi = poisson_rate_ci([25], [50_000], per=100_000)
    assert rate[0] == pytest.approx(50.0)
    assert lo[0] < 50.0 < hi[0]


def test_poisson_rate_cero_no_da_negativo():
    rate, lo, hi = poisson_rate_ci([0], [10_000])
    assert rate[0] == 0.0
    assert lo[0] == 0.0
    assert hi[0] > 0.0


def test_poisson_ic_se_angosta_con_n():
    _, lo_c, hi_c = poisson_rate_ci([5], [10_000])
    _, lo_g, hi_g = poisson_rate_ci([500], [1_000_000])
    assert (hi_c - lo_c) > (hi_g - lo_g)


def test_poisson_exposicion_cero_es_nan():
    rate, lo, hi = poisson_rate_ci([3], [0])
    assert np.isnan(rate[0]) and np.isnan(hi[0])


# --------------------------------------------------------------------------- #
# rate_ratio_ci / odds_ratio_ci
# --------------------------------------------------------------------------- #
def test_rate_ratio_identidad():
    rr, lo, hi = rate_ratio_ci(50, 10_000, 50, 10_000)
    assert rr == pytest.approx(1.0)
    assert lo < 1.0 < hi


def test_rate_ratio_doble():
    rr, lo, hi = rate_ratio_ci(100, 10_000, 50, 10_000)
    assert rr == pytest.approx(2.0)
    assert lo > 1.0          # con estos n, el efecto es claro


def test_rate_ratio_con_cero_no_explota():
    rr, lo, hi = rate_ratio_ci(0, 10_000, 10, 10_000)
    assert np.isfinite(rr) and rr < 1


def test_odds_ratio_identidad_y_haldane():
    or_, lo, hi = odds_ratio_ci(10, 10, 10, 10)
    assert or_ == pytest.approx(1.0)
    assert lo < 1 < hi
    # Con una celda en cero, la corrección +0.5 mantiene el OR finito.
    or0, lo0, hi0 = odds_ratio_ci(0, 10, 10, 10)
    assert np.isfinite(or0) and or0 < 1


# --------------------------------------------------------------------------- #
# fdr_bh
# --------------------------------------------------------------------------- #
def test_fdr_monotono_y_acotado():
    p = [0.001, 0.008, 0.039, 0.041, 0.9]
    rechaza, adj = fdr_bh(p, alpha=0.05)
    assert np.all(np.diff(adj[np.argsort(p)]) >= -1e-12)   # no decrece
    assert np.all(adj <= 1.0)
    assert rechaza[0]
    assert not rechaza[-1]


def test_fdr_es_mas_conservador_que_crudo():
    p = np.array([0.04] * 10)
    _, adj = fdr_bh(p)
    assert np.all(adj >= p)


def test_fdr_no_altera_el_orden():
    p = np.array([0.5, 0.01, 0.2])
    _, adj = fdr_bh(p)
    assert np.argsort(adj).tolist() == np.argsort(p).tolist()
