"""Herramientas estadísticas del estudio.

Regla del proyecto: ningún hallazgo se apoya solo en un p-valor. Cada función
devuelve el estadístico, sus grados de libertad, el p, el tamaño de efecto y el
intervalo de confianza — juntos, para que no se pueda reportar uno sin el otro.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict

import numpy as np
import pandas as pd
from scipy import stats


# --------------------------------------------------------------------------- #
# Bondad de ajuste
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class GofResult:
    chi2: float
    df: int
    p: float
    n: int
    cohens_w: float
    cramers_v: float

    def as_dict(self) -> dict:
        return asdict(self)


def chi2_gof(observed, expected_props) -> GofResult:
    """Chi-cuadrado de bondad de ajuste contra una distribución esperada.

    `expected_props` son las proporciones poblacionales reales (se renormalizan
    por las dudas). Nunca uniforme por defecto: el baseline es el dato.

    Cohen's w = sqrt(chi2 / n). Para bondad de ajuste con k categorías,
    Cramér's V = sqrt(chi2 / (n * (k-1))).
    """
    obs = np.asarray(observed, dtype=float)
    props = np.asarray(expected_props, dtype=float)
    if obs.shape != props.shape:
        raise ValueError("observado y esperado deben tener el mismo largo")
    if np.any(props < 0) or props.sum() <= 0:
        raise ValueError("las proporciones esperadas deben ser positivas")
    props = props / props.sum()
    n = obs.sum()
    exp = props * n
    chi2 = float(((obs - exp) ** 2 / exp).sum())
    k = len(obs)
    df = k - 1
    p = float(stats.chi2.sf(chi2, df))
    w = float(np.sqrt(chi2 / n)) if n else np.nan
    v = float(np.sqrt(chi2 / (n * df))) if n and df else np.nan
    return GofResult(chi2=chi2, df=df, p=p, n=int(n), cohens_w=w, cramers_v=v)


def standardized_residuals(observed, expected_props) -> np.ndarray:
    """Residuos estandarizados: qué categorías empujan el chi-cuadrado.

    Se usan los residuos ajustados (dividen por sqrt(1-p)), que bajo H0 son
    aproximadamente N(0,1): |r| > 2 marca una celda que se aparta.
    """
    obs = np.asarray(observed, dtype=float)
    props = np.asarray(expected_props, dtype=float)
    props = props / props.sum()
    n = obs.sum()
    exp = props * n
    return (obs - exp) / np.sqrt(exp * (1 - props))


# --------------------------------------------------------------------------- #
# Tasas
# --------------------------------------------------------------------------- #
def poisson_rate_ci(count, exposure, per: float = 100_000, level: float = 0.95):
    """Tasa por `per` habitantes con IC exacto de Poisson (Garwood).

    Exacto y no aproximado porque muchos departamentos tienen 0, 1 o 2
    jugadores: ahí la aproximación normal da intervalos que incluyen negativos.
    """
    count = np.asarray(count, dtype=float)
    exposure = np.asarray(exposure, dtype=float)
    alpha = 1 - level
    with np.errstate(divide="ignore", invalid="ignore"):
        lo_c = np.where(count > 0, stats.chi2.ppf(alpha / 2, 2 * count) / 2, 0.0)
        hi_c = stats.chi2.ppf(1 - alpha / 2, 2 * count + 2) / 2
        scale = np.where(exposure > 0, per / exposure, np.nan)
        return count * scale, lo_c * scale, hi_c * scale


def rate_ratio_ci(k1, n1, k2, n2, level: float = 0.95):
    """Razón de tasas (grupo 1 vs grupo 2) con IC por el método delta en log.

    Devuelve (rr, lo, hi). Con conteos chicos el IC se ensancha, que es lo
    correcto: no hay que leer una diferencia donde no hay evidencia.
    """
    k1, n1, k2, n2 = map(float, (k1, n1, k2, n2))
    if min(n1, n2) <= 0:
        return np.nan, np.nan, np.nan
    if k1 == 0 or k2 == 0:
        # Corrección de continuidad para que el log exista.
        k1, k2 = k1 + 0.5, k2 + 0.5
    rr = (k1 / n1) / (k2 / n2)
    se = np.sqrt(1 / k1 + 1 / k2)
    z = stats.norm.ppf(1 - (1 - level) / 2)
    return rr, rr * np.exp(-z * se), rr * np.exp(z * se)


def odds_ratio_ci(a, b, c, d, level: float = 0.95):
    """OR con IC de Woolf y corrección Haldane-Anscombe si hay celdas en cero.

    Tabla 2×2:  a = expuestos casos, b = expuestos no casos,
                c = no expuestos casos, d = no expuestos no casos.
    """
    a, b, c, d = map(float, (a, b, c, d))
    if min(a, b, c, d) == 0:
        a, b, c, d = a + 0.5, b + 0.5, c + 0.5, d + 0.5
    or_ = (a * d) / (b * c)
    se = np.sqrt(1 / a + 1 / b + 1 / c + 1 / d)
    z = stats.norm.ppf(1 - (1 - level) / 2)
    return or_, or_ * np.exp(-z * se), or_ * np.exp(z * se)


# --------------------------------------------------------------------------- #
# Comparaciones múltiples
# --------------------------------------------------------------------------- #
def fdr_bh(pvalues, alpha: float = 0.05):
    """Benjamini-Hochberg. Devuelve (rechaza, p_ajustados).

    Obligatorio en los cruces exploratorios: con 6 regiones × 4 posiciones hay
    24 tests y algo va a dar «significativo» por puro azar.
    """
    p = np.asarray(pvalues, dtype=float)
    n = len(p)
    order = np.argsort(p)
    ranked = p[order]
    adj = ranked * n / np.arange(1, n + 1)
    adj = np.minimum.accumulate(adj[::-1])[::-1]
    adj = np.clip(adj, 0, 1)
    out = np.empty(n)
    out[order] = adj
    return out <= alpha, out


def add_rate_columns(df: pd.DataFrame, count_col: str, pop_col: str,
                     per: float = 100_000, level: float = 0.95,
                     prefix: str = "tasa") -> pd.DataFrame:
    """Agrega tasa e IC exacto de Poisson a una tabla ya agregada."""
    rate, lo, hi = poisson_rate_ci(df[count_col], df[pop_col], per=per, level=level)
    out = df.copy()
    out[prefix] = rate
    out[f"{prefix}_ic_lo"] = lo
    out[f"{prefix}_ic_hi"] = hi
    return out
