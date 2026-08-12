from __future__ import annotations
import math
from pathlib import Path
import pandas as pd
import xarray as xr

WEIGHTS_FILE = Path("data/belgium_era5_grid_weights.csv")
CLIMATOLOGY_FILE = Path("data/climatology_belgium_1961_1990.csv")
OUTPUT_FILE = Path("data/belgium_national_temperature_anomaly_era5t.csv")
AREA = [51.75, 2.25, 49.25, 6.75]  # north, west, south, east


def load_weights() -> pd.DataFrame:
    weights = pd.read_csv(WEIGHTS_FILE)
    required = {"latitude", "longitude", "weight"}
    if required - set(weights.columns):
        raise RuntimeError("Grid weights file has missing columns")
    weights["lat_key"] = weights["latitude"].round(4)
    weights["lon_key"] = weights["longitude"].round(4)
    weights["weight"] = weights["weight"].astype(float)
    if len(weights) < 10 or weights["weight"].sum() <= 0:
        raise RuntimeError("Grid weights are empty or implausible")
    return weights


def find_temperature_variable(ds: xr.Dataset) -> str:
    if "t2m" in ds.data_vars:
        return "t2m"
    variables = list(ds.data_vars)
    if not variables:
        raise RuntimeError("NetCDF contains no data variables")
    return variables[0]


def national_daily_max_from_netcdf(path: Path) -> pd.DataFrame:
    weights = load_weights()
    with xr.open_dataset(path) as ds:
        var = find_temperature_variable(ds)
        da = ds[var] - 273.15
        time_name = "valid_time" if "valid_time" in da.coords else "time"
        if time_name not in da.coords:
            raise RuntimeError("No time coordinate found")
        # First calculate the UTC daily maximum at each raster point.
        cell_daily = da.resample({time_name: "1D"}).max()
        frame = cell_daily.to_dataframe(name="cell_daily_max_c").reset_index()

    frame["lat_key"] = frame["latitude"].round(4)
    frame["lon_key"] = frame["longitude"].round(4)
    frame = frame.merge(weights[["lat_key","lon_key","weight"]], on=["lat_key","lon_key"], how="inner")
    if frame.empty:
        raise RuntimeError("No ERA5 grid centres matched the Belgian mask")
    frame["weighted"] = frame["cell_daily_max_c"] * frame["weight"]
    result = frame.groupby(time_name, as_index=False).agg(weighted_sum=("weighted","sum"), weight_sum=("weight","sum"), grid_points=("weight","size"))
    result["belgium_mean_daily_max_c"] = result["weighted_sum"] / result["weight_sum"]
    result["date"] = pd.to_datetime(result[time_name]).dt.strftime("%Y-%m-%d")
    return result[["date","belgium_mean_daily_max_c","grid_points"]]


def add_anomalies(daily: pd.DataFrame) -> pd.DataFrame:
    clim = pd.read_csv(CLIMATOLOGY_FILE, dtype={"month_day":str}).set_index("month_day")
    out = daily.copy()
    out["month_day"] = pd.to_datetime(out["date"]).dt.strftime("%m-%d")
    out["historic_norm_c"] = out["month_day"].map(clim["historic_norm_c"])
    if out["historic_norm_c"].isna().any():
        raise RuntimeError("Historical norm missing for one or more dates")
    out["belgium_mean_daily_max_c"] = out["belgium_mean_daily_max_c"].round(2)
    out["historic_norm_c"] = out["historic_norm_c"].round(2)
    out["anomaly_c"] = (out["belgium_mean_daily_max_c"] - out["historic_norm_c"]).round(2)
    out["status"] = "era5t"
    out["weighting"] = "cosine_latitude"
    return out[["date","belgium_mean_daily_max_c","historic_norm_c","anomaly_c","status","weighting","grid_points"]]
