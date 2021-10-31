from collections import defaultdict
from flask import Flask, render_template, request, redirect
from flask import Flask

from flask_cors  import CORS
from numpy import add


import pandas as pd
import geopandas as gpd

from io import StringIO
from keplergl import KeplerGl

from shapely.geometry import shape
from random import randint


from functools import lru_cache
import geocoder
import mercantile

ZOOM_LEVEL = 15

def load_new_appeal_by_df(map_data, df):
    if len(df) == 0:
        return

    lon = find_df_column_values(df, ['lon'])
    lat = find_df_column_values(df, ['lat'])
    if len(lon) == 0 or len(lat) == 0:
        address = find_df_column_values(df, ['address'])
        if len(address) == 0:
            raise Exception('Incorrect file was uploaded')

        df[['lat', 'lon']] = address.apply(get_latlon)
        df = df[~pd.isna(df['lat'])]
        # filter inside Cheboksari

    map_data.add_new_appeals(df)


class MapData:
    def __init__(self):
        self.tiles_info = defaultdict(lambda: defaultdict(int)) # quadkey -> category -> count
        self.tiles_geometry = {}
        self.custom_geometry = None

    def load_custom_geometry(self, gdf):
        self.custom_geometry = gdf # TODO append

    def add_new_appeals(self, df):
        for _, row in df.iterrows():
            category = self._detect_category(row)
            lon, lat = row['lon'], row['lat']
            tile = mercantile.tile(lon, lat, ZOOM_LEVEL)
            quad_key = mercantile.quadkey(tile)

            self.tiles_info[quad_key][category] += 1

    def get_tile_features(self):
        features = []

        for quad_key, counter_by_category in self.tiles_info.items():
            feature = self.tiles_geometry.get(quad_key)
            if feature is None:
                tile = mercantile.quadkey_to_tile(quad_key)
                feature = mercantile.feature(tile)
                self.tiles_geometry[quad_key] = feature

            for category, counter in counter_by_category.items():
                feature['properties'][category] = counter

            features.append(feature)

        return features

    def _detect_category(self, row):
        return 'park'


def find_df_column_values(df, columns):
    for c in columns:
        if c in df:
            return df[c]

    return []
