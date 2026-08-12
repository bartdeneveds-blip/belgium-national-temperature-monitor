import pandas as pd
from pathlib import Path
p=Path("data/belgium_national_temperature_anomaly_era5t.csv"); df=pd.read_csv(p)
req={"date","belgium_mean_daily_max_c","historic_norm_c","anomaly_c","status","weighting","grid_points"}
assert not(req-set(df.columns)), f"Missing columns {req-set(df.columns)}"
assert not df.empty and df.date.is_unique
assert df.status.eq("era5t").all()
assert ((df.belgium_mean_daily_max_c-df.historic_norm_c).round(2)==df.anomaly_c.round(2)).all()
assert df.anomaly_c.between(-30,30).all()
assert df.grid_points.nunique()==1
print(f"Validated {len(df)} rows; {df.grid_points.iloc[0]} grid centres; {df.date.min()} to {df.date.max()}")
