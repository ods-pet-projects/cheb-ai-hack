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
import json
import geocoder
import mercantile
from dataclasses import dataclass


@lru_cache()
def geocode_address(address):
    return geocoder.osm(address).latlng


def prepare_address(address):
    address = address.strip().lower().replace('республика', '').\
        replace('респ', '').replace('.', '').replace(',', '').\
        replace('чувашия', '').replace('чувашская', '').\
        replace('чебоксары', '').replace('г ', '').strip()

    address = address.replace('ул ', 'улица ')
    address = address.replace('пр-кт ', 'проспект ')
    address = address.replace('б-р ', 'бульвар ')
    address = address.split(' к ')[0]
    address += " Чебоксары"

    return address


# Координаты Чебоксар
LAT = 56.1167663
LON = 47.262782

# ббокс
left_lon = LON - 0.15
right_lon = LON + 0.15
bottom_lat = LAT - 0.05
top_lat = LAT + 0.1

def filter_df_by_bbox(df):
    return df[
        (df.lat <= top_lat) &
        (bottom_lat <= df.lat) &
        (left_lon <= df.lon) &
        (df.lon <= right_lon)
    ]



ZOOM_LEVEL = 15

def get_quad_key(lon, lat):
    tile = mercantile.tile(lon, lat, ZOOM_LEVEL)
    quad_key = mercantile.quadkey(tile)
    return quad_key
