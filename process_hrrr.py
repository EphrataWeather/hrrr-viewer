import os
import json
from herbie import Herbie
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# 1. Setup environment and directories
os.environ['HERBIE_SAVE_DIR'] = '/tmp/herbie_data'
os.makedirs("web", exist_ok=True)

# 2. Get the most recent valid date (HRRR usually lags by ~1 hour on AWS)
# We look at the top of the current hour in UTC
now = pd.Timestamp("now", tz="UTC").floor("1h").replace(tzinfo=None)

print(f"Attempting to fetch HRRR data for: {now}")

try:
    # 3. Pull the latest sub-hourly HRRR data
    # We specify the date and fxx=0 (the analysis/nowcast)
    H = Herbie(date=now, model='hrrr', product='subh', fxx=0) 
    
    # 4. Download and Subset for Categorical Precip Types
    ds = H.xarray(":(?:CSNOW|CICEP|CFRZR|CRAIN):surface:")
except Exception as e:
    print(f"Primary fetch failed: {e}. Trying one hour earlier...")
    # If the current hour isn't on AWS yet, try the previous hour
    now = now - pd.Timedelta(hours=1)
    H = Herbie(date=now, model='hrrr', product='subh', fxx=0)
    ds = H.xarray(":(?:CSNOW|CICEP|CFRZR|CRAIN):surface:")

# 5. Process Precip Type (Logic: Snow=4, Sleet=3, FrzRain=2, Rain=1)
ptype = ds.crain * 1 + ds.cfrzr * 2 + ds.cicep * 3 + ds.csnow * 4

# 6. Generate the Image
colors = [(0,0,0,0), (0,0.8,0,0.6), (1,0,0,0.6), (1,0.5,0,0.6), (0,0,1,0.6)]
cmap = plt.matplotlib.colors.ListedColormap(colors)

fig = plt.figure(frameon=False, figsize=(12, 8))
ax = plt.Axes(fig, [0., 0., 1., 1.])
ax.set_axis_off()
fig.add_axes(ax)

# Use the first time step [0]
ax.imshow(ptype.values[0], cmap=cmap, aspect='auto', interpolation='nearest')
plt.savefig("web/overlay.png", transparent=True, dpi=300)

# 7. Save Bounds and Timestamp for the Web Map
bounds = [
    [float(ds.latitude.min()), float(ds.longitude.min())],
    [float(ds.latitude.max()), float(ds.longitude.max())]
]

metadata = {
    "bounds": bounds,
    "updated": now.strftime("%Y-%m-%d %H:%M UTC")
}

with open("web/metadata.json", "w") as f:
    json.dump(metadata, f)

print(f"Map updated successfully for {now}")
