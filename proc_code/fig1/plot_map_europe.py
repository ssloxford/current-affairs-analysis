import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.colors import ListedColormap, LinearSegmentedColormap, BoundaryNorm
from shapely.geometry import Polygon, mapping

# https://ec.europa.eu/eurostat/web/gisco/geodata/reference-data/administrative-units-statistical-units/countries

# Set the default font family to Times New Roman
plt.rc('font', family='Times New Roman')

def linestring_to_polygon(fili_shps):
    print(fili_shps['geometry'])
    for l in fili_shps['geometry']:
        print(l)
        print(Polygon(l))

    return fili_shps

# Read the data from the CSV
df = pd.read_csv('Data/dc_chargers_europe_september_2024_incl_population.csv')
print(df)

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

# Load the shapefile
world = gpd.read_file('ref-countries-2020-10m/CNTR_RG_10M_2020_4326.shp')
print(world['CNTR_ID'].head())

# Define the conditions and corresponding values
conditions = {'AT': 123, 'DE': 456}

# Update the column based on the conditions
for index, row in df.iterrows():
    code = row['CNTR_ID']
    value = row['chargers_per_100000']
    world.loc[world['CNTR_ID'] == code, 'chargers_per_100000'] = value

# These are the countries that should be plotted
countries_to_plot = ['United Kingdom', 'Norway', 'Iceland', 'Switzerland', 'Turkey', 'Liechtenstein', 'Germany', 'France',
                     'Italy', 'Spain', 'Netherlands', 'Belgium', 'Greece', 'Portugal',
                        'Sweden', 'Austria', 'Denmark', 'Finland', 'Poland', 'Romania', 'Czechia',
                        'Hungary', 'Ireland', 'Croatia', 'Bulgaria', 'Slovakia', 'Estonia', 'Denmark',
                        'Slovenia', 'Lithuania', 'Latvia', 'Cyprus', 'Malta', 'Luxembourg']

eu_and_selected = world
print(eu_and_selected.head())

num_countries = len(countries_to_plot)
colors = [(1, 1, 1), (0, 0.129, 0.278)]  # white to #002147
cmap = LinearSegmentedColormap.from_list('custom', colors)

# Plot the map
world.plot(column='chargers_per_100000', cmap=cmap, legend=True, edgecolors='#002147', linewidths=0.3, legend_kwds={"label": "", "orientation": "horizontal","fraction":0.044, "pad":-0.06}, figsize=(5,4.7))

#plt.axis('equal')
plt.ylim((31, 71.5))
plt.xlim((-11, 45))
plt.gca().set_aspect(1.3)

plt.subplots_adjust(left=0, right=1, top=1, bottom=0.06)

# Customize the plot if needed
plt.axis('off')

#plt.tight_layout()

# Save the figure to a PDF file.
# This need post-processing to put it in the correct aspect ratio etc.
plt.savefig('map_europe_september_2024.pdf', bbox_inches='tight')
#Number of DC Charging Stations per 100,000 People
plt.show()
