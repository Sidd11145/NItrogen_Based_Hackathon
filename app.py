from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict
import geopandas as gpd
from shapely.geometry import shape, Polygon, MultiPolygon

# -------------------------------
# Load GeoJSON file and create spatial index
# -------------------------------
gdf = gpd.read_file("fields_n_loads.geojson")
sindex = gdf.sindex  # spatial index for fast queries

# -------------------------------
# FastAPI app
# -------------------------------
app = FastAPI(title="Fertilizer & Restriction API")

# -------------------------------
# Input model
# -------------------------------
class GeoJSONRequest(BaseModel):
    type: str
    coordinates: Any  # can be list of coords (Polygon) or list of list (MultiPolygon)

# -------------------------------
# Helper function to convert input to shapely geometry
# -------------------------------
def parse_geojson(geojson: GeoJSONRequest):
    try:
        geom = shape({"type": geojson.type, "coordinates": geojson.coordinates})
        if not isinstance(geom, (Polygon, MultiPolygon)):
            raise ValueError("Geometry must be Polygon or MultiPolygon")
        return geom
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid GeoJSON: {e}")

# -------------------------------
# API endpoint
# -------------------------------
@app.post("/check-area")
def check_area(request: GeoJSONRequest):
    polygon = parse_geojson(request)

    # Use spatial index to filter possible matches
    possible_matches_index = list(sindex.intersection(polygon.bounds))
    possible_matches = gdf.iloc[possible_matches_index]

    results = []
    for _, row in possible_matches.iterrows():
        if polygon.intersects(row.geometry):
            results.append({
                "id": row.get("id", None),
                "fertilizer": row.get("fertilizer", None),
                "restriction": row.get("restriction", None),
                "geometry": row.geometry.__geo_interface__  # return geometry in GeoJSON format
            })

    if not results:
        return {"message": "No matching area found"}
    return {"matches": results}

# -------------------------------
# Health check endpoint
# -------------------------------
@app.get("/health")
def health_check():
    return {"status": "API is running"}
