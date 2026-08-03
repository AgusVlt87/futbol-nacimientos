"""Padrón oficial de departamentos y estabilidad de la geografía en el tiempo.

**Por qué existe este módulo.** El pipeline tenía dos errores que compartían la
misma causa: códigos de departamento escritos a mano y nunca contrastados contra
el padrón.

1. La lista de los 24 partidos del Gran Buenos Aires en `config.yaml` estaba
   corrida un lugar a partir de Lomas de Zamora: doce de los veinticuatro códigos
   apuntaban a otro partido que el que decía su comentario. `06441` decía «Lomas
   de Zamora» y era La Plata. El AMBA del estudio excluía Quilmes, Merlo, San
   Miguel, Tres de Febrero y Vicente López, e incluía La Plata y Pilar.
2. Los códigos de departamento del INDEC **no son estables entre censos**. 44 de
   532 cambiaron entre 1991 y 2022, casi todos por las divisiones de partidos
   bonaerenses de 1994. Como los nacimientos se reparten con el censo más cercano
   al año de nacimiento y los jugadores se geocodifican contra la geografía 2022,
   los nacimientos de un partido dividido quedaban partidos entre dos códigos y
   el denominador se truncaba. Un millón de nacimientos —el 70 % del Gran Buenos
   Aires— desaparecía del denominador por ciudad.

Ninguno de los dos falló ruidosamente: los totales provinciales cuadraban en los
dos casos, porque el error estaba en el reparto interno.

**Qué hace este módulo.** Todo código de departamento que use el pipeline se
resuelve contra `c2022_codigos_departamentos.xlsx`, que es el padrón oficial que
`src.ingest.indec_census` ya descarga. Nada se escribe a mano: `config.yaml`
declara los partidos del AMBA **por nombre** y acá se resuelven a códigos. Si un
nombre no resuelve a exactamente un código, se levanta una excepción.

El crosswalk histórico vive en `data/reference/crosswalk_departamentos.csv`, con
el criterio con el que se estableció cada equivalencia anotado fila por fila.
"""

from __future__ import annotations

from functools import lru_cache

import pandas as pd

from src.clean.geo_units import CABA_DEPT_ID, CABA_PROV, normalize_name
from src.common import ROOT, get_logger

log = get_logger("clean.padron")

PADRON_XLSX = ROOT / "data" / "raw" / "indec" / "codigos" / "c2022_codigos_departamentos.xlsx"
CROSSWALK_CSV = ROOT / "data" / "reference" / "crosswalk_departamentos.csv"

# Departamentos sin ninguna localidad censal: territorios sin población asentada.
# No es un error que no aparezcan en `tamano_localidad`; se declaran para que la
# verificación de conservación no los confunda con filas perdidas por un merge.
SIN_LOCALIDAD_CENSAL = {
    "94021": "Islas del Atlántico Sur",
    "94028": "Antártida Argentina",
}

# Códigos de relleno que publica algún censo y que no son departamentos. Se
# descartan, pero solo después de verificar que no llevan población: si alguna
# vez traen gente, el descarte deja de ser inocuo y tiene que fallar.
CODIGOS_NULOS = {
    "94999": "código de resto sin asignar del Censo 2010 (población 0)",
}


# --------------------------------------------------------------------------- #
# Padrón 2022
# --------------------------------------------------------------------------- #
@lru_cache(maxsize=1)
def padron() -> pd.DataFrame:
    """Padrón oficial de departamentos del Censo 2022 (INDEC).

    Devuelve `dept_id` (5 dígitos), `dept_nombre`, `prov_id`, `prov_nombre`.
    """
    if not PADRON_XLSX.exists():
        raise FileNotFoundError(
            f"falta el padrón de departamentos del INDEC en {PADRON_XLSX}. "
            "Correr `python -m src.ingest.indec_census` antes que cualquier otra "
            "cosa: sin el padrón no se puede validar ningún código geográfico.")
    df = pd.read_excel(PADRON_XLSX)
    df.columns = ["prov_cod", "prov_nombre", "dept_cod", "dept_nombre"]
    df = df.dropna(subset=["dept_cod"]).copy()
    df["dept_id"] = df["dept_cod"].astype(int).astype(str).str.zfill(5)
    df["prov_id"] = df["dept_id"].str[:2]
    return df[["dept_id", "dept_nombre", "prov_id", "prov_nombre"]].reset_index(drop=True)


@lru_cache(maxsize=1)
def codigos_validos() -> frozenset[str]:
    """Códigos de departamento válidos en la geografía 2022, con CABA colapsada.

    CABA se analiza como una unidad y no como sus quince comunas (ver
    `geo_units.collapse_caba`), así que el conjunto trae `02000` en lugar de
    `02007`…`02105`.
    """
    ids = set(padron()["dept_id"])
    ids = {i for i in ids if not i.startswith(CABA_PROV)}
    return frozenset(ids | {CABA_DEPT_ID})


def resolver_nombres(nombres: list[str], prov_id: str) -> dict[str, str]:
    """Nombres de departamento -> códigos INDEC 2022, dentro de una provincia.

    Falla ruidosamente. Un nombre que no resuelve a **exactamente un** código es
    un error de configuración, no un dato faltante: devolver `NaN` en silencio es
    justamente como la lista del AMBA estuvo doce códigos mal sin que nada lo
    notara.
    """
    pad = padron()
    pad = pad[pad["prov_id"] == prov_id]
    indice: dict[str, list[str]] = {}
    for _, r in pad.iterrows():
        indice.setdefault(normalize_name(r["dept_nombre"]), []).append(r["dept_id"])

    out, problemas = {}, []
    for nombre in nombres:
        hits = indice.get(normalize_name(nombre), [])
        if len(hits) == 1:
            out[nombre] = hits[0]
        else:
            problemas.append(f"  {nombre!r}: {len(hits)} coincidencias {hits}")
    if problemas:
        raise ValueError(
            f"no se pudieron resolver contra el padrón del INDEC (provincia "
            f"{prov_id}) los siguientes departamentos:\n" + "\n".join(problemas) +
            f"\nPadrón: {PADRON_XLSX}")
    return out


@lru_cache(maxsize=1)
def _amba_cacheado(gba_nombres: tuple[str, ...], prov_gba: str) -> frozenset[str]:
    return frozenset(resolver_nombres(list(gba_nombres), prov_gba).values())


def codigos_amba(cfg: dict) -> frozenset[str]:
    """Códigos de los partidos del Gran Buenos Aires, resueltos por nombre.

    No incluye CABA: `region_of` la resuelve por código de provincia.
    """
    amba = cfg["geography"]["amba"]
    return _amba_cacheado(tuple(amba["gba_department_names"]), amba["gba_province_code"])


# --------------------------------------------------------------------------- #
# Crosswalk histórico
# --------------------------------------------------------------------------- #
@lru_cache(maxsize=1)
def crosswalk() -> pd.DataFrame:
    """Equivalencias entre códigos históricos (1991/2001/2010) y geografía 2022."""
    if not CROSSWALK_CSV.exists():
        raise FileNotFoundError(f"falta el crosswalk de departamentos en {CROSSWALK_CSV}")
    cw = pd.read_csv(CROSSWALK_CSV, dtype={"dept_id": str})
    cw["dept_id"] = cw["dept_id"].str.zfill(5)

    validos = codigos_validos()
    destino = cw[cw["rol"] == "2022"]
    malos = sorted(set(destino["dept_id"]) - validos)
    if malos:
        raise ValueError(
            f"el crosswalk apunta a códigos que no existen en el padrón 2022: {malos}")
    historicos = set(cw[cw["rol"] == "historico"]["dept_id"])
    solapan = historicos & validos
    if solapan:
        raise ValueError(
            f"códigos declarados como históricos que además existen en 2022: "
            f"{sorted(solapan)}. El crosswalk asume que un código histórico "
            f"desapareció; si sigue vigente, la equivalencia está mal.")
    return cw


def a_geografia_2022(hist: pd.DataFrame) -> pd.DataFrame:
    """Reexpresa la población histórica por departamento en geografía 2022.

    `hist` es `pop_dept_historica`: censo × dept_id × pob, con los códigos tal
    como los publicó cada censo.

    Para cada componente del crosswalk se suma la población de los códigos
    históricos y se reparte entre los códigos 2022 según su participación en el
    **primer censo en el que todos ellos existen por separado**. Ese reparto es
    un supuesto nuevo —que la proporción entre las partes en ese censo describe
    la proporción que tenían antes de dividirse— y hay que declararlo en las
    limitaciones: es la única forma de bajar de un partido que ya no existe a los
    partidos actuales sin datos de radio anteriores a la división.
    """
    cw = crosswalk()
    hist = hist.copy()
    hist["dept_id"] = hist["dept_id"].astype(str).str.zfill(5)

    nulos = hist[hist["dept_id"].isin(CODIGOS_NULOS)]
    if len(nulos):
        con_gente = nulos[nulos["pob"] > 0]
        if len(con_gente):
            raise ValueError(
                f"códigos declarados como nulos que sí traen población:\n"
                f"{con_gente.to_string(index=False)}\nRevisar CODIGOS_NULOS.")
        log.info("descartados %d código(s) de relleno sin población: %s",
                 len(nulos), ", ".join(sorted(set(nulos["dept_id"]))))
        hist = hist[~hist["dept_id"].isin(CODIGOS_NULOS)]

    pob = hist.set_index(["dept_id", "censo"])["pob"]

    partes = []
    consumidos: set[str] = set()
    for comp, g in cw.groupby("componente", sort=True):
        olds = list(g[g["rol"] == "historico"]["dept_id"])
        news = list(g[g["rol"] == "2022"]["dept_id"])

        censos_old = sorted({c for o in olds for (d, c) in pob.index if d == o})
        if not censos_old:
            continue
        # Un código histórico y sus sucesores no pueden coexistir en un censo: si
        # coexisten, la equivalencia está mal planteada.
        censos_new = {c for n in news for (d, c) in pob.index if d == n}
        if set(censos_old) & censos_new:
            raise ValueError(
                f"componente {comp}: los códigos históricos {olds} y los de 2022 "
                f"{news} aparecen en el mismo censo "
                f"{sorted(set(censos_old) & censos_new)}")

        # Pesos: primer censo donde TODOS los sucesores tienen población.
        ref = next((c for c in sorted(censos_new)
                    if all((n, c) in pob.index for n in news)), None)
        if ref is None:
            raise ValueError(f"componente {comp}: ningún censo tiene a todos "
                             f"los sucesores {news} a la vez")
        base = {n: float(pob[(n, ref)]) for n in news}
        total_base = sum(base.values())
        if total_base <= 0:
            raise ValueError(f"componente {comp}: población de referencia nula en {ref}")

        for censo in censos_old:
            pooled = sum(float(pob[(o, censo)]) for o in olds if (o, censo) in pob.index)
            for n in news:
                partes.append({"dept_id": n, "censo": censo,
                               "pob": pooled * base[n] / total_base})
        consumidos.update(olds)
        log.info("crosswalk %s: %s -> %s (pesos del censo %d)",
                 comp, "+".join(olds), "+".join(news), ref)

    resto = hist[~hist["dept_id"].isin(consumidos)]
    out = (pd.concat([resto[["dept_id", "censo", "pob"]], pd.DataFrame(partes)],
                     ignore_index=True)
             .groupby(["dept_id", "censo"], as_index=False)["pob"].sum())

    # Conservación: reexpresar la geografía no puede mover población entre
    # provincias ni cambiar el total de ningún censo.
    verificar_conservacion(
        hist.assign(prov_id=hist["dept_id"].str[:2]).groupby(["censo", "prov_id"])["pob"].sum(),
        out.assign(prov_id=out["dept_id"].str[:2]).groupby(["censo", "prov_id"])["pob"].sum(),
        contexto="crosswalk de departamentos (población por censo y provincia)")
    return out


def verificar_geografia_2022(dept_ids, contexto: str) -> None:
    """Falla si algún código no existe en la geografía 2022.

    Es el chequeo que faltaba: los códigos de partidos disueltos en 1994 pasaban
    por todo el pipeline sin que nada los mirara, y recién se caían al hacer un
    merge contra una tabla 2022 —en silencio, porque el merge era `how="left"`.
    """
    desconocidos = sorted(set(map(str, dept_ids)) - codigos_validos())
    if desconocidos:
        raise ValueError(
            f"{contexto}: {len(desconocidos)} código(s) de departamento no existen "
            f"en el padrón 2022 del INDEC: {desconocidos[:20]}"
            f"{' …' if len(desconocidos) > 20 else ''}. "
            "Si son códigos de un censo anterior, agregarlos a "
            f"{CROSSWALK_CSV.name}.")


def verificar_conservacion(antes, despues, contexto: str, tol: float = 1e-6) -> None:
    """Falla si una transformación perdió o inventó masa.

    `antes` y `despues` pueden ser escalares o Series. Si son Series **se
    comparan grupo por grupo**, no solo el total: los dos errores que motivaron
    este módulo conservaban el total y rompían el reparto interno, así que
    comparar totales no habría alcanzado para detectarlos.

    La tolerancia es **relativa** (1e-6 por defecto). El reparto usa flotantes,
    de modo que exigir igualdad exacta daría falsos positivos; cualquier
    diferencia real es de órdenes de magnitud mayor.

    Esta verificación sola habría detenido los 1.049.301 nacimientos que se
    perdían del denominador por ciudad el día que empezaron a perderse.
    """
    def _falla(a: float, b: float, donde: str) -> str:
        pct = f" ({abs(b - a) / abs(a):.4%})" if a else ""
        return f"{donde}: antes={a:,.2f} después={b:,.2f} diferencia={b - a:,.2f}{pct}"

    if isinstance(antes, pd.Series) and isinstance(despues, pd.Series):
        a, b = antes.align(despues, fill_value=0.0)
        rel = (b - a).abs() / a.abs().where(a.abs() > 0, 1.0)
        rotos = rel[(rel > tol) | ((a == 0) & (b != 0))]
        if len(rotos):
            det = "\n".join(f"    {k}: {_falla(float(a[k]), float(b[k]), 'grupo')}"
                            for k in list(rotos.index)[:15])
            raise ValueError(
                f"{contexto}: no se conserva la masa en {len(rotos)} de {len(a)} "
                f"grupos.\n{det}\n"
                "Casi siempre es un merge que descartó filas en silencio.")
        return

    a = float(antes.sum()) if hasattr(antes, "sum") else float(antes)
    b = float(despues.sum()) if hasattr(despues, "sum") else float(despues)
    if a == 0:
        if b != 0:
            raise ValueError(f"{contexto}: el total pasó de 0 a {b:,.2f}")
        return
    if abs(b - a) / abs(a) > tol:
        raise ValueError(f"{contexto}: no se conserva el total. "
                         f"{_falla(a, b, 'total')}. "
                         "Casi siempre es un merge que descartó filas en silencio.")
