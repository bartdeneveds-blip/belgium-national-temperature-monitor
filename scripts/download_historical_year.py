from __future__ import annotations
import argparse, time
from pathlib import Path
import cdsapi
from common import AREA, national_daily_max_from_netcdf


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--year",type=int,required=True); ap.add_argument("--output",type=Path,required=True); a=ap.parse_args()
    year=a.year; target=Path(f"era5_belgium_{year}.nc")
    request={"product_type":["reanalysis"],"variable":["2m_temperature"],"year":[str(year)],"month":[f"{m:02d}" for m in range(1,13)],"day":[f"{d:02d}" for d in range(1,32)],"time":[f"{h:02d}:00" for h in range(24)],"area":AREA,"data_format":"netcdf","download_format":"unarchived"}
    for attempt in range(1,6):
        try:
            target.unlink(missing_ok=True); print(f"{year}: attempt {attempt}/5",flush=True)
            cdsapi.Client().retrieve("reanalysis-era5-single-levels",request,str(target)); break
        except Exception:
            target.unlink(missing_ok=True)
            if attempt==5: raise
            time.sleep(60*attempt)
    daily=national_daily_max_from_netcdf(target)
    expected=366 if __import__('calendar').isleap(year) else 365
    if len(daily)!=expected: raise RuntimeError(f"{year}: {len(daily)} days, expected {expected}")
    daily["year"]=year; daily["month_day"]=daily["date"].str[5:]
    a.output.parent.mkdir(parents=True,exist_ok=True); daily.to_csv(a.output,index=False); target.unlink(missing_ok=True)
    print(f"{year}: wrote {len(daily)} national daily values")

if __name__=="__main__": main()
