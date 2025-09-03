import os
import re
from typing import List, Dict
import geopandas as gpd
import pdfplumber
import pandas as pd

def scan_workspace(root: str) -> Dict[str, List[str]]:
    """
    Scan workspace root for geo and pdf files. Returns dict with keys:
    'shapefiles', 'geopackages', 'geojson', 'pdfs'.
    """
    out = {"shapefiles": [], "geopackages": [], "geojson": [], "pdfs": []}
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            path = os.path.join(dirpath, fn)
            lower = fn.lower()
            if lower.endswith(".shp"):
                out["shapefiles"].append(path)
            elif lower.endswith(".gpkg"):
                out["geopackages"].append(path)
            elif lower.endswith(".geojson") or lower.endswith(".json"):
                out["geojson"].append(path)
            elif lower.endswith(".pdf"):
                out["pdfs"].append(path)
    return out

def load_first_vector(paths: List[str]) -> gpd.GeoDataFrame:
    """
    Load first existing vector file from list using geopandas.
    """
    for p in paths:
        try:
            return gpd.read_file(p)
        except Exception:
            continue
    return gpd.GeoDataFrame()

def extract_n_from_pdf(pdf_path: str) -> List[Dict]:
    """
    Extract numeric 'N' application values from PDF text using regex.
    Returns list of records: {'source': pdf_path, 'n_kg_per_ha': float, 'raw': str}
    """
    records = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            full = "\n".join([p.extract_text() or "" for p in pdf.pages])
    except Exception:
        return records
    # simple regex to find "N" followed by numbers (e.g. "N 120 kg/ha", "N: 80 kg/ha")
    regex = re.compile(r"\bN[:\s]*([0-9]{1,4}(?:[.,][0-9]+)?)\s*(?:kg\/ha|kg/ha|kg per ha|kg ha-1)?", re.IGNORECASE)
    for m in regex.finditer(full):
        val = float(m.group(1).replace(",", "."))
        records.append({"source": pdf_path, "n_kg_per_ha": val, "raw": m.group(0)})
    return records

def load_bewirtschaftungs_docs(folder: str) -> pd.DataFrame:
    """
    Parse PDFs in the Bewirtschaftungsdokumentation-PDF folder and return a DataFrame
    of N applications.
    """
    records = []
    for fn in os.listdir(folder):
        if fn.lower().endswith(".pdf"):
            p = os.path.join(folder, fn)
            records.extend(extract_n_from_pdf(p))
    return pd.DataFrame(records)