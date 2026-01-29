import os
import json
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import pandas as pd
from herbie import Herbie

# 1. Setup
os.environ['HERBIE_SAVE_DIR'] = '/tmp/herbie_data'
os.makedirs("web", exist_ok=True)

# 2. Find the latest model run (Start 1 hour ago to ensure data availability)
now = pd.Timestamp("now", tz="UTC").floor("1h") - pd.Timedelta(hours=1)
now = now.replace(tzinfo=None)

print(f"Fetching HRRR Forecast initialized at: {now}")

# 3. Define the Projections
# HRRR Native (Approximate Lambert parameters for HRRR)
hrrr_crs = ccrs.LambertConformal(central_longitude=-97.5, central_latitude=38.5, standard_parallels=(38.5, 38.5))
# Web Map Standard (Lat/Lon) - The target for Leaflet
web_crs = ccrs.PlateCarree()

# 4. Loop through 18 forecast hours
forecast_metadata = []

for fxx in range(0, 19): # 0 to 18
    print(f"Processing Forecast Hour: {fxx:02d}")
    
    try:
        H = Herbie(date=now, model='hrrr', product='subh', fxx=fxx)
        # Download variables
        ds = H.xarray(":(?:CSNOW|CICEP|CFRZR|CRAIN):surface:")
        
        # Calculate Precip Type
        ptype = ds.crain * 1 + ds.cfrzr * 2 + ds.cicep * 3 + ds.csnow * 4
        
        # --- REPROJECTION LOGIC ---
        # We set up a matplotlib figure that is inherently Lat/Lon (PlateCarree)
        # This forces matplotlib to warp the Lambert data to fit a square grid
        
        fig = plt.figure(figsize=(10, 8), frameon=False)
        # This 'projection=web_crs' implies the AXIS is Lat/Lon
        ax = plt.axes(projection=web_crs) 
        
        # We want to zoom into CONUS (Continental US) to avoid huge empty files
        # (West, East, South, North)
        extent = [-125, -66, 24, 50] 
        ax.set_extent(extent, crs=web_crs)
        ax.axis('off')
        
        # Custom Colormap
        colors = [(0,0,0,0), (0,0.8,0,0.6), (1,0,0,0.6), (1,0.5,0,0.6), (0,0,1,0.6)]
        cmap = plt.matplotlib.colors.ListedColormap(colors)
        
        # Plot! transform=hrrr_crs tells mpl the DATA is in Lambert
        # The axis is in PlateCarree, so it reprojects on the fly.
        ax.pcolormesh(ds.longitude, ds.latitude, ptype.values[0], 
                      transform=web_crs, # Using web_crs because ds.lat/lon are actual lat/lon values
                      cmap=cmap, 
                      shading='nearest')
        
        # Save frame
        filename = f"overlay_{fxx:02d}.png"
        plt.savefig(f"web/{filename}", transparent=True, bbox_inches='tight', pad_inches=0, dpi=150)
        plt.close(fig)
        
        # Add to metadata list
        forecast_metadata.append({
            "hour": fxx,
            "file": filename,
            "valid_time": (now + pd.Timedelta(hours=fxx)).strftime("%Y-%m-%d %H:%M UTC")
        })

    except Exception as e:
        print(f"Failed on hour {fxx}: {e}")
        continue

# 5. Save the Master JSON
# Note: The bounds must match the 'extent' we set above!
# Leaflet format: [[South, West], [North, East]]
master_data = {
    "run_time": now.strftime("%Y-%m-%d %H:%M UTC"),
    "bounds": [[24, -125], [50, -66]], 
    "forecasts": forecast_metadata
}

with open("web/data.json", "w") as f:
    json.dump(master_data, f)
