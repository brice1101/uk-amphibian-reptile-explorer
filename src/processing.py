import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

def occurrences_to_gdf(df, lon_cols=("decimalLongitude","lon","lng"),
                       lat_cols=("decimalLatitude","lat")):

    lon = None; lat = None
    for c in lon_cols:
        if c in df.columns:
            lon = c; break
    for c in lat_cols:
        if c in df.columns:
            lat = c; break
    if lon is None or lat is None:
        raise ValueError("No lon/lat columns found in DataFrame")
    df = df.dropna(subset=[lon, lat])
    gdf = gpd.GeoDataFrame(df.copy(),
                           geometry=[Point(xy) for xy in zip(df[lon].astype(float),
                                                             df[lat].astype(float))],
                           crs="EPSG:4326")
    return gdf
