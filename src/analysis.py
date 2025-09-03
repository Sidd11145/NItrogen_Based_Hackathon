import geopandas as gpd
import pandas as pd
from shapely.ops import unary_union
from typing import Tuple

def calculate_nitrogen_from_distance(dist_to_water_m):
    """Calculate the nitrogen requirement based on distance from water body."""
    if dist_to_water_m >= 3000:  # Example threshold for nitrogen application
        return 80  # For large distance, apply 80 kg N/ha
    elif dist_to_water_m >= 2000:
        return 50  # Medium distance, apply 50 kg N/ha
    elif dist_to_water_m >= 1000:
        return 40  # Shorter distance, apply 40 kg N/ha
    else:
        return 0  # No nitrogen applied if too close to the water

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

    # Apply the fertilizer calculation based on distance to water
    fields_m["fertilizer_amount_N_kg_per_ha"] = fields_m["dist_to_water_m"].apply(calculate_nitrogen_from_distance)
    return fields_m.to_crs(fields.crs)

def compute_n_loads(fields: gpd.GeoDataFrame, n_df: pd.DataFrame, runoff_coef: float = 0.1) -> gpd.GeoDataFrame:
    """
    Estimate nitrogen load to water per field.
    - fields must have an 'area_ha' column or will be computed from geometry.
    - n_df should contain n_kg_per_ha values; we take mean if multiple.
    Returns fields with 'n_applied_kg_ha', 'n_total_kg', 'n_estimated_to_water_kg'.
    """
    print("Computing nitrogen loads...")
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
