import geopandas as gpd
import pandas as pd
from shapely.ops import unary_union
from typing import Tuple

def compute_distance_to_water(fields: gpd.GeoDataFrame, water: gpd.GeoDataFrame, crs: str = "EPSG:3857") -> gpd.GeoDataFrame:
    """
    Ensure both layers in the same projection and compute distance to nearest waterbody.
    Adds 'dist_to_water_m' column.
    """
    if fields.empty or water.empty:
        fields["dist_to_water_m"] = None
        return fields
    # project to metric CRS for distances
    fields_m = fields.to_crs(crs)
    water_m = water.to_crs(crs)
    water_union = unary_union(list(water_m.geometry))
    fields_m["dist_to_water_m"] = fields_m.geometry.apply(lambda g: g.distance(water_union))
    return fields_m.to_crs(fields.crs)

def compute_n_loads(fields: gpd.GeoDataFrame, n_df: pd.DataFrame, runoff_coef: float = 0.1) -> gpd.GeoDataFrame:
    """
    Estimate nitrogen load to water per field.
    - fields must have an 'area_ha' column or will be computed from geometry.
    - n_df should contain n_kg_per_ha values; we take mean if multiple.
    Returns fields with 'n_applied_kg_ha', 'n_total_kg', 'n_estimated_to_water_kg'.
    """
    f = fields.copy()
    if "area_ha" not in f.columns:
        f["area_ha"] = f.geometry.to_crs("EPSG:3857").area / 10000.0
    if n_df.empty:
        f["n_applied_kg_ha"] = None
        f["n_total_kg"] = None
        f["n_estimated_to_water_kg"] = None
        return f
    mean_n = n_df["n_kg_per_ha"].mean()
    f["n_applied_kg_ha"] = mean_n
    f["n_total_kg"] = f["n_applied_kg_ha"] * f["area_ha"]
    # simple model: portion of applied N that reaches water
    f["n_estimated_to_water_kg"] = f["n_total_kg"] * runoff_coef
    return f