"""Fase 3 — Construcción de los denominadores poblacionales.

El Censo 2022 se publica **tabulado por radio censal**: para cada radio, el
conteo de cada categoría de cada variable. No es microdato, así que hay
marginales pero no cruces (se puede tener población por edad y población por
sexo, no población por edad × sexo). Eso condiciona qué baselines son posibles
y está documentado en cada salida.

El radio es el átomo. A partir de él se arma todo:

    radio ──> departamento          (H2)
          ──> localidad censal      (H1, tamaño de ciudad)
          ──> aglomerado urbano     (H1, definición alternativa de "ciudad")
          ──> urbano / rural

Salidas en `data/processed/`:
    radio_geo.parquet          radio -> depto, localidad, aglomerado, urbano/rural
    pop_dept_edad.parquet      población por departamento y edad simple (2022)
    pop_localidad_edad.parquet ídem por localidad censal
    pop_aglomerado_edad.parquet ídem por aglomerado
    pop_dept_nacprov.parquet   residentes por depto según provincia de nacimiento
    pop_dept_historica.parquet población total por depto en 1991/2001/2010/2022
    tamano_localidad.parquet   tamaño de cada localidad y aglomerado (2022)

Uso:
    python -m src.clean.build_population [--force]
"""

from __future__ import annotations

import argparse
import io
import zipfile
from pathlib import Path

import pandas as pd

from src.clean.geo_units import CABA_DEPT_ID, collapse_caba
from src.common import get_logger, load_config, paths

log = get_logger("clean.poblacion")

CENSO_YEAR = 2022

VARS_PERSONA = {"PERSONA_EDAD", "PERSONA_P02", "PERSONA_P14"}
VARS_VIVIENDA = {"VIVIENDA_CODLOC", "VIVIENDA_CODAGLO", "VIVIENDA_URP"}

# Todas las comunas de CABA comparten una única localidad censal: la ciudad.
# El censo les da un CODLOC por comuna, pero el nombre es siempre el mismo.
CABA_LOCALIDAD_ID = "02000010"
CABA_LOCALIDAD_NOMBRE = "Ciudad Autónoma de Buenos Aires"

# Columna con la población total por radio en cada archivo de radios censales.
POB_COL = {1991: "B_POB_TOT", 2001: "POB_TOT", 2010: "B_POB_TOT", 2022: "POB_TOT_P"}


def _read_zip_member(zf: zipfile.ZipFile, suffix: str, keep_vars: set[str]) -> pd.DataFrame:
    name = next(n for n in zf.namelist() if n.endswith(suffix))
    chunks = []
    with zf.open(name) as fh:
        text = io.TextIOWrapper(fh, encoding="utf-8-sig")
        for chunk in pd.read_csv(text, chunksize=500_000,
                                 dtype={"cod_variable": "string", "categoria": "string"}):
            chunks.append(chunk[chunk["cod_variable"].isin(keep_vars)])
    return pd.concat(chunks, ignore_index=True)


def _radio_code(df: pd.DataFrame) -> pd.Series:
    """Código de radio de 9 dígitos: 2 provincia + 3 departamento + 2 fracción + 2 radio."""
    return (df["cod_prov"].astype(int).astype(str).str.zfill(2)
            + df["cod_dep"].astype(int).astype(str).str.zfill(3)
            + df["fraccion"].astype(int).astype(str).str.zfill(2)
            + df["radio"].astype(int).astype(str).str.zfill(2))


def _dominant(df: pd.DataFrame, var: str, id_len: int | None = None) -> pd.DataFrame:
    """Categoría dominante por radio para una variable de vivienda.

    Un radio puede tener viviendas en más de una localidad; se toma la de mayor
    peso y se guarda la proporción para poder auditar cuán limpio fue el corte.
    """
    s = df[df["cod_variable"] == var]
    if s.empty:
        return pd.DataFrame(columns=["codigo", var, f"{var}_nombre", f"{var}_share"])
    tot = s.groupby("codigo")["cantidad"].transform("sum")
    best = s.assign(share=s["cantidad"] / tot).sort_values("share", ascending=False) \
            .drop_duplicates("codigo")
    code = best["cod_categoria"].astype("Int64").astype(str)
    if id_len:
        code = code.str.zfill(id_len)
    return pd.DataFrame({"codigo": best["codigo"].values,
                         var: code.values,
                         f"{var}_nombre": best["categoria"].values,
                         f"{var}_share": best["share"].values})


def build_from_census(raw_dir: Path) -> tuple[pd.DataFrame, ...]:
    geo_parts, edad_parts, sexo_parts, nac_parts = [], [], [], []

    for zpath in sorted(raw_dir.glob("*.zip")):
        with zipfile.ZipFile(zpath) as zf:
            per = _read_zip_member(zf, "-persona.csv", VARS_PERSONA)
            viv = _read_zip_member(zf, "-vivienda.csv", VARS_VIVIENDA)
        per["codigo"] = _radio_code(per)
        viv["codigo"] = _radio_code(viv)

        geo = (viv[["codigo", "cod_prov", "cod_dep"]].drop_duplicates("codigo")
               .merge(_dominant(viv, "VIVIENDA_CODLOC", 8), on="codigo", how="left")
               .merge(_dominant(viv, "VIVIENDA_CODAGLO"), on="codigo", how="left")
               .merge(_dominant(viv, "VIVIENDA_URP"), on="codigo", how="left"))
        geo_parts.append(geo)

        e = per[per["cod_variable"] == "PERSONA_EDAD"]
        edad_parts.append(pd.DataFrame({"codigo": e["codigo"].values,
                                        "edad": e["cod_categoria"].astype(int).values,
                                        "n": e["cantidad"].astype(int).values}))
        s = per[per["cod_variable"] == "PERSONA_P02"]
        sexo_parts.append(pd.DataFrame({"codigo": s["codigo"].values,
                                        "sexo": s["categoria"].values,
                                        "n": s["cantidad"].astype(int).values}))
        b = per[per["cod_variable"] == "PERSONA_P14"]
        nac_parts.append(pd.DataFrame({"codigo": b["codigo"].values,
                                       "prov_nac_id": b["cod_categoria"].astype(int)
                                                        .astype(str).str.zfill(2).values,
                                       "prov_nac_nombre": b["categoria"].values,
                                       "n": b["cantidad"].astype(int).values}))
        log.info("%s: %d radios", zpath.name, geo["codigo"].nunique())

    return (pd.concat(geo_parts, ignore_index=True),
            pd.concat(edad_parts, ignore_index=True),
            pd.concat(sexo_parts, ignore_index=True),
            pd.concat(nac_parts, ignore_index=True))


def tidy_geo(geo: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame({
        "codigo": geo["codigo"],
        "prov_id": geo["codigo"].str[:2],
        "dept_id_raw": geo["codigo"].str[:5],
        "localidad_id": geo["VIVIENDA_CODLOC"],
        "localidad_nombre": geo["VIVIENDA_CODLOC_nombre"],
        "localidad_share": geo["VIVIENDA_CODLOC_share"],
        "aglomerado_id": geo["VIVIENDA_CODAGLO"],
        "aglomerado_nombre": geo["VIVIENDA_CODAGLO_nombre"],
        "urp": geo["VIVIENDA_URP_nombre"],
    })
    out["dept_id"] = out["dept_id_raw"].map(collapse_caba)
    # CABA: una sola localidad, no una por comuna.
    caba = out["prov_id"] == "02"
    out.loc[caba, "localidad_id"] = CABA_LOCALIDAD_ID
    out.loc[caba, "localidad_nombre"] = CABA_LOCALIDAD_NOMBRE
    return out


def build_historical(radios_dir: Path) -> pd.DataFrame:
    """Población total por departamento en cada censo con radios publicados."""
    frames = []
    for year, col in POB_COL.items():
        d = pd.read_csv(radios_dir / f"radios-{year}.csv.gz",
                        dtype={"cod_prov": str, "cod_dep": str})
        d["dept_id_raw"] = d["cod_prov"].str.zfill(2) + d["cod_dep"].str.zfill(3)
        d["dept_id"] = d["dept_id_raw"].map(collapse_caba)
        g = (d.assign(pob=pd.to_numeric(d[col], errors="coerce"))
               .groupby("dept_id", as_index=False)["pob"].sum())
        g["censo"] = year
        frames.append(g)
    return pd.concat(frames, ignore_index=True)


def main() -> None:
    ap = argparse.ArgumentParser(description="Construye los denominadores poblacionales")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    load_config()
    p = paths()
    dest = p.processed
    if (dest / "pop_dept_edad.parquet").exists() and not args.force:
        log.info("ya existen los denominadores (usar --force)")
        return

    geo_raw, edad, sexo, nac = build_from_census(p.raw / "indec" / "censo2022")
    geo = tidy_geo(geo_raw)
    geo.to_parquet(dest / "radio_geo.parquet", index=False)

    edad = edad.merge(geo[["codigo", "dept_id", "localidad_id", "aglomerado_id"]],
                      on="codigo", how="left")

    (edad.groupby(["dept_id", "edad"], as_index=False)["n"].sum()
         .to_parquet(dest / "pop_dept_edad.parquet", index=False))
    (edad.dropna(subset=["localidad_id"])
         .groupby(["localidad_id", "edad"], as_index=False)["n"].sum()
         .to_parquet(dest / "pop_localidad_edad.parquet", index=False))
    (edad.dropna(subset=["aglomerado_id"])
         .groupby(["aglomerado_id", "edad"], as_index=False)["n"].sum()
         .to_parquet(dest / "pop_aglomerado_edad.parquet", index=False))

    (sexo.merge(geo[["codigo", "dept_id"]], on="codigo", how="left")
         .groupby(["dept_id", "sexo"], as_index=False)["n"].sum()
         .to_parquet(dest / "pop_dept_sexo.parquet", index=False))

    (nac.merge(geo[["codigo", "dept_id"]], on="codigo", how="left")
        .groupby(["dept_id", "prov_nac_id", "prov_nac_nombre"], as_index=False)["n"].sum()
        .to_parquet(dest / "pop_dept_nacprov.parquet", index=False))

    build_historical(p.raw / "indec" / "radios").to_parquet(
        dest / "pop_dept_historica.parquet", index=False)

    # Tamaño de cada localidad y de cada aglomerado (población total 2022).
    tot = edad.groupby("codigo", as_index=False)["n"].sum().merge(geo, on="codigo", how="left")
    loc_size = (tot.dropna(subset=["localidad_id"])
                   .groupby(["localidad_id", "localidad_nombre", "dept_id", "prov_id"],
                            as_index=False)["n"].sum()
                   .rename(columns={"n": "pob_localidad"}))
    aglo_size = (tot.dropna(subset=["aglomerado_id"])
                    .groupby(["aglomerado_id", "aglomerado_nombre"], as_index=False)["n"].sum()
                    .rename(columns={"n": "pob_aglomerado"}))
    loc_aglo = (tot.dropna(subset=["localidad_id"])
                   .groupby(["localidad_id", "aglomerado_id"], as_index=False)["n"].sum()
                   .sort_values("n", ascending=False).drop_duplicates("localidad_id")
                   [["localidad_id", "aglomerado_id"]])
    tamano = loc_size.merge(loc_aglo, on="localidad_id", how="left") \
                     .merge(aglo_size, on="aglomerado_id", how="left")
    # "Tamaño de ciudad" = el aglomerado si la localidad forma parte de uno.
    # Lanús no es una ciudad de 200.000: es un pedazo de un conurbano de 15
    # millones, y para el birthplace effect eso es lo que importa.
    tamano["pob_ciudad"] = tamano["pob_aglomerado"].fillna(tamano["pob_localidad"])
    tamano.to_parquet(dest / "tamano_localidad.parquet", index=False)

    log.info("radios %d | deptos %d | localidades %d | aglomerados %d",
             len(geo), geo["dept_id"].nunique(), tamano["localidad_id"].nunique(),
             tamano["aglomerado_id"].nunique())
    log.info("población total 2022: %s", f"{edad['n'].sum():,}")
    log.info("listo -> %s", dest)


if __name__ == "__main__":
    main()
