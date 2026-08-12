# Belgian national temperature anomaly monitor

This repository calculates an area-weighted Belgian mean of daily maximum 2 metre temperature from ERA5/ERA5T.

## Definition

1. Select every ERA5 0.25 degree grid centre that lies inside the Belgian ADM0 boundary.
2. Calculate the UTC daily maximum at each selected grid centre.
3. Calculate a national weighted mean using `cos(latitude)` weights, which approximate cell area on a regular longitude-latitude grid.
4. Compare it with a similarly calculated 1961-1990 climatology using a circular 31-day window.
5. Publish only ERA5T rows. Forecast data are not included.

## Required GitHub secrets

- `CDS_API_URL`: `https://cds.climate.copernicus.eu/api`
- `CDS_API_KEY`: personal Copernicus CDS token

Accept the ERA5 single-level dataset licence in the CDS before running the workflows.

## Run order

1. Run **Prepare Belgian ERA5 grid mask** once.
2. Inspect `data/belgium_era5_grid_weights.csv`, including the number and coordinates of selected centres.
3. Optionally test one historical year locally or temporarily reduce the matrix.
4. Run **Build Belgian ERA5 climatology** once.
5. Run **Backfill Belgian ERA5T year** once for 2026.
6. Run **Daily Belgian ERA5T update** manually once.
7. Leave the daily schedule enabled.
8. Connect Datawrapper to the raw URL of `data/belgium_national_temperature_anomaly_era5t.csv`.

## Datawrapper file

`data/belgium_national_temperature_anomaly_era5t.csv`

Suggested source line: Copernicus Climate Change Service/ECMWF, ERA5 and ERA5T; Belgian boundary from geoBoundaries/Eurostat; own area-weighted calculation.

## Boundary attribution

The setup script downloads the Belgium ADM0 boundary through geoBoundaries `gbOpen` and stores the exact GeoJSON in this repository for reproducibility. Check the stored metadata/source before publication and retain attribution.
