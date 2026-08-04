"""Fase 11 — Covariables: pobreza estructural y distancia a la infraestructura.

**Por qué existe.** El §4.1 del paper interpretaba el patrón geográfico diciendo
que el lugar de nacimiento «no mide la calidad del entorno formativo, mide la
distancia a la infraestructura formativa». Esa frase era una interpretación y no
un resultado, porque la distancia a la infraestructura formativa no era una
variable en ningún modelo. Este módulo la construye, junto con el otro confusor
obvio que el trabajo nunca controló: el nivel socioeconómico.

**Distancia al club formador más cercano.** El universo de clubes formadores no
se define a mano: son los clubes argentinos que aparecen como primer club de al
menos un futbolista de la muestra. Para cada ciudad se calcula la distancia
haversine al más cercano. Es una medida cruda —no distingue un club de Primera
con pensión de uno de Federal A, ni tiene en cuenta que la red cambió a lo largo
de las cohortes— y por eso se declara como proxy, no como medida de acceso.

Ojo con la circularidad: el universo de clubes sale de los mismos datos que el
numerador. Un club que nunca formó a nadie no entra, de modo que la variable mide
«distancia al club formador más cercano **que efectivamente formó a alguien**».
Se reporta también la variante con todos los clubes argentinos geolocalizados,
que no tiene ese problema y a cambio incluye clubes irrelevantes.

**Pobreza estructural.** El censo 2022 publica el NBI por hogar como variable
derivada (`HOGAR_NBI_TOT`), con sus cinco componentes. Se agrega a departamento:
porcentaje de hogares con al menos una necesidad básica insatisfecha.

Salidas en `data/processed/`:
    covariables_departamento.parquet
    covariables_ciudad.parquet

Uso:
    python -m src.clean.build_covariables
"""

from __future__ import annotations

import io
import zipfile

import numpy as np
import pandas as pd

from src.clean.geo_units import collapse_caba, haversine_km
from src.common import get_logger, load_config, paths

log = get_logger("clean.covariables")

VARIABLE_NBI = "HOGAR_NBI_TOT"
# Los CSV del censo vienen en UTF-8. Leerlos como latin-1 —que es lo que pide el
# resto del pipeline para otros recursos del INDEC— convierte «Sí» en «SÃ­», y
# como el filtro por categoría entonces no encuentra nada, el NBI salía 0,0 % en
# los 513 departamentos sin que nada fallara. Es la misma firma que los «guiones
# blandos» de los padrones: U+00AD apareciendo donde debería haber un acento.
ENCODING_CENSO = "utf-8"
# Se compara sin acentos para no depender de que el acento sobreviva el viaje.
CATEGORIA_CON_NBI = "si"


def nbi_por_departamento(p) -> pd.DataFrame:
    """Porcentaje de hogares con NBI por departamento, censo 2022."""
    filas = []
    for zip_path in sorted((p.raw / "indec" / "censo2022").glob("*.zip")):
        with zipfile.ZipFile(zip_path) as z:
            nombre = next(n for n in z.namelist() if n.endswith("-hogar.csv"))
            with z.open(nombre) as h:
                d = pd.read_csv(io.TextIOWrapper(h, encoding=ENCODING_CENSO),
                                usecols=["cod_prov", "cod_dep", "cod_variable",
                                         "categoria", "cantidad"])
        d = d[d["cod_variable"] == VARIABLE_NBI]
        if d.empty:
            log.warning("%s no trae %s", zip_path.name, VARIABLE_NBI)
            continue
        d["dept_id"] = (d["cod_prov"].astype(int).astype(str).str.zfill(2)
                        + d["cod_dep"].astype(int).astype(str).str.zfill(3))
        filas.append(d)

    todo = pd.concat(filas, ignore_index=True)
    todo["dept_id"] = todo["dept_id"].map(collapse_caba)
    todo["cat"] = (todo["categoria"].str.normalize("NFKD")
                                    .str.encode("ascii", "ignore").str.decode("ascii")
                                    .str.strip().str.lower())
    piv = todo.groupby(["dept_id", "cat"])["cantidad"].sum().unstack(fill_value=0)
    if CATEGORIA_CON_NBI not in piv.columns:
        raise ValueError(
            f"la categoría {CATEGORIA_CON_NBI!r} no está en {VARIABLE_NBI}; "
            f"presentes: {list(piv.columns)}. Revisar el encoding del censo.")
    con = piv[CATEGORIA_CON_NBI]
    total = piv.sum(axis=1)
    out = pd.DataFrame({
        "dept_id": piv.index,
        "hogares": total.values,
        "hogares_con_nbi": con.values,
        "pct_nbi": 100 * con.values / total.replace(0, np.nan).values,
    })
    return out.reset_index(drop=True)


def clubes_formadores(p) -> pd.DataFrame:
    """Clubes argentinos que formaron al menos un futbolista de la muestra."""
    lv = pd.read_parquet(p.processed / "player_level.parquet")
    clubs = pd.read_parquet(p.interim / "clubs_resolved.parquet")
    usados = set(lv["primer_club_qid"].dropna())
    c = clubs[clubs["team_qid"].isin(usados)
              & clubs["club_lat"].notna()
              & clubs["club_en_argentina"].fillna(False)]
    return c[["team_qid", "team_label", "club_lat", "club_lon"]].drop_duplicates()


def distancia_al_mas_cercano(lat, lon, clat, clon) -> np.ndarray:
    """Distancia de cada punto al más cercano de un conjunto de referencia."""
    out = np.full(len(lat), np.nan)
    for i, (la, lo) in enumerate(zip(lat, lon)):
        if pd.isna(la) or pd.isna(lo):
            continue
        out[i] = float(np.min(haversine_km(la, lo, clat, clon)))
    return out


def main() -> None:
    load_config()
    p = paths()

    # --- NBI -----------------------------------------------------------------
    nbi = nbi_por_departamento(p)
    log.info("NBI: %d departamentos | mediana %.1f%% | rango %.1f–%.1f%%",
             len(nbi), nbi["pct_nbi"].median(), nbi["pct_nbi"].min(), nbi["pct_nbi"].max())

    # --- distancia -----------------------------------------------------------
    clubes = clubes_formadores(p)
    todos = pd.read_parquet(p.interim / "clubs_resolved.parquet")
    todos = todos[todos["club_lat"].notna() & todos["club_en_argentina"].fillna(False)]
    log.info("clubes formadores geolocalizados: %d (de %d argentinos con coordenada)",
             len(clubes), len(todos))

    # Coordenada de cada ciudad: la de su localidad más poblada, que es la que
    # define el aglomerado. El crosswalk es el único lugar con lat/lon censal.
    cw = pd.read_parquet(p.interim / "crosswalk_localidades.parquet")
    tam = pd.read_parquet(p.processed / "tamano_localidad.parquet")
    loc = (tam.merge(cw[["localidad_id", "lat", "lon"]].dropna(subset=["localidad_id"])
                       .drop_duplicates("localidad_id"),
                     on="localidad_id", how="left"))
    loc["ciudad_id"] = np.where(loc["aglomerado_id"].notna(),
                                "AGLO_" + loc["aglomerado_id"].astype(str),
                                "LOC_" + loc["localidad_id"].astype(str))
    ciudad = (loc.sort_values("pob_localidad", ascending=False)
                 .drop_duplicates("ciudad_id")
                 [["ciudad_id", "dept_id", "prov_id", "pob_ciudad", "lat", "lon"]])

    ciudad["km_club_formador"] = distancia_al_mas_cercano(
        ciudad["lat"].values, ciudad["lon"].values,
        clubes["club_lat"].values, clubes["club_lon"].values)
    ciudad["km_club_cualquiera"] = distancia_al_mas_cercano(
        ciudad["lat"].values, ciudad["lon"].values,
        todos["club_lat"].values, todos["club_lon"].values)
    ciudad = ciudad.merge(nbi[["dept_id", "pct_nbi"]], on="dept_id", how="left")

    # --- departamento --------------------------------------------------------
    dep = pd.read_parquet(p.processed / "denom_cohorte_departamento.parquet")
    centro = (ciudad.dropna(subset=["lat"])
                    .sort_values("pob_ciudad", ascending=False)
                    .drop_duplicates("dept_id")[["dept_id", "lat", "lon"]])
    dep = dep.merge(centro, on="dept_id", how="left")
    dep["km_club_formador"] = distancia_al_mas_cercano(
        dep["lat"].values, dep["lon"].values,
        clubes["club_lat"].values, clubes["club_lon"].values)
    dep = dep.merge(nbi[["dept_id", "pct_nbi", "hogares"]], on="dept_id", how="left")

    ciudad.to_parquet(p.processed / "covariables_ciudad.parquet", index=False)
    dep.to_parquet(p.processed / "covariables_departamento.parquet", index=False)

    log.info("ciudades con distancia: %d de %d | mediana %.0f km",
             int(ciudad["km_club_formador"].notna().sum()), len(ciudad),
             ciudad["km_club_formador"].median())
    log.info("departamentos con NBI: %d de %d",
             int(dep["pct_nbi"].notna().sum()), len(dep))


if __name__ == "__main__":
    main()
