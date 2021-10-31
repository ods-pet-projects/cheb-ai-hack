
# coding: utf-8

# ## Data exploration and aggregation

# In[115]:


"""
1. Отображаем знания о реформе жкх
2. Парсим данные по гео / спорт площдкам
"""


# In[116]:


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


# In[213]:


def geocode_address(address):
    return geocoder.osm(address).latlng

def get_latlon(address):
    address = address.strip().lower().replace('республика', '').replace('респ', '').replace('.', '').replace(',', '').replace('чувашия', '').replace('чувашская', '').replace('чебоксары', '').replace('г ', '').strip()
    address = address.replace('ул ', 'улица ')
    address = address.replace('пр-кт ', 'проспект ')
    address = address.replace('б-р ', 'бульвар ')
    address = address.split(' к ')[0]
    address += " Чебоксары"
    latlng = geocode_address(address)
    if latlng is not None and len(latlng) == 2:
        return pd.Series({'lat': latlng[0], 'lon': latlng[1], 'address': address})
    
    return pd.Series({'lat': np.nan, 'lon': np.nan, 'address': address})


# In[214]:



def geocode_df(df, address_column):
    df[['lat', 'lon', address_column]] = df[address_column].progress_apply(get_latlon)

    cnt_before = len(df)
#     success_geocoded_df = df[~pd.isna(df['lat'])]
#     df = success_geocoded_df
#     df['point'] = df.apply(lambda row: Point(row['lon'], row['lat']), axis=1)
#     gdf_data = gpd.GeoDataFrame(df, geometry='point')
#     gdf_data.set_crs(epsg=4326, inplace=True)
    return df


# In[215]:


reforma_df = pd.read_excel('./parsing_data/cheb_HACKS_AI__reformagkh_full.xlsx')
print(len(reforma_df))
reforma_df = reforma_df[~pd.isna(reforma_df['Численность жителей, чел.'])]
reforma_df = reforma_df[reforma_df['Численность жителей, чел.'] != 'Нет']


reforma_df['Численность жителей, чел.'] = reforma_df['Численность жителей, чел.'].astype(int)
reforma_df['Численность жителей, чел.'].sum()


# In[216]:


reforma_df = geocode_df(reforma_df, 'Адрес дома')

reforma_df.to_csv('./pointed_data/reforma.csv', index=None)
reforma_df.head()

# reforma_df[~pd.isna(reforma_df['lat'])]


# In[221]:


reforma_df[~pd.isna(reforma_df['lat'])]['Численность жителей, чел.'].sum()


# ## Обработка 2gis данных

# In[160]:


two_gis_df = pd.read_excel('./parsing_data/cheb_HACKS_AI__2gis_full_(all).xlsx')


# In[194]:


clean_df = two_gis_df[two_gis_df.text.str.contains('°')]
clean_df


# In[206]:


import re
print(r1)

def find_latlon(text):
    r1 = re.findall(r"[\d.]+", text)
    return pd.Series({'lat': r1[0], 'lon': r1[1]})


clean_df = two_gis_df[two_gis_df.text.str.contains('°')]
clean_df
clean_df[['lat', 'lon']] = clean_df.apply(lambda row: find_latlon(row['text']), axis=1)


def convert_type(row):
    request_text = row['request_text']
    mapping = {
        'чебоксары парки': 'парк',
        'Декоративное сооружение чебоксары': 'декоративное сооружение',
        'чебоксары спортивная площадка': 'спортивная площадка',
    }
    return mapping[request_text]

    
clean_df['request_text'] = clean_df.apply(lambda x: convert_type(x), axis=1)
clean_df = clean_df[clean_df.lon != '.']
clean_df = clean_df[clean_df.lat != '.']
clean_df.lon = clean_df.lon.astype(float)
clean_df.lat = clean_df.lat.astype(float)
clean_df.head()


# In[208]:


clean_df.to_csv('./pointed_data/2gis_data_social.csv', index=None)


# In[167]:


include[['lat', 'lon']]


# In[164]:


exclude

