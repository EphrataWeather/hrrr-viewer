from herbie import Herbie
import matplotlib.pyplot as plt
import numpy as np
import os
import json

# Create web directory if it doesn't exist
os.makedirs("web", exist_ok=True)

# 1. Pull the latest sub-hourly HRRR data from AWS
# 'subh' is the sub-hourly model
H = Herbie(model='hrrr', product='subh', fxx=0) 

# 2. Download and Subset (looking for categorical precip types)
# This pulls only the variables we need to keep the GitHub runner fast
ds = H.xarray(":(?:CSNOW|CICEP|CFRZR|CRAIN):surface:")

# 3. Process Precip Type
# Logic: Snow=4, Sleet=3, FrzRain=2, Rain=1
ptype = ds.crain * 1 + ds.cfrzr * 2 + ds.cicep * 3 + ds.csnow * 4

# 4. Generate the Image
colors = [(0,0,0,0), (0,0.8,0,0.6), (1,0,0,0.6), (1,0.5,0,0.6), (0,0,1,0.6)]
cmap = plt.matplotlib.colors.ListedColormap(colors)

fig = plt.figure(frameon=False, figsize=(12, 8))
ax = plt.Axes(fig, [0., 0., 1., 1.])
ax.set_axis_off()
fig.add_axes(ax)

# Display data
ax.imshow(ptype.values[0], cmap=cmap, aspect='auto', interpolation='nearest')
plt.savefig("web/overlay.png", transparent=True, dpi=300)

# 5. Save Bounds for Leaflet
# HRRR uses a Lambert Conformal projection, we extract the lat/lon corners
bounds = [
    [float(ds.latitude.min()), float(ds.longitude.min())],
    [float(ds.latitude.max()), float(ds.longitude.max())]
]
with open("web/bounds.json", "w") as f:
    json.dump(bounds, f)

print("Map updated successfully.")
