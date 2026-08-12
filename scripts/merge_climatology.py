from pathlib import Path
import pandas as pd
INPUT=Path("yearly-data"); OUTPUT=Path("data/climatology_belgium_1961_1990.csv")
files=sorted(INPUT.glob("**/belgium_*.csv"))
if len(files)!=30: raise RuntimeError(f"Expected 30 yearly files, found {len(files)}")
data=pd.concat([pd.read_csv(f,dtype={"month_day":str}) for f in files],ignore_index=True)
if set(data.year.astype(int)) != set(range(1961,1991)): raise RuntimeError("Historical years incomplete")
calendar_days=pd.date_range("2000-01-01","2000-12-31").strftime("%m-%d").tolist(); pos={d:i for i,d in enumerate(calendar_days)}; rows=[]
for md in calendar_days:
    window={calendar_days[(pos[md]+o)%366] for o in range(-15,16)}
    vals=data.loc[data.month_day.isin(window),"belgium_mean_daily_max_c"]
    rows.append({"month_day":md,"historic_norm_c":round(float(vals.mean()),2),"sample_count":int(vals.count()),"reference_period":"1961-1990","geography":"Belgium","weighting":"cosine_latitude","grid_selection":"centre_inside_boundary"})
out=pd.DataFrame(rows); OUTPUT.parent.mkdir(exist_ok=True); out.to_csv(OUTPUT,index=False); print(f"Wrote {len(out)} climatology rows")
