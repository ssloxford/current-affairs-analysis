"""
Plot all chargers on a map of Europe
"""

import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap

from . import metadata

def plot_map():
    parks = metadata.read_charger_metadata_table().parks

    # Create a Basemap instance
    m = Basemap(
        projection='merc',
        llcrnrlat=42, urcrnrlat=57, llcrnrlon=-8, urcrnrlon=22,
        resolution='i')

    # Draw coastlines and countries
    #m.drawcoastlines(linewidth=1)
    m.drawmapboundary(fill_color='#9CD9EC')
    m.fillcontinents(color='#72B74A', lake_color='#9CD9EC')
    m.drawrivers(color='#7CB9EC')
    m.drawcountries(linewidth=1)
    #m.shadedrelief(scale=2)

    # Plot each coordinate
    for park in parks.values():
        x, y = m(park.long, park.lat)
        m.plot(x, y, 'rx', markersize=8)

def main():
    plt.figure(figsize=(12, 9))
    plot_map()
    plt.show()

if __name__ == "__main__":
    main()