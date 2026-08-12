from __future__ import annotations
import calendar, os, time
from datetime import datetime, timedelta, timezone
from pathlib import Path
import cdsapi
import pandas as pd
from common import AREA, OUTPUT_FILE, CLIMATOLOGY_FILE, add_anomalies, national_daily_max_from_netcdf

LAG=int(os.getenv("ERA5_LAG_DAYS","5")); YEAR=int(os.getenv("DATA_YEAR",str(datetime.now(timezone.utc).year))); CACHE=Path("data/cache")

def cutoff():
    d=datetime.now(timezone.utc).date()-timedelta(days=LAG)
    return pd.Timestamp(max(d, datetime(YEAR,1,1).date()) if d.year==YEAR else (datetime(YEAR,12,31).date() if d.year>YEAR else datetime(YEAR,1,1).date()))

def existing():
    if not OUTPUT_FILE.exists(): return pd.DataFrame(columns=["date","belgium_mean_daily_max_c","historic_norm_c","anomaly_c","status","weighting","grid_points"])
    return pd.read_csv(OUTPUT_FILE,dtype={"date":str})

def missing_ranges(df,end):
    have=set(df.loc[df.status.eq("era5t"),"date"]) if not df.empty else set(); expected=pd.date_range(f"{YEAR}-01-01",end).strftime("%Y-%m-%d").tolist(); missing=[pd.Timestamp(d) for d in expected if d not in have]
    if not missing:return []
    ranges=[]; start=prev=missing[0]
    for d in missing[1:]:
        if d==prev+pd.Timedelta(days=1) and d.month==start.month: prev=d
        else:ranges.append((start,prev)); start=prev=d
    ranges.append((start,prev)); return ranges

def retrieve(start,end):
    target=CACHE/f"era5t_{start:%Y%m%d}_{end:%Y%m%d}.nc"; req={"product_type":["reanalysis"],"variable":["2m_temperature"],"year":[str(start.year)],"month":[f"{start.month:02d}"],"day":[f"{d:02d}" for d in range(start.day,end.day+1)],"time":[f"{h:02d}:00" for h in range(24)],"area":AREA,"data_format":"netcdf","download_format":"unarchived"}
    for attempt in range(1,6):
        try: target.unlink(missing_ok=True); cdsapi.Client().retrieve("reanalysis-era5-single-levels",req,str(target)); return target
        except Exception:
            target.unlink(missing_ok=True)
            if attempt==5: raise
            time.sleep(60*attempt)

def main():
    if not CLIMATOLOGY_FILE.exists(): raise RuntimeError("National climatology is missing")
    CACHE.mkdir(parents=True,exist_ok=True); old=existing(); frames=[]; end=cutoff()
    for start,stop in missing_ranges(old,end):
        p=retrieve(start,stop)
        try: frames.append(national_daily_max_from_netcdf(p))
        finally:p.unlink(missing_ok=True)
    if frames:
        new=add_anomalies(pd.concat(frames,ignore_index=True)); old=old.loc[~old.date.isin(new.date)]; out=pd.concat([old,new],ignore_index=True)
    else: out=old
    out=out.sort_values("date").drop_duplicates("date",keep="last"); OUTPUT_FILE.parent.mkdir(exist_ok=True); out.to_csv(OUTPUT_FILE,index=False)
    print(f"Rows={len(out)}; first={out.date.min()}; last={out.date.max()}; cutoff={end.date()}")

if __name__=="__main__":main()
