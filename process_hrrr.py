import os
import shutil
import json
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import pandas as pd
from herbie import Herbie

# 1. Directory Management: Clear and Recreate
# This ensures stale data from previous runs is deleted
output_dir = "web"
data_dir = os.path.join(output_dir, "data")

if os.path.exists(data_dir):
    shutil.rmtree(data_dir)
os.makedirs(data_dir, exist_ok=True)

# 2. Timing Logic (Find latest available run)
# We look back up to 3 hours to find the most recent complete run on AWS
now = pd.Timestamp("now", tz="UTC").floor("1h").replace(tzinfo=None)
print(f"Searching for most recent HRRR run starting from: {now}")

H = None
for offset in range(0, 4):
    try:
        check_time = now - pd.Timedelta(hours=offset)
        H = Herbie(date=check_time, model='hrrr', product='subh', fxx=0)
        print(f"Success! Found model run: {check_time}")
        now = check_time
        break
    except Exception:
        continue

if H is None:
    raise RuntimeError("Could not find any recent HRRR data on AWS.")

# 3. Define Map Bounds (Standard USA Zoom)
# These coordinates prevent the "stretched" look in Leaflet
extent = [-125, -66, 24, 50] 
web_crs = ccrs.PlateCarree()

forecast_metadata = []

# 4. Loop through 18 forecast hours
for fxx in range(0, 19):
    print(f"Processing Forecast Hour: {fxx:02d}...")
    try:
        # Pull precip type variables
        h_idx = Herbie(date=now, model='hrrr', product='subh', fxx=fxx)
        ds = h_idx.xarray(":(?:CSNOW|CICEP|CFRZR|CRAIN):surface:")
        
        # Combine into types: Rain=1, FrzRain=2, Sleet=3, Snow=4
        ptype = ds.crain * 1 + ds.cfrzr * 2 + ds.cicep * 3 + ds.csnow * 4
        
        # Create the plot
        fig = plt.figure(figsize=(12, 8), frameon=False)
        ax = plt.axes(projection=web_crs)
        ax.set_extent(extent, crs=web_crs)
        ax.axis('off')
        
        colors = [(0,0,0,0), (0,0.8,0,0.6), (1,0,0,0.6), (1,0.5,0,0.6), (0,0,1,0.6)]
        cmap = plt.matplotlib.colors.ListedColormap(colors)
        
        # Plot data using lat/lon coordinates to ensure no distortion
        ax.pcolormesh(ds.longitude, ds.latitude, ptype.values[0], 
                      transform=web_crs, cmap=cmap, shading='nearest')
        
        filename = f"overlay_{fxx:02d}.png"
        filepath = os.path.join(data_dir, filename)
        plt.savefig(filepath, transparent=True, bbox_inches='tight', pad_inches=0, dpi=150)
        plt.close(fig)
        
        forecast_metadata.append({
            "hour": fxx,
            "file": f"data/{filename}",
            "valid_time": (now + pd.Timedelta(hours=fxx)).strftime("%Y-%m-%d %H:%M UTC")
        })
    except Exception as e:
        print(f"Skipping hour {fxx} due to error: {e}")

# 5. Save the Master Manifest
master_data = {
    "run_time": now.strftime("%Y-%m-%d %H:%M UTC"),
    "bounds": [[24, -125], [50, -66]], 
    "forecasts": forecast_metadata
}

with open(os.path.join(output_dir, "manifest.json"), "w") as f:
    json.dump(master_data, f)

print("Processing complete.")
