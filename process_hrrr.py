import xarray as xr
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

def get_precip_type_overlay():
    # 1. Load sub-hourly data (Example: F00 hour, sub-hourly slice)
    # Variable names: CSNOW (Snow), CICEP (Ice Pellets), CFRZR (Frz Rain), CRAIN (Rain)
    ds = xr.open_dataset("hrrr_data.grib2", engine="cfgrib", 
                         filter_by_attrs={'shortName': ['csnow', 'cicep', 'cfrzr', 'crain']})

    # 2. Combine into a single 'Type' array (Rain=1, FrzRain=2, IcePellets=3, Snow=4)
    ptype = ds.crain * 1 + ds.cfrzr * 2 + ds.cicep * 3 + ds.csnow * 4
    
    # 3. Create a Custom Colormap
    # 0: Transparent, 1: Green (Rain), 2: Red (FrzRain), 3: Orange (Sleet), 4: Blue (Snow)
    colors = [(0,0,0,0), (0,0.8,0,0.6), (1,0,0,0.6), (1,0.5,0,0.6), (0,0,1,0.6)]
    cmap = plt.matplotlib.colors.ListedColormap(colors)

    # 4. Plot and Save as PNG
    fig = plt.figure(frameon=False, figsize=(10, 6))
    ax = plt.Axes(fig, [0., 0., 1., 1.])
    ax.set_axis_off()
    fig.add_axes(ax)
    
    # Use 'nearest' to keep the categorical blocks sharp
    ax.imshow(ptype.values, cmap=cmap, aspect='auto', interpolation='nearest')
    
    plt.savefig("web/overlay.png", transparent=True, dpi=300)
    
    # 5. Export Bounds (Leaflet needs these to stretch the image correctly)
    bounds = [[ds.latitude.min().item(), ds.longitude.min().item()], 
              [ds.latitude.max().item(), ds.longitude.max().item()]]
    with open("web/bounds.json", "w") as f:
        import json
        json.dump(bounds, f)

if __name__ == "__main__":
    get_precip_type_overlay()
