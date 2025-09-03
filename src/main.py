import argparse
import os
import geopandas as gpd
import pandas as pd
import data_loader, analysis

def run_pipeline(root: str, out_dir: str):
    os.makedirs(out_dir, exist_ok=True)
    scan = data_loader.scan_workspace(root)
    print("Found files:", {k: len(v) for k, v in scan.items()})
    # load fields (first candidate)
    fields = data_loader.load_first_vector(scan["shapefiles"] + scan["geojson"] + scan["geopackages"])
    if fields.empty:
        print("No field vector found in workspace.")
    else:
        print("Loaded fields:", len(fields))

    try:
        # fields = data_loader.add_whg_geoms_to_fields(fields, scan["shapefiles"], name_hint="WHGGewAbstand_Polygone", col_name="restrictions")
        print("Attached WHG geometries to fields (column 'restrictions').")
    except Exception as e:
        print("Failed to attach WHG geometries:", e)

    # load water layers - look in Maps/ and root for likely water layers
    waters = data_loader.load_first_vector([p for p in scan["shapefiles"] + scan["geojson"] + scan["geopackages"] if "water" in p.lower() or "gew" in p.lower()])
    # parse N docs
    bew_dir = os.path.join(root, "Bewirtschaftungsdokumentation-PDF")
    if os.path.isdir(bew_dir):
        n_df = data_loader.load_bewirtschaftungs_docs(bew_dir)
    else:
        n_df = pd.DataFrame()
    # analysis
    if not fields.empty and not waters.empty:
        fields = analysis.compute_distance_to_water(fields, waters)
    fields = analysis.compute_n_loads(fields, n_df)
    print("Analysis complete.")
    # save outputs
    out_csv = os.path.join(out_dir, "fields_n_loads.csv")
    fields.drop(columns=["geometry"], errors="ignore").to_csv(out_csv, index=False)
    out_geo = os.path.join(out_dir, "fields_n_loads.geojson")
    fields.to_file(out_geo, driver="GeoJSON")
    print("Outputs written to", out_dir)

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", default=".", help="workspace root to scan")
    p.add_argument("--out", default="out", help="output folder")
    args = p.parse_args()
    run_pipeline(args.root, args.out)