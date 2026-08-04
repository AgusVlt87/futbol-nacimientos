"""Fase 12c — De los nombres escritos a mano al tramo de tamaño.

El eslabón que faltaba entre la planilla codificada y la corrección. Toma lo que
la persona escribió —«Monte Cristo», «Córdoba Capital», «San Salvador»— y lo
resuelve contra el padrón de localidades para saber en qué tramo de tamaño cae.

**Por qué no alcanza con comparar strings.** El nombre anotado y el `P19` cargado
pueden diferir sin que haya ningún error: «San Salvador» y «San Salvador de
Jujuy» son el mismo lugar. Y pueden coincidir en el nombre y diferir en el
tramo: hay cuatro Santa Rosa en el país. Lo que hay que comparar no son los
nombres sino **los tramos de tamaño a los que cada nombre resuelve**, que es lo
que el estudio usa.

**La cadena de matcheo**, de más estricta a más laxa, deteniéndose en la primera
que acierta:

    1. nombre normalizado exacto, dentro de la provincia declarada
    2. nombre sin espacios ni guiones  («Monte Cristo» = «Montecristo»)
    3. sin los adornos de cabecera     («Córdoba Capital» = «Córdoba»)
    4. prefijo: el anotado es el comienzo del padrón, o al revés
       («San Salvador» → «San Salvador de Jujuy»)

Cada caso queda con el nivel de matcheo que usó, para poder mirar aparte los que
se resolvieron con la regla más laxa. Lo que no matchea **no se descarta**: se
reporta como `sin_resolver`, porque un faltante silencioso es lo que arruina este
tipo de validación.

Salida: `outputs/validacion/validacion_resuelta.csv`

Uso:
    python -m src.analysis.resolver_validacion
"""

from __future__ import annotations

import re
import unicodedata

import numpy as np
import pandas as pd

from src.common import get_logger, load_config, paths

log = get_logger("analysis.resolver")

# Palabras que la gente agrega y el padrón no tiene. «Capital» es la más común:
# quien escribe «Córdoba Capital» se refiere a la ciudad de Córdoba.
ADORNOS = re.compile(
    r"\b(capital|ciudad( autonoma)?( de)?|localidad de|partido de|"
    r"gran|provincia de|dpto\.?|departamento de)\b")

# Nombres de provincia escritos a mano -> código INDEC. Se resuelve por
# normalización y prefijo, no por igualdad: la gente escribe «Ciudad Autónoma»,
# «CABA», «Bs As», «Tucuman».
ALIAS_PROVINCIA = {
    "caba": "02", "capital federal": "02", "ciudad autonoma": "02",
    "ciudad autonoma de buenos aires": "02", "ciudad de buenos aires": "02",
    "bs as": "06", "bsas": "06", "buenos aires": "06", "pcia de buenos aires": "06",
    "tierra del fuego": "94", "santiago del estero": "86",
}


# Equivalencias resueltas a mano, con el motivo de cada una. Son casos que el
# padrón no puede resolver solo, no atajos para ahorrarse el matcheo.
#
# El grueso son localidades del Gran Buenos Aires: el padrón lista el GBA a nivel
# de PARTIDO (Almirante Brown, La Matanza, Tres de Febrero) y no de barrio, así
# que Adrogué o Villa Luzuriaga no existen como entrada. Todas caen dentro del
# aglomerado Gran Buenos Aires, que es el tramo >500k.
#
# Cada línea es una decisión revisable: si alguna está mal, cambia un caso.
ALIAS_LOCALIDAD = {
    # (localidad normalizada, prov_id) -> localidad del padrón
    ("adrogue", "06"): "Almirante Brown",        # cabecera de Almirante Brown, GBA
    ("villa luzuriaga", "06"): "La Matanza",     # barrio de La Matanza, GBA
    ("rafael castillo", "06"): "La Matanza",     # barrio de La Matanza, GBA
    ("san martin", "06"): "General San Martín",  # partido del GBA
    ("saenz pena", "06"): "Tres de Febrero",     # localidad de Tres de Febrero, GBA
    ("roque saenz pena", "06"): "Tres de Febrero",   # ídem
    ("bouvril", "30"): "Bovril",                 # error de tipeo en la planilla
}
# Deliberadamente NO se resuelve «Alsina, Buenos Aires» (caso 57). El padrón solo
# trae «Villa Alsina» (partido de Colón) y «Laguna Alsina» (Guaminí), y ninguna
# está en Baradero, que es lo que dice el `P19`. Sin poder verificar cuál es, se
# deja sin resolver: inventar la equivalencia sería el mismo error silencioso que
# el resto del proyecto documenta.


def norm(s: object) -> str:
    """Minúsculas, sin acentos, sin puntuación, espacios colapsados."""
    if s is None or (isinstance(s, float) and np.isnan(s)):
        return ""
    t = unicodedata.normalize("NFD", str(s)).lower()
    t = "".join(c for c in t if unicodedata.category(c) not in {"Mn", "Cf", "Cc"})
    t = re.sub(r"[^\w\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def sin_adornos(s: str) -> str:
    return re.sub(r"\s+", " ", ADORNOS.sub(" ", s)).strip()


def compacto(s: str) -> str:
    return s.replace(" ", "")


def resolver_provincia(texto: str, provincias: dict[str, str]) -> str | None:
    """Nombre de provincia escrito a mano -> código INDEC."""
    n = norm(texto)
    if not n:
        return None
    if n in ALIAS_PROVINCIA:
        return ALIAS_PROVINCIA[n]
    if n in provincias:
        return provincias[n]
    # Prefijo en cualquiera de las dos direcciones: «Tierra del Fuego» contra el
    # nombre oficial larguísimo, o «Ciudad Autonoma» contra el completo.
    for nombre, cod in provincias.items():
        if nombre.startswith(n) or n.startswith(nombre):
            return cod
    for alias, cod in ALIAS_PROVINCIA.items():
        if n.startswith(alias) or alias.startswith(n):
            return cod
    return None


def resolver_localidad(nombre: str, prov: str | None,
                       padron: pd.DataFrame) -> tuple[str | None, str]:
    """Devuelve (ciudad_id, nivel_de_matcheo)."""
    n = norm(nombre)
    if not n:
        # Solo se anotó la provincia. Es una respuesta válida y parcial: alcanza
        # para saber la provincia pero no el tamaño de la ciudad, que es lo que
        # el estudio necesita. No entra a la matriz.
        return None, "solo_provincia"

    alias = ALIAS_LOCALIDAD.get((n, prov))
    if alias is not None:
        hit = padron[(padron["prov_id"] == prov) & (padron["n"] == norm(alias))]
        if len(hit):
            return hit.nlargest(1, "pob_ciudad")["ciudad_id"].iloc[0], "alias_manual"

    cand = padron if prov is None else padron[padron["prov_id"] == prov]
    if cand.empty:
        cand = padron

    for nivel, col, clave in (("exacto", "n", n),
                              ("compacto", "n_compacto", compacto(n)),
                              ("sin_adornos", "n_sin_adornos", sin_adornos(n))):
        hit = cand[cand[col] == clave]
        if len(hit):
            # Ante homónimos dentro de la provincia, gana el más poblado: es el
            # que alguien nombraría sin aclarar cuál.
            return hit.nlargest(1, "pob_ciudad")["ciudad_id"].iloc[0], nivel

    # Prefijo: «San Salvador» -> «San Salvador de Jujuy». Se exige que el lado
    # corto tenga al menos 5 caracteres para no matchear «San» con cualquier cosa.
    if len(n) >= 5:
        pref = cand[cand["n"].str.startswith(n) | cand["n"].map(lambda x: n.startswith(x) and len(x) >= 5)]
        if len(pref):
            return pref.nlargest(1, "pob_ciudad")["ciudad_id"].iloc[0], "prefijo"

    return None, "sin_resolver"


def main() -> None:
    cfg = load_config()
    p = paths()
    val = p.root / "outputs" / "validacion"

    cod = pd.read_csv(val / "validacion_p19_codificado.csv")
    clave = pd.read_csv(val / "muestra_p19_clave.csv")

    # --- padrón de ciudades, con su tramo --------------------------------------
    tam = pd.read_parquet(p.processed / "tamano_localidad.parquet")
    unica = pd.read_parquet(p.processed / "denom_ciudad_unica.parquet")
    tam["ciudad_id"] = np.where(tam["aglomerado_id"].notna(),
                                "AGLO_" + tam["aglomerado_id"].astype(str),
                                "LOC_" + tam["localidad_id"].astype(str))
    padron = tam[["localidad_nombre", "prov_id", "pob_ciudad", "ciudad_id"]].copy()
    padron["n"] = padron["localidad_nombre"].map(norm)
    padron["n_compacto"] = padron["n"].map(compacto)
    padron["n_sin_adornos"] = padron["n"].map(sin_adornos)

    provincias = {norm(v): k for k, v in
                  pd.read_parquet(p.processed / "analysis_players.parquet")
                  [["prov_id", "prov_nombre"]].drop_duplicates()
                  .set_index("prov_id")["prov_nombre"].items()}

    d = cod.merge(clave, on="caso", how="left")
    ref = cfg["city_size"]["schemes"][cfg["city_size"]["default_scheme"]]["reference_label"]

    filas = []
    for r in d.itertuples():
        if r.encontrado != 1:
            filas.append({"prov_resuelta": None, "ciudad_id_real": None,
                          "nivel_matcheo": "no_verificable"})
            continue
        prov = resolver_provincia(r.provincia_encontrada, provincias)
        cid, nivel = resolver_localidad(r.localidad_encontrada, prov, padron)
        filas.append({"prov_resuelta": prov, "ciudad_id_real": cid,
                      "nivel_matcheo": nivel})
    d = pd.concat([d.reset_index(drop=True), pd.DataFrame(filas)], axis=1)

    d = d.merge(unica[["ciudad_id", "tramo"]].rename(
        columns={"ciudad_id": "ciudad_id_real", "tramo": "tramo_real"}),
        on="ciudad_id_real", how="left")
    d["estrato_real"] = np.where(
        d["tramo_real"].isna(), None,
        np.where(d["tramo_real"].eq(ref), "metropoli", "resto"))

    d.to_csv(val / "validacion_resuelta.csv", index=False, encoding="utf-8")

    log.info("=== resolución de los %d casos codificados ===", len(d))
    log.info("\n%s", d["nivel_matcheo"].value_counts().to_string())
    ok = d["estrato_real"].notna()
    log.info("con tramo resuelto: %d de %d codificados con lugar (%d no verificables)",
             int(ok.sum()), int((d["encontrado"] == 1).sum()),
             int((d["encontrado"] != 1).sum()))
    sin = d[(d["encontrado"] == 1) & d["estrato_real"].isna()]
    if len(sin):
        log.warning("sin resolver (%d) — revisar a mano:", len(sin))
        for r in sin.head(15).itertuples():
            log.warning("   caso %-4s %-28s %s",
                        r.caso, str(r.localidad_encontrada)[:27],
                        str(r.provincia_encontrada)[:20])


if __name__ == "__main__":
    main()
