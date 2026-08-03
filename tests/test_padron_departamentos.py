"""Tests del padrón de departamentos y del crosswalk histórico.

Estos tests existen por dos errores concretos que el repo tuvo y que ningún test
detectaba:

1. La lista de los 24 partidos del GBA en `config.yaml` estaba corrida un lugar:
   doce códigos apuntaban a otro partido. El único test que había
   (`test_region_amba_gana_sobre_provincia`) verificaba **un** partido, La
   Matanza, que era de los doce que estaban bien. Por eso pasaba.
2. Los códigos de departamento cambian entre censos y nada lo verificaba.

La lección de los dos es la misma: verificar un caso no verifica una lista. Acá
se verifican los 24 y las 44 equivalencias completas.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.clean.geo_units import region_of
from src.clean.padron_departamentos import (
    PADRON_XLSX,
    a_geografia_2022,
    codigos_amba,
    codigos_validos,
    crosswalk,
    padron,
    resolver_nombres,
    verificar_conservacion,
    verificar_geografia_2022,
)
from src.common import load_config, paths

CFG = load_config()

# El padrón vive en `data/raw/`, que no se versiona. En un clon limpio hay que
# correr la ingesta antes; el pipeline falla ruidosamente si no está, pero un
# test no debería fallar por eso.
requiere_padron = pytest.mark.skipif(
    not PADRON_XLSX.exists(),
    reason="falta el padrón del INDEC: correr `python -m src.ingest.indec_census`")


# --------------------------------------------------------------------------- #
# Resolución de nombres
# --------------------------------------------------------------------------- #
@requiere_padron
def test_los_24_partidos_del_gba_resuelven():
    codigos = codigos_amba(CFG)
    assert len(codigos) == 24, "el GBA tiene 24 partidos"
    assert len(set(codigos)) == 24, "hay códigos repetidos"
    assert all(c.startswith("06") for c in codigos), "todos son de Buenos Aires"


@requiere_padron
def test_cada_partido_del_gba_resuelve_al_nombre_que_dice():
    """El test que faltaba: nombre por nombre contra el padrón, no uno solo."""
    nombres = CFG["geography"]["amba"]["gba_department_names"]
    resueltos = resolver_nombres(nombres, "06")
    pad = padron().set_index("dept_id")["dept_nombre"].to_dict()
    for nombre, codigo in resueltos.items():
        assert pad[codigo] == nombre, (
            f"{nombre!r} resolvió a {codigo}, que en el padrón es {pad[codigo]!r}")


@requiere_padron
def test_partidos_que_el_bug_dejaba_afuera_ahora_estan():
    """Quilmes, Merlo, San Miguel, Tres de Febrero y Vicente López.

    Los cinco quedaban fuera del AMBA con la lista de códigos vieja. Ojo: hay que
    resolver dentro de Buenos Aires, porque «Merlo» también es un departamento de
    San Luis — homónimo entre provincias, la trampa que documenta `CLAUDE.md`.
    """
    codigos = codigos_amba(CFG)
    for nombre in ["Quilmes", "Merlo", "San Miguel", "Tres de Febrero", "Vicente López"]:
        codigo = resolver_nombres([nombre], "06")[nombre]
        assert codigo in codigos, f"{nombre} tiene que ser AMBA"
        assert region_of(codigo, CFG) == "AMBA"


@requiere_padron
def test_partidos_que_el_bug_metia_de_mas_ahora_no_estan():
    """La Plata, Marcos Paz, Pilar y Presidente Perón no son del GBA-24."""
    codigos = codigos_amba(CFG)
    for nombre in ["La Plata", "Marcos Paz", "Pilar", "Presidente Perón"]:
        codigo = resolver_nombres([nombre], "06")[nombre]
        assert codigo not in codigos, f"{nombre} no es del GBA-24"
        assert region_of(codigo, CFG) == "Pampeana"


@requiere_padron
def test_nombre_inexistente_falla_ruidosamente():
    with pytest.raises(ValueError, match="no se pudieron resolver"):
        resolver_nombres(["Partido Que No Existe"], "06")


@requiere_padron
def test_resolucion_ignora_tildes_y_mayusculas():
    assert (resolver_nombres(["ITUZAINGO"], "06")["ITUZAINGO"]
            == resolver_nombres(["Ituzaingó"], "06")["Ituzaingó"])


# --------------------------------------------------------------------------- #
# Crosswalk histórico
# --------------------------------------------------------------------------- #
@requiere_padron
def test_crosswalk_apunta_a_codigos_vigentes():
    cw = crosswalk()
    destino = set(cw[cw["rol"] == "2022"]["dept_id"])
    assert destino <= codigos_validos()


@requiere_padron
def test_crosswalk_no_reusa_codigos_vigentes_como_historicos():
    cw = crosswalk()
    historicos = set(cw[cw["rol"] == "historico"]["dept_id"])
    assert not (historicos & codigos_validos())


@requiere_padron
def test_cada_componente_tiene_las_dos_puntas():
    cw = crosswalk()
    for comp, g in cw.groupby("componente"):
        roles = set(g["rol"])
        assert roles == {"historico", "2022"}, f"{comp}: roles {roles}"


@requiere_padron
def test_todo_codigo_historico_queda_en_geografia_2022():
    """El chequeo que faltaba: ningún código de censo viejo sobrevive al remapeo."""
    p = paths()
    hist = pd.read_parquet(p.processed / "pop_dept_historica.parquet")
    verificar_geografia_2022(a_geografia_2022(hist)["dept_id"],
                             "población histórica remapeada")


@requiere_padron
def test_el_remapeo_conserva_la_poblacion_de_cada_provincia_y_censo():
    p = paths()
    hist = pd.read_parquet(p.processed / "pop_dept_historica.parquet")
    out = a_geografia_2022(hist)
    for df in (hist, out):
        df["prov_id"] = df["dept_id"].astype(str).str[:2]
    # 94999 es un código de relleno con población 0 que el remapeo descarta.
    antes = hist[hist["dept_id"] != "94999"].groupby(["censo", "prov_id"])["pob"].sum()
    verificar_conservacion(antes, out.groupby(["censo", "prov_id"])["pob"].sum(),
                           contexto="remapeo a geografía 2022")


# --------------------------------------------------------------------------- #
# verificar_conservacion
# --------------------------------------------------------------------------- #
def test_conservacion_detecta_perdida_de_masa():
    with pytest.raises(ValueError, match="no se conserva"):
        verificar_conservacion(1_000_000.0, 950_000.0, contexto="prueba")


def test_conservacion_tolera_ruido_de_punto_flotante():
    verificar_conservacion(1_000_000.0, 1_000_000.0000001, contexto="prueba")


def test_conservacion_compara_grupo_por_grupo_no_solo_el_total():
    """El caso exacto de los dos bugs: el total cuadra y el reparto no."""
    antes = pd.Series({"a": 100.0, "b": 100.0})
    despues = pd.Series({"a": 150.0, "b": 50.0})
    assert antes.sum() == despues.sum()
    with pytest.raises(ValueError, match="no se conserva la masa"):
        verificar_conservacion(antes, despues, contexto="prueba")


def test_conservacion_detecta_grupo_que_aparece_de_la_nada():
    with pytest.raises(ValueError, match="no se conserva la masa"):
        verificar_conservacion(pd.Series({"a": 100.0, "b": 0.0}),
                               pd.Series({"a": 100.0, "b": 5.0}), contexto="prueba")
