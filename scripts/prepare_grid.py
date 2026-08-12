from __future__ import annotations
import json, math
from pathlib import Path
import requests
import pandas as pd
from shapely.geometry import Point, shape
from shapely.ops import unary_union

API = "https://www.geoboundaries.org/api/current/gbOpen/BEL/ADM0/"
BOUNDARY = Path("data/belgium_boundary.geojson")
WEIGHTS = Path("data/belgium_era5_grid_weights.csv")


def quarter_degree_values(low: float, high: float):
    start = math.ceil(low * 4) / 4
    end = math.floor(high * 4) / 4
    n = int(round((end-start)*4))
    return [round(start+i*0.25, 2) for i in range(n+1)]


def main():
    metadata = requests.get(API, timeout=60).json()
    if isinstance(metadata, list): metadata = metadata[0]
    url = metadata["gjDownloadURL"]
    geojson = requests.get(url, timeout=120).json()
    BOUNDARY.parent.mkdir(parents=True, exist_ok=True)
    BOUNDARY.write_text(json.dumps(geojson), encoding="utf-8")
    features = geojson["features"] if geojson.get("type") == "FeatureCollection" else [geojson]
    country = unary_union([shape(f["geometry"] if f.get("type")=="Feature" else f) for f in features])
    minx,miny,maxx,maxy = country.bounds
    rows=[]
    for lat in quarter_degree_values(miny,maxy):
        for lon in quarter_degree_values(minx,maxx):
            if country.covers(Point(lon,lat)):
                rows.append({"latitude":lat,"longitude":lon,"weight":math.cos(math.radians(lat)),"selection":"grid_centre_inside_belgium"})
    df=pd.DataFrame(rows).sort_values(["latitude","longitude"], ascending=[False,True])
    if len(df) < 10:
        raise RuntimeError(f"Only {len(df)} grid centres selected")
    df["normalized_weight"] = df["weight"] / df["weight"].sum()
    df.to_csv(WEIGHTS,index=False)
    print(f"Selected {len(df)} ERA5 grid centres. Weight sum={df['weight'].sum():.6f}")
    print(f"Boundary source: {metadata.get('boundarySource')}; licence: {metadata.get('boundaryLicense')}")

if __name__ == "__main__": main()
