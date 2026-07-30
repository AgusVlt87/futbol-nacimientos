"""Lectura de capas vectoriales sin GDAL.

Por qué: en esta máquina el Application Control de Windows bloquea la DLL de
GDAL que trae `pyogrio`, así que `geopandas.read_file` no funciona. `shapely`,
`pyproj` y el resto de `geopandas` sí andan — el problema es solo la I/O.

La solución es leer los shapefiles con `pyshp` (Python puro) y construir el
GeoDataFrame a mano. No cambia ningún resultado: es el mismo archivo, leído por
otra vía.
"""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

import geopandas as gpd
import pandas as pd
import shapefile  # pyshp
from shapely.geometry import shape

# Los shapefiles del IGN vienen en WGS84 (ver el .prj de cada capa).
DEFAULT_CRS = "EPSG:4326"


def read_shapefile_zip(path: Path | str, encoding: str = "utf-8",
                       crs: str = DEFAULT_CRS) -> gpd.GeoDataFrame:
    """Lee un .zip con un shapefile adentro y devuelve un GeoDataFrame."""
    path = Path(path)
    with zipfile.ZipFile(path) as z:
        parts = {}
        for name in z.namelist():
            ext = name.rsplit(".", 1)[-1].lower()
            if ext in {"shp", "dbf", "shx"}:
                parts[ext] = io.BytesIO(z.read(name))
        missing = {"shp", "dbf", "shx"} - parts.keys()
        if missing:
            raise ValueError(f"{path.name}: faltan componentes {sorted(missing)}")

        reader = shapefile.Reader(shp=parts["shp"], dbf=parts["dbf"], shx=parts["shx"],
                                  encoding=encoding, encodingErrors="replace")
        fields = [f[0] for f in reader.fields[1:]]
        records = [dict(zip(fields, rec)) for rec in reader.records()]
        geoms = [shape(s.__geo_interface__) for s in reader.shapes()]

    return gpd.GeoDataFrame(pd.DataFrame(records), geometry=geoms, crs=crs)


def read_geojson(path: Path | str, crs: str = DEFAULT_CRS) -> gpd.GeoDataFrame:
    """Lee un GeoJSON sin pasar por GDAL."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    feats = data["features"]
    return gpd.GeoDataFrame(
        pd.DataFrame([f.get("properties", {}) for f in feats]),
        geometry=[shape(f["geometry"]) for f in feats],
        crs=crs,
    )


def write_geojson(gdf: gpd.GeoDataFrame, path: Path | str) -> None:
    """Escribe un GeoJSON sin pasar por GDAL."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    geo = gdf.to_crs(DEFAULT_CRS) if gdf.crs and gdf.crs.to_string() != DEFAULT_CRS else gdf
    features = []
    for _, row in geo.iterrows():
        props = {k: (None if pd.isna(v) else v)
                 for k, v in row.drop(labels=geo.geometry.name).items()}
        features.append({"type": "Feature", "properties": props,
                         "geometry": row[geo.geometry.name].__geo_interface__})
    path.write_text(json.dumps({"type": "FeatureCollection", "features": features},
                               ensure_ascii=False, default=str),
                    encoding="utf-8")
