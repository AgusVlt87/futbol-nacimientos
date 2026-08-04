"""El paper no puede tener números propios.

Las tablas de `reports/paper.md` se generan desde `outputs/tables/`. Este test es
lo que hace cumplir la regla: si alguien edita una tabla a mano, o si el pipeline
se re-corre y el paper no, falla acá y no seis meses después.

Es el modo de falla que tuvo el §3.2: cinco de sus seis filas dejaron de coincidir
con `h2_regiones.csv` al arreglarse un bug río arriba, y nada lo notó.
"""

from __future__ import annotations

import pytest

from src.common import paths
from src.report.sync_tablas_paper import auditar_prosa, sincronizar

P = paths()

requiere_salidas = pytest.mark.skipif(
    not (P.tables / "h1_tramos_principal.csv").exists(),
    reason="faltan las salidas del pipeline: correr `python -m src.analysis.run_all`")


@requiere_salidas
@pytest.mark.parametrize("ruta, formato", [
    (P.reports / "paper.md", "md"),
    (P.root / "paper" / "paper.tex", "tex"),
])
def test_las_tablas_del_paper_coinciden_con_las_salidas(ruta, formato):
    """Vale para las dos versiones del paper.

    El `.tex` quedó cuatro lotes atrasado respecto del `.md` justamente porque
    tenía números propios y nada los comparaba con nada.
    """
    if not ruta.exists():
        pytest.skip(f"no existe {ruta.name}")
    original = ruta.read_text(encoding="utf-8")
    nuevo, vistos = sincronizar(original, P, formato)
    assert vistos, f"{ruta.name} no tiene ninguna marca de tabla"
    assert nuevo == original, (
        f"las tablas de {ruta.name} están desfasadas respecto de outputs/tables/. "
        "Correr `python -m src.report.sync_tablas_paper`.")


@requiere_salidas
@pytest.mark.parametrize("ruta", [
    P.reports / "paper.md",
    P.root / "paper" / "paper.tex",
    P.root / "README.md",
])
def test_las_cifras_de_la_prosa_coinciden_con_las_salidas(ruta):
    """Las tablas al día no alcanzan: la prosa se desfasa por su cuenta.

    Con las diez tablas sincronizadas y este chequeo solo en el CLI, diecisiete
    cifras del texto corrido quedaron viejas —el χ² de H2, la muestra
    departamental, el AIC, el n de juveniles, la retención del NEA— y la suite
    daba verde igual. `--check` ya las miraba; lo que faltaba era que las mirara
    también el test.
    """
    if not ruta.exists():
        pytest.skip(f"no existe {ruta.name}")
    problemas = auditar_prosa(ruta.read_text(encoding="utf-8"), P)
    assert not problemas, f"cifras desfasadas en {ruta.name}:\n" + "\n".join(problemas)
