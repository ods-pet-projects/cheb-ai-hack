from collections import defaultdict
import numpy as np
import pandas as pd
import geopandas as gpd

from helpers import prepare_address, geocode_address, filter_df_by_bbox


def upload_file(file_content, file_ext, data_type, metrics_data):
    possible_separators = [',', '|', ';']
    data_df = None
    is_geo = False

    if file_ext == 'csv':
        for sep in possible_separators:
            data_df = pd.read_csv(file_content, sep=sep)
            if len(data_df.columns) > 1:
                break

    elif file_ext == 'xlsx':
        for sep in possible_separators:
            data_df = pd.read_excel(file_content, sep=sep)
            if len(data_df.columns) > 1:
                break

    elif file_ext == 'geojson':
        is_geo = True
        data_df = gpd.read_file(file_content)

    else:
        raise Exception('Unsupported extenstion {}'.format(file_ext))

    if is_geo:
        metrics_data.load_new_custom_geometry(data_df)
    else:
        load_data_df(data_df, data_type, metrics_data)


def load_data_df(data_df, data_type, metrics_data):
    if len(data_df) == 0:
        return

    data_df = try_set_geo_fields(data_df)
    metrics_data.load_by_data_type(data_df, data_type)


def try_set_geo_fields(data_df):
    lon = find_df_column_values(data_df, {'lon', 'longitude', 'долгота'})
    lat = find_df_column_values(data_df, {'lat', 'latitude', 'широта'})
    if len(lon) == 0 or len(lat) == 0:
        address_column = find_df_column_values(data_df, {'address', 'адрес'})
        if len(address_column) == 0:
            raise Exception('Incorrect file was uploaded')

        data_df[['lat', 'lon']] = address_column.apply(get_latlon)

    data_df = data_df[~pd.isna(data_df['lat'])]
    data_df = filter_df_by_bbox(data_df)

    return data_df


def find_df_column_values(df, defined_columns):
    for column in df.columns:
        if column.lower() in defined_columns:
            return df[column]

    return []


def get_latlon(address):
    address = prepare_address(address)
    latlng = geocode_address(address)

    if latlng is not None and len(latlng) == 2:
        return pd.Series({'lat': latlng[0], 'lon': latlng[1]})

    return pd.Series({'lat': np.nan, 'lon': np.nan})
