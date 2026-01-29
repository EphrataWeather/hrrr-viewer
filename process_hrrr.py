import os
import json
from herbie import Herbie
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# 1. Setup environment
os.environ['HERBIE_SAVE_DIR'] = '/tmp/herbie_data'
os.makedirs("web", exist_ok=True)

# 2. Timing Logic (Search for latest available run)
now = pd.Timestamp("now", tz="UTC").floor("1h").replace(tzinfo=None)
print(f"Attempting to fetch HRRR data for: {now}")

try:
    H = Herbie(date=now, model='hrrr', product='subh', fxx=0) 
    ds = H.xarray(":(?:CSNOW|CICEP|CFRZR|CRAIN):surface:")
except Exception:
    print("Current hour not found, trying previous hour...")
    now = now - pd.Timedelta(hours=1)
    H = Herbie(date=now, model='hrrr', product='subh', fxx=0)
    ds = H.xarray(":(?:CSNOW|CICEP|CFRZR|CRAIN):surface:")

# 3. Process Precip Type
ptype_raw = ds.crain * 1 + ds.cfrzr * 2 + ds.cicep * 3 + ds.csnow * 4

# --- FIX: RESHAPE DATA TO 2D GRID ---
# HRRR subh is typically (1, 1059, 1799) for (time, y, x)
# We remove the time dimension and ensure it's 2D
if len(ptype_raw.shape) == 3:
    ptype_2d = ptype_raw.values[0] # Take first time step
else:
    # If it came in flat (e.g., shape 1905141), reshape to standard HRRR grid
    # HRRR CONUS grid is 1059 rows by 1799 columns
    try:
        ptype_2d = ptype_raw.values.reshape(1059, 1799)
    except ValueError:
        # Fallback if dimensions differ (e.g., Alaska or different product)
        ptype_2d = ptype_raw.values 

# 4. Generate the Image
colors = [(0,0,0,0), (0,0.8,0,0.6), (1,0,0,0.6), (1,0.5,0,0.6), (0,0,1,0.6)]
cmap = plt.matplotlib.colors.ListedColormap(colors)

fig = plt.figure(frameon=False, figsize=(15, 10)) # Adjusted size for better resolution
ax = plt.Axes(fig, [0., 0., 1., 1.])
ax.set_axis_off()
fig.add_axes(ax)

# Plotting the 2D array
ax.imshow(ptype_2d, cmap=cmap, aspect='auto', interpolation='nearest')
plt.savefig("web/overlay.png", transparent=True, dpi=300)

# 5. Metadata for Leaflet
bounds = [
    [float(ds.latitude.min()), float(ds.longitude.min())],
    [float(ds.latitude.max()), float(ds.longitude.max())]
]

with open("web/metadata.json", "w") as f:
    json.dump({"bounds": bounds, "updated": now.strftime("%Y-%m-%d %H:%M UTC")}, f)

print(f"Map updated successfully for {now}")
