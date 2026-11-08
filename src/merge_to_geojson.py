"""
Merge the two Odisha data files into GeoJSON (State + City)
-----------------------------------------------------------
Inputs  (data/raw/):
    odisha_points_daily.json   39 districts/cities, daily T2MMEAN + T2MMAX   (extract_points.py)
    t2m_odisha.json            Odisha-wide daily mean temperature            (dataextract.py)
    odisha_boundary.geojson    OPTIONAL real Odisha border (Polygon/MultiPolygon)

Outputs (data/processed/):
    odisha_state.geojson       FeatureCollection with 1 State feature  (spec 6.1 + 6.3)
    odisha_cities.geojson      FeatureCollection with 39 City features (spec 6.2)

Run from the folder that contains pixi.toml (test_setup/):
    pixi run python src/merge_to_geojson.py

NOTE: the data is ~3 months of daily values (demo). "annual" is left empty on purpose:
an annual value needs a full calendar year of data.
"""
import json
import re
from collections import defaultdict
from pathlib import Path

# ---------------- settings ----------------
STATE_ID, STATE_NAME = "OD", "Odisha"
# ------------------------------------------

ROOT = Path(__file__).resolve().parents[1]      # test_setup/ (folder with pixi.toml)
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"
POINTS_JSON = RAW / "odisha_points_daily.json"
STATE_JSON = RAW / "t2m_odisha.json"
BOUNDARY_FILE = RAW / "odisha_boundary.geojson"
OUT.mkdir(parents=True, exist_ok=True)


# ---------- helpers ----------
def monthly_mean(dates, values):
    """{'2026-07': mean of that month's daily values}"""
    groups = defaultdict(list)
    for d, v in zip(dates, values):
        groups[d[:7]].append(float(v))
    return {m: round(sum(v) / len(v), 2) for m, v in sorted(groups.items())}


def by_date(dates, values):
    """{'2026-07-01': value}"""
    return {d: round(float(v), 2) for d, v in zip(dates, values)}


def temp_block(dates, mean, tmax=None):
    """Temperature block in the spec's annual / monthly layout (+ daily values)."""
    block = {
        "units": "°C",
        "annual": {},                                   # needs full years of data
        "monthly": monthly_mean(dates, mean),           # mean of daily mean temperature
        "daily": by_date(dates, mean),
    }
    if tmax is not None:
        block["monthly_tmax"] = monthly_mean(dates, tmax)   # mean of daily maximum
        block["daily_tmax"] = by_date(dates, tmax)
    return block


def make_id(name):
    return f"{STATE_ID}_" + re.sub(r"[^A-Z0-9]+", "_", name.upper()).strip("_")


def load_boundary(bbox):
    """Real border if odisha_boundary.geojson exists, otherwise a bbox placeholder."""
    if BOUNDARY_FILE.exists():
        gj = json.loads(BOUNDARY_FILE.read_text(encoding="utf-8"))
        if gj.get("type") == "FeatureCollection":
            feats = gj["features"]
            match = [
                f for f in feats
                if any(str(v).strip().lower() in ("odisha", "orissa")
                       for v in (f.get("properties") or {}).values())
            ]
            if len(match) == 1:
                feat = match[0]
            elif len(feats) == 1:
                feat = feats[0]
            else:
                raise SystemExit("Could not pick the Odisha feature in odisha_boundary.geojson.")
        elif gj.get("type") == "Feature":
            feat = gj
        else:
            feat = {"geometry": gj}
        geom = feat["geometry"]
        if geom["type"] == "Polygon":
            geom = {"type": "MultiPolygon", "coordinates": [geom["coordinates"]]}
        if geom["type"] != "MultiPolygon":
            raise SystemExit(f"Boundary geometry must be Polygon or MultiPolygon, got {geom['type']}.")
        return geom, BOUNDARY_FILE.name
    w, s, e, n = bbox
    ring = [[w, s], [e, s], [e, n], [w, n], [w, s]]
    return {"type": "MultiPolygon", "coordinates": [[ring]]}, "bbox_placeholder (NOT the real border)"


# ---------- load ----------
for f in (POINTS_JSON, STATE_JSON):
    if not f.exists():
        raise SystemExit(f"Missing input file: {f}")
points = json.loads(POINTS_JSON.read_text(encoding="utf-8"))
state = json.loads(STATE_JSON.read_text(encoding="utf-8"))

if points["dates"] != state["dates"]:
    print("WARNING: the two files cover different dates; each is used with its own dates.")

# ---------- City features (spec 6.2) ----------
city_features, seen_ids = [], set()
for p in points["points"]:
    n = len(points["dates"])
    if len(p["t2m_mean_c"]) != n or len(p["t2m_max_c"]) != n:
        raise SystemExit(f"{p['name']}: series length does not match the dates list.")
    city_id = make_id(p["name"])
    if city_id in seen_ids:
        raise SystemExit(f"Duplicate city_id: {city_id}")
    seen_ids.add(city_id)
    city_features.append(
        {
            "type": "Feature",
            "properties": {
                "city_id": city_id,
                "name": p["name"],
                "state_id": STATE_ID,
                "district": p["district"],
                "point_type": "district_hq" if p["type"] == "district" else "city",
                "temperature": temp_block(points["dates"], p["t2m_mean_c"], p["t2m_max_c"]),
                "grid_cell": {
                    "lat": p["cell"][0],
                    "lon": p["cell"][1],
                    "shares_cell_with": p["shares_cell_with"],
                },
                "source": points["source"],
            },
            "geometry": {"type": "Point", "coordinates": [p["lon"], p["lat"]]},   # lon first!
        }
    )

cities_fc = {
    "type": "FeatureCollection",
    "metadata": {
        "source": points["source"],
        "period": points["period"],
        "demo_only": True,
        "note": points["note"],
    },
    "features": city_features,
}

# ---------- State feature (spec 6.1 + 6.3) ----------
geometry, boundary_source = load_boundary(state["bbox"])
state_temp = temp_block(state["dates"], state["values"])
state_temp["daily_anomaly"] = by_date(state["dates"], state["anomalies"])
state_temp["anomaly_baseline"] = state["anomaly_baseline"]

state_feature = {
    "type": "Feature",
    "properties": {
        "state_id": STATE_ID,
        "name": STATE_NAME,
        "boundary_source": boundary_source,
        "climate": {"temp": state_temp},
        "climate_method": "area-weighted mean of the MERRA-2 cells inside the box "
        f"{state['bbox']} (west, south, east, north); not masked to the state border",
        "source": state["source"],
        "demo_only": True,
    },
    "geometry": geometry,
}
state_fc = {"type": "FeatureCollection", "features": [state_feature]}

# ---------- write ----------
(OUT / "odisha_cities.geojson").write_text(
    json.dumps(cities_fc, ensure_ascii=False, indent=2), encoding="utf-8"
)
(OUT / "odisha_state.geojson").write_text(
    json.dumps(state_fc, ensure_ascii=False, indent=2), encoding="utf-8"
)

print(f"State feature : {STATE_ID} | boundary: {boundary_source}")
print(f"City features : {len(city_features)}")
print(f"Months        : {', '.join(state_temp['monthly'])}")
print(f"Saved:\n  {OUT / 'odisha_state.geojson'}\n  {OUT / 'odisha_cities.geojson'}")