"""
Small demo slice for frontend development
-----------------------------------------
MERRA-2 daily mean 2 m air temperature (M2SDNXSLV, variable T2MMEAN)
averaged over a rough Odisha bounding box -> one JSON file for the frontend.

Run from the folder that contains pixi.toml (test_setup/):
    pixi run python src/dataextract.py

NOTE: ~3 months of daily data is ONLY for building/testing the UI.
"""
import json
from pathlib import Path

import earthaccess
import numpy as np
import pandas as pd
import xarray as xr

# ---------------- settings (edit these) ----------------
START, END = "2026-07-01", "2026-09-30"   # Oct 2026 is not published yet (~3 week lag after month end)
SHORT_NAME, VERSION = "M2SDNXSLV", "5.12.4"
VAR = "T2MMEAN"                           # daily mean 2 m air temperature, in Kelvin
# Rough Odisha box (west, south, east, north). NOT the exact state border.
WEST, SOUTH, EAST, NORTH = 81.0, 17.5, 88.0, 23.0
REGION_ID, VAR_ID = "odisha", "t2m"
# -------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]            # test_setup/ (folder with pixi.toml)
RAW = ROOT / "data" / "raw"                           # downloaded .nc4 files go here
OUT = RAW                                             # JSON + CSV output also go to data/raw
RAW.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)

# 1. Login (free Earthdata account) and search ------------------------------
earthaccess.login(persist=True)   # asks once, then remembers in ~/.netrc
results = earthaccess.search_data(
    short_name=SHORT_NAME, version=VERSION, temporal=(START, END)
)
print(f"Found {len(results)} daily files for {START} to {END}")
if not results:
    raise SystemExit("No files found. Try an earlier END date or check the dataset name.")

# 2. Download (global daily files, so this is the slow step) ------------------
paths = earthaccess.download(results, local_path=str(RAW))
paths = sorted(str(p) for p in paths)

# 3. Open, subset to the Odisha box, convert K -> degC -------------------------
ds = xr.open_mfdataset(paths, combine="by_coords")
t2m = ds[VAR].sel(lat=slice(SOUTH, NORTH), lon=slice(WEST, EAST)) - 273.15
print(f"Grid cells in box: {t2m.sizes['lat']} lat x {t2m.sizes['lon']} lon")

# 4. Area-weighted regional mean (cells get smaller towards the poles) ---------
weights = np.cos(np.deg2rad(t2m["lat"]))
series = t2m.weighted(weights).mean(dim=["lat", "lon"]).load()

values = series.values.astype(float)
dates = pd.to_datetime(series["time"].values).strftime("%Y-%m-%d").tolist()
if np.isnan(values).any():
    print("WARNING: missing values found in the series")

# 5. Anomaly vs the mean of this short period (demo only) ----------------------
anomalies = values - values.mean()

out = {
    "variable": VAR_ID,
    "region": REGION_ID,
    "units": "°C",
    "source": f"MERRA-2 {SHORT_NAME} v{VERSION}, {VAR}",
    "bbox": [WEST, SOUTH, EAST, NORTH],
    "dates": dates,
    "values": [round(float(v), 3) for v in values],
    "anomalies": [round(float(a), 3) for a in anomalies],
    "anomaly_baseline": "mean of this short period (demo only)",
    "demo_only": True,
    "note": "About 3 months of daily data, for building and testing the UI only.",
}

out_file = OUT / f"{VAR_ID}_{REGION_ID}.json"
out_file.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
pd.DataFrame({"date": dates, "t2m_degC": values}).to_csv(
    OUT / f"{VAR_ID}_{REGION_ID}_daily.csv", index=False
)

print(f"Days: {len(values)} | min {values.min():.1f} | max {values.max():.1f} °C")
print(f"Saved: {out_file}")