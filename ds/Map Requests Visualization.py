
# coding: utf-8

# In[1]:


get_ipython().system('pip install requests shapely geopandas pandas keplergl flask flask-cors geocoder tqdm mercantile rtree pygeos')


# In[23]:


import pandas as pd
import geopandas as gpd
import geocoder

import numpy as np

from tqdm import tqdm

from tqdm.auto import tqdm
tqdm.pandas()

import json
from functools import lru_cache

# geo
import mercantile

from mercantile import xy_bounds, feature, quadkey
from shapely.geometry import shape, Point, Polygon

get_ipython().run_line_magic('reload_ext', 'autoreload')
get_ipython().run_line_magic('autoreload', '2')


# In[24]:


# Чебоксары центр

LAT = 56.1167663
LON = 47.262782


# In[25]:


@lru_cache()
def geocode_address(address):
    return geocoder.osm(address).latlng

def get_latlon(address):
    latlng = geocode_address(address)
    if latlng is not None and len(latlng) == 2:
        return pd.Series({'lat': latlng[0], 'lon': latlng[1]})
    
    return pd.Series({'lat': np.nan, 'lon': np.nan})


# In[26]:


prosiba_df = pd.read_excel('./content/Просьбы жителей по благоустройству.xlsx')
prosiba_df.head()


# In[6]:


obrash_df = pd.read_excel('./content/обращения граждан на портале народный контроль.xlsx')
obrash_df.head()


# In[30]:


def geocode_df(df):
    df[['lat', 'lon']] = df.address.progress_apply(get_latlon)

    cnt_before = len(df)
    success_geocoded_df = df[~pd.isna(df['lat'])]
    df = success_geocoded_df
    inside_cheboksari = df # df[(df.lat <= LAT + 0.5) & (LAT - 0.5 <= df.lat) & (LON - 0.5 < df.lon) & (df.lon <= LON + 0.5)]
    inside_cheboksari['point'] = inside_cheboksari.apply(lambda row: Point(row['lon'], row['lat']), axis=1)
    gdf_data = gpd.GeoDataFrame(inside_cheboksari, geometry='point')
    gdf_data.set_crs(epsg=4326, inplace=True)
#     print(f'cnt_before={cnt_before}; cnt_after={success_geocoded_df}; inside_chebo={inside_cheboksari}')
    
    return gdf_data


# In[31]:


prosiba_df['address'] = prosiba_df.progress_apply(lambda row: row['Адрес обращения'].strip() + ' ' + row['Дом'].strip() + ' Чебоксары', axis=1)
prosiba_data_gdf = geocode_df(prosiba_df)

prosiba_data_gdf.head()


# In[32]:


prosiba_data_gdf.to_file("./content/Prosba_geocoded.geojson", driver="GeoJSON")


# ## Geo preparation

# In[9]:


"""
генерируем сетку на выставленном зуме карты
"""

ZOOM = 16
bottom_lat, top_lat = LAT - 0.3, LAT + 0.3
left_lon, right_lon = LON - 0.3, LON + 0.3


start_tile = mercantile.tile(left_lon, top_lat, ZOOM)
end_tile = mercantile.tile(right_lon, bottom_lat, ZOOM)

features = []
for xi in range(start_tile.x, end_tile.x + 1):
    for yi in range(start_tile.y, end_tile.y + 1):
        tile = (xi, yi, ZOOM)
        feature_id = quadkey(tile)
        f = feature(tile, fid=feature_id)
        features.append(f)


# In[10]:


gdf = gpd.GeoDataFrame([
    {
        'id': f['id'],
         'title': f['properties']['title'],
        'geometry': shape(f['geometry']),
    }
    for i, f in enumerate(features, start=1)
])
gdf.set_crs(epsg=4326, inplace=True)


# In[11]:


prosiba_data_gdf_merged = gdf.sjoin(prosiba_data_gdf, how="inner")
prosiba_data_gdf_merged.plot()


# In[12]:


gdf.head()


# In[13]:


prosiba_data_gdf_merged.head()


# In[22]:


aggregated_gdf = prosiba_data_gdf_merged[['id']].groupby(['id']).count().reset_index()
# aggregated_gdf.plot()

aggregated_gdf
# aggregated_gdf.set_crs(epsg=4326, inplace=True)
# aggregated_gdf.geometry


# ## Vizualization

# In[15]:


from keplergl import KeplerGl
map_data = KeplerGl(height=1000, data={"prosba": aggregated_gdf})
map_data


# In[34]:


get_ipython().system('ls parsing_data/')


# In[38]:


df = pd.read_excel('./parsing_data/cheb_HACKS_AI__2gis_full_(all).xlsx')


# In[40]:


df['text'

