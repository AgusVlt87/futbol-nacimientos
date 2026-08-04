"""Tests de la extracción del club de debut desde el wikitext.

Son críticas porque de acá sale el 41,8 % de la cobertura de H3, y porque son
parsing de texto libre: fallan en silencio devolviendo `None` o el club
equivocado, sin que nada se rompa. Los casos de abajo son wikitext real,
recortado, de los artículos que se usaron para validar contra BDFA.
"""

from __future__ import annotations

import pytest

from src.analysis.validar_club_wiki import clave, coincide
from src.clean.build_club_debut import (
    campo,
    enlaces,
    extraer_anio,
    extraer_club,
    extraer_lugar,
    titulo_canonico,
)

# El caso que motivó todo: Wikidata daba «Pumas Morelos» y el club real es
# Instituto, que es lo que dice la ficha.
CAPRARI = """{{Ficha de deportista
|nombre              = Gastón Caprari
|lugar nacimiento    = [[Córdoba (Argentina)|Córdoba]], [[Argentina]]
|inicio              = 2004
|equipo_debut        = [[Instituto Atlético Central Córdoba|Instituto]]
|club                = [[Club Juventud Agrario (Corralito)]]
}}
'''Gastón Nicolás Caprari''' es un futbolista argentino.

== Trayectoria ==
Debutó en el conjunto cordobés a los 19 años.
"""

# Sin `equipo_debut`: hay que caer a la tabla de clubes.
SOLO_TABLA = """{{Ficha de deportista
|nombre = Un Jugador
|lugar nacimiento = [[Rosario]], [[Santa Fe]]
}}
== Clubes ==
{|align="center"
!width="190"|Club
|-align=center
|[[Club Atlético Rosario Central|Rosario Central]]
|{{ARG}}
|2005 - 2009
|-align=center
|[[Boca Juniors]]
|{{ARG}}
|2009 - 2012
|}
"""


class TestExtraccionDeCampos:
    def test_campo_devuelve_el_valor(self):
        assert campo(CAPRARI, "inicio") == "2004"

    def test_campo_ausente_devuelve_vacio(self):
        assert campo(CAPRARI, "peso") == ""

    def test_campo_no_se_come_el_siguiente(self):
        """El valor corta en el próximo `|`, no sigue hasta el fin de la ficha."""
        assert "equipo_debut" not in campo(CAPRARI, "inicio")

    def test_enlaces_separa_destino_de_texto_visible(self):
        assert enlaces("[[Instituto Atlético Central Córdoba|Instituto]]") == [
            ("Instituto Atlético Central Córdoba", "Instituto")]

    def test_enlace_sin_barra_usa_el_destino_como_texto(self):
        assert enlaces("[[Boca Juniors]]") == [("Boca Juniors", "Boca Juniors")]


class TestClubDeDebut:
    def test_prefiere_la_ficha(self):
        destino, visible, origen = extraer_club(CAPRARI)
        assert destino == "Instituto Atlético Central Córdoba"
        assert visible == "Instituto"
        assert origen == "ficha:equipo_debut"

    def test_cae_a_la_tabla_cuando_no_hay_ficha(self):
        destino, visible, origen = extraer_club(SOLO_TABLA)
        assert destino == "Club Atlético Rosario Central"
        assert origen == "tabla_clubes"

    def test_la_tabla_toma_la_primera_fila_no_la_ultima(self):
        """Si tomara la última daría Boca: el club donde terminó, no donde empezó."""
        _, visible, _ = extraer_club(SOLO_TABLA)
        assert visible == "Rosario Central"

    def test_sin_dato_no_inventa(self):
        destino, visible, origen = extraer_club("{{Ficha de deportista\n|nombre = X\n}}")
        assert (destino, visible, origen) == (None, None, "sin_dato")

    def test_ignora_enlaces_que_no_son_clubes(self):
        texto = ("== Clubes ==\n{|\n|[[Archivo:escudo.png]]\n"
                 "|[[Club Atlético Talleres|Talleres]]\n|}")
        destino, _, _ = extraer_club(texto)
        assert destino == "Club Atlético Talleres"


class TestAnioYLugar:
    def test_anio_de_debut(self):
        assert extraer_anio(CAPRARI) == 2004

    def test_anio_ausente_es_none(self):
        assert extraer_anio(SOLO_TABLA) is None

    def test_anio_rechaza_numeros_que_no_son_anios(self):
        assert extraer_anio("{{X\n|inicio = 12 partidos\n}}") is None

    def test_lugar_de_nacimiento(self):
        destino, visible = extraer_lugar(CAPRARI)
        assert destino == "Córdoba (Argentina)"
        assert visible == "Córdoba"


class TestTituloCanonico:
    @pytest.mark.parametrize("entrada,esperado", [
        ("club_atlético_boca", "Club atlético boca"),
        ("boca Juniors", "Boca Juniors"),
        ("  Rosario Central  ", "Rosario Central"),
    ])
    def test_normaliza(self, entrada, esperado):
        assert titulo_canonico(entrada) == esperado

    def test_no_rompe_con_vacio(self):
        assert titulo_canonico("") == ""


class TestComparacionDeNombres:
    """El comparador se testea aparte de lo que compara.

    Un desacuerdo puede ser un error del dato o un error del matcheo; si no se
    separan, la tasa de error medida mezcla las dos cosas y sale inflada.
    """

    @pytest.mark.parametrize("a,b", [
        ("Club Atlético Boca Juniors", "Boca Juniors"),
        ("Newell's Old Boys", "Newells Old Boys"),         # apóstrofo
        ("C. A. Colón", "Colón de Santa Fe"),              # iniciales sueltas
        ("Gimnasia y Esgrima (LP)", "Gimnasia y Esgrima de La Plata"),
        ("Rivadavia de Lincoln", "Rivadavia Lincoln"),     # conector «de»
    ])
    def test_mismo_club(self, a, b):
        assert coincide(a, b), f"{clave(a)} vs {clave(b)}"

    @pytest.mark.parametrize("a,b", [
        ("Boca Juniors", "River Plate"),
        ("Gimnasia y Esgrima de Jujuy", "Gimnasia y Esgrima de La Plata"),
        ("Racing de Olavarría", "El Fortín de Olavarría"),
        ("Independiente Rivadavia", "Jorge Newbery de Villa Mercedes"),
    ])
    def test_clubes_distintos(self, a, b):
        assert not coincide(a, b), f"{clave(a)} vs {clave(b)}"

    def test_nombre_vacio_no_coincide_con_nada(self):
        """Sin esto, un club sin nombre 'coincidiría' con todos por conjunto vacío."""
        assert not coincide("", "Boca Juniors")
        assert not coincide(None, "Boca Juniors")
