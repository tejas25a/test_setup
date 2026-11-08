"""
Point data for Odisha (39 districts/cities) from MERRA-2 daily data
-------------------------------------------------------------------
Reads   : data/coord/odisha_points.csv   (name, district, lat, lon, ...)
Needs   : MERRA-2 daily files (M2SDNXSLV). Missing ones are downloaded into data/raw/
Writes  : data/raw/odisha_points_daily.csv    (one row per point per day)
          data/raw/odisha_points_daily.json   (one entry per point, for the frontend)

Run from the folder that contains pixi.toml (test_setup/):
    pixi run python src/point_data_ext.py

NOTE: MERRA-2 cells are ~50 km wide (0.5 deg lat x 0.625 deg lon). Each point gets the value
of the cell it falls in, so points in the same cell have identical series.
About 3 months of daily data is for building/testing the UI only.
"""
import json
from pathlib import Path
from urllib.parse import urlparse

import earthaccess
import numpy as np
import pandas as pd
import xarray as xr

# ---------------- settings (edit these) ----------------
START, END = "2026-07-01", "2026-09-30"
SHORT_NAME, VERSION = "M2SDNXSLV", "5.12.4"
# MERRA-2 variable -> output column name (both are in Kelvin in the file)
VARS = {"T2MMEAN": "t2m_mean_c", "T2MMAX": "t2m_max_c"}
# -------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]      # test_setup/ (folder with pixi.toml)
RAW = ROOT / "data" / "raw"
COORD = ROOT / "data" / "coord"
POINTS_CSV = COORD / "odisha_points.csv"
OUT_CSV = RAW / "odisha_points_daily.csv"
OUT_JSON = RAW / "odisha_points_daily.json"
RAW.mkdir(parents=True, exist_ok=True)

# 1. Read the points ---------------------------------------------------------
if not POINTS_CSV.exists():
    raise SystemExit(f"Put odisha_points.csv in {RAW} first.")
pts = pd.read_csv(POINTS_CSV).fillna({"shares_cell_with": ""})
n_pts = len(pts)
print(f"Loaded {n_pts} points")

# 2. Find the daily files and download only the missing ones -----------------
earthaccess.login(persist=True)
results = earthaccess.search_data(
    short_name=SHORT_NAME, version=VERSION, temporal=(START, END)
)
print(f"Found {len(results)} daily files for {START} to {END}")
if not results:
    raise SystemExit("No files found. Try an earlier END date.")


def file_name(granule):
    return Path(urlparse(granule.data_links()[0]).path).name


names = [file_name(g) for g in results]
missing = [g for g, n in zip(results, names) if not (RAW / n).exists()]
print(f"Already on disk: {len(results) - len(missing)} | to download: {len(missing)}")
if missing:
    earthaccess.download(missing, local_path=str(RAW))

paths = sorted(str(RAW / n) for n in names)
absent = [p for p in paths if not Path(p).exists()]
if absent:
    raise SystemExit(f"{len(absent)} files are missing after download, e.g. {absent[0]}")

# 3. Open all files and pick the nearest grid cell for every point -----------
ds = xr.open_mfdataset(paths, combine="by_coords")
sel = ds[list(VARS)].sel(
    lat=xr.DataArray(pts["lat"].values, dims="point"),
    lon=xr.DataArray(pts["lon"].values, dims="point"),
    method="nearest",
).load()

# sanity check: the cell chosen here must match the cell listed in the CSV
cell_lat = sel["lat"].values
cell_lon = sel["lon"].values
bad = ~(
    np.isclose(cell_lat, pts["merra2_cell_lat"].values)
    & np.isclose(cell_lon, pts["merra2_cell_lon"].values)
)
if bad.any():
    print("WARNING: cell differs from the CSV for:", ", ".join(pts.loc[bad, "name"]))

dates = pd.to_datetime(sel["time"].values).strftime("%Y-%m-%d").to_numpy()
n_days = len(dates)
temp = {col: sel[var].values - 273.15 for var, col in VARS.items()}   # K -> degC, (time, point)
for col, arr in temp.items():
    if np.isnan(arr).any():
        print(f"WARNING: missing values in {col}")

# 4. Save: tidy CSV (one row per point per day) -------------------------------
long = pd.DataFrame(
    {
        "date": np.repeat(dates, n_pts),
        "name": np.tile(pts["name"].values, n_days),
        "district": np.tile(pts["district"].values, n_days),
        "type": np.tile(pts["type"].values, n_days),
        "lat": np.tile(pts["lat"].values, n_days),
        "lon": np.tile(pts["lon"].values, n_days),
        "cell_lat": np.tile(cell_lat, n_days),
        "cell_lon": np.tile(cell_lon, n_days),
        **{col: arr.ravel().round(2) for col, arr in temp.items()},
    }
)
long.to_csv(OUT_CSV, index=False)

# 5. Save: JSON for the frontend (one entry per point) ------------------------
points_json = []
for k, r in pts.iterrows():
    points_json.append(
        {
            "name": r["name"],
            "district": r["district"],
            "type": r["type"],
            "lat": float(r["lat"]),
            "lon": float(r["lon"]),
            "cell": [float(cell_lat[k]), float(cell_lon[k])],
            "shares_cell_with": [x for x in r["shares_cell_with"].split("; ") if x],
            **{col: [round(float(v), 2) for v in arr[:, k]] for col, arr in temp.items()},
        }
    )

out = {
    "source": f"MERRA-2 {SHORT_NAME} v{VERSION}",
    "variables": {col: {"merra2_name": var, "units": "°C"} for var, col in VARS.items()},
    "period": [START, END],
    "dates": dates.tolist(),
    "points": points_json,
    "demo_only": True,
    "note": "About 3 months of daily data, for building and testing the UI only. "
    "Each point holds the value of its ~50 km grid cell.",
}
OUT_JSON.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")

# 6. Quick summary ------------------------------------------------------------
print(f"\nDays: {n_days} | points: {n_pts} | unique cells: {len(set(zip(cell_lat, cell_lon)))}")
peak = pd.Series(temp["t2m_max_c"].max(axis=0), index=pts["name"]).sort_values(ascending=False)
print("Highest daily max (degC) in the period:")
print(peak.head(5).round(1).to_string())
print(f"\nSaved:\n  {OUT_CSV}\n  {OUT_JSON}")