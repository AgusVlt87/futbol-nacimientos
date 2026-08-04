"""Un club es un QID, no una forma de escribirlo.

`primer_club` guarda el texto visible del enlace cuando el dato salió de una
ficha de Wikipedia, y ese texto es el que tipeó cada editor. Q18640 llega como
«Gimnasia (LP)», «Gimnasia La Plata», «Gimnasia y Esgrima de La Plata» y cuatro
variantes más. Mientras `run_futbol` agrupó por `(qid, nombre)` y `run_seleccion`
por `nombre` a secas, un club se partía en tantas filas como grafías tuviera:
Boca en cuatro, Newell's en siete, y el ranking del §3.3 salía con el orden
cambiado y la concentración hundida a la mitad.

Es la otra mitad de la trampa 16 del CLAUDE.md —resolver las redirecciones
arregló el QID y dejó el nombre crudo— y esto es lo que impide que vuelva.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.common import paths

P = paths()

requiere_salidas = pytest.mark.skipif(
    not (P.tables / "futbol_clubes_formadores.csv").exists(),
    reason="faltan las salidas: correr `python -m src.analysis.run_futbol`")


@requiere_salidas
def test_cada_club_aparece_una_sola_vez():
    d = pd.read_csv(P.tables / "futbol_clubes_formadores.csv")
    dup = d[d.duplicated("primer_club_qid", keep=False)]
    assert dup.empty, (
        "hay QIDs repartidos en varias filas, o sea el mismo club contado como "
        f"varios:\n{dup[['primer_club_qid', 'primer_club', 'formados']].to_string()}")


@requiere_salidas
def test_la_concentracion_usa_el_total_de_jugadores_no_de_filas():
    """El denominador de la concentración son jugadores, y las partes suman."""
    d = pd.read_csv(P.tables / "futbol_clubes_formadores.csv")
    c = pd.read_csv(P.tables / "futbol_concentracion_clubes.csv")
    assert int(d["formados"].sum()) == int(c["total_jugadores_con_club"].iloc[0])
    assert int(c["clubes_distintos"].iloc[0]) == d["primer_club_qid"].nunique()
    for _, r in c.iterrows():
        esperado = int(d["formados"].head(int(r["top_n"])).sum())
        assert int(r["formados"]) == esperado, f"top {r['top_n']} no cuadra"


@requiere_salidas
def test_los_clubes_de_seleccion_tambien_van_por_qid():
    ruta = P.tables / "seleccion_clubes_formadores.csv"
    if not ruta.exists():
        pytest.skip("falta seleccion_clubes_formadores.csv")
    d = pd.read_csv(ruta)
    assert "primer_club_qid" in d.columns, (
        "seleccion_clubes_formadores debe agrupar por QID, no por nombre")
    assert not d.duplicated("primer_club_qid").any()
