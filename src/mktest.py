import json
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import pymannkendall as mk

ROOT = Path(__file__).resolve().parents[1]            # test_setup/ (folder with pixi.toml)
# 1. Generate sample time-series data
np.random.seed(42)
"""
years = np.arange(2000, 2021)
data = np.array([
    45, 47, 46, 49, 48, 51, 50,
    53, 52, 55, 54, 57, 56, 59,
    58, 61, 60, 63, 62, 65, 67
])
"""

with open(ROOT / "data/raw/t2m_odisha.json", "r") as data_file:
    data = json.load(data_file)
dates = np.array(data["dates"])
dat = np.array(data["values"])

# Remove missing or invalid observations
valid = np.isfinite(dat)
dates = dates[valid]
dat = dat[valid]


# 2. Perform Mann-Kendall test
result = mk.original_test(dat)

print("Mann-Kendall Test Results")
print("-------------------------")
print("Trend:", result.trend)
print("p-value:", result.p)
print("Tau:", result.Tau)
print("Slope:", result.slope)
print("Intercept:", result.intercept)

# 3. Calculate Sen's slope trend line
time = np.arange(len(dat))
trend_line = result.intercept + result.slope * time

# 4. Plot the graph
plt.figure(figsize=(12, 6))

plt.plot(
    dates, dat,
    marker='o',
    linestyle='-',
    color='blue',
    label='Observed Data'
)

plt.plot(
    dates, trend_line,
    color='red',
    linestyle='--',
    linewidth=2,
    label="Sen's Slope Trend"
)

plt.xlabel("Year", fontsize=12)
plt.ylabel("Observed Value", fontsize=12)
plt.title("Mann-Kendall Trend Test", fontsize=15)

plt.legend()
plt.grid(True, linestyle='--', alpha=0.5)

plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("mann_kendall_test.png", dpi=300)
print("saved")
plt.show()

