import bisect
import enum

import mercantile
import geopandas as gpd

from collections import defaultdict
from helpers import get_quad_key
from shapely.geometry import shape



class Metrics:
    def __init__(self) -> None:
        self.tiles_info = defaultdict(lambda: defaultdict(int))
        self.tiles_geometry = {}
        self.all_food_places = 0

        self.custom_geometries = []

    def load_new_custom_geometry(self, data_df):
        self.custom_geometries.append(data_df)

    def load_by_data_type(self, data_df, data_type):
        if data_type == 'people':
            self.load_people_df(data_df)
        elif data_type == 'green':
            self.load_green_df(data_df)
        elif data_type == 'social':
            self.load_social_df(data_df)
        elif data_type == 'commercial':
            self.load_commercial_df(data_df)
        elif data_type == 'appeals':
            self.load_appeals_df(data_df)

    def load_people_df(self, df):
        for _, row in df.iterrows():
            lon, lat = row['lon'], row['lat']
            quad_key = get_quad_key(lon, lat)

            self.tiles_info[quad_key]['численность жителей'] += row['Численность жителей, чел.']
            self.tiles_info[quad_key]['количество зданий младше 2000 года'] += 1 if row['Год ввода дома в эксплуатацию'] > 2000 else 0
            self.tiles_info[quad_key]['количество зданий'] += 1

    def load_social_df(self, df):
        for _, row in df.iterrows():
            lon, lat = row['lon'], row['lat']
            quad_key = get_quad_key(lon, lat)
            self.tiles_info[quad_key][row['request_text']] += 1

    def load_commercial_df(self, df):
        self.all_food_places = 0

        for _, row in df.iterrows():
            lon, lat = row['lon'], row['lat']
            quad_key = get_quad_key(lon, lat)

            if row.amenity == 'fountain': # TODO less specific
                self.tiles_info[quad_key]['количество фонтанов'] += 1
            elif row.amenity == 'toilets':
                self.tiles_info[quad_key]['количество туалетов'] += 1
            else:
                self.tiles_info[quad_key]['количество общепит мест'] += 1
                self.all_food_places += 1

    def load_green_df(self, df):
        for _, row in df.iterrows():
            lon, lat = row['lon'], row['lat']
            quad_key = get_quad_key(lon, lat)
            key = "Индекс озеленения"
            self.tiles_info[quad_key][key] = row['green_index']

    def load_appeals_df(self, df):
        for _, row in df.iterrows():
            lon, lat = row['lon'], row['lat']
            quad_key = get_quad_key(lon, lat)
            key = "Обращение " + row['category']
            all_key = 'Обращение'
            self.tiles_info[quad_key][key] += 1
            self.tiles_info[quad_key][all_key] += 1

    def calculate_indexes(self):
        all_indexes = []
        for quad_key, props in self.tiles_info.items():
            # social_index
            social_index = 0
            social_value = 100 / 4
            if props.get('парк', 0) > 0:
                social_index += social_value

            if props.get('спортивная площадка', 0) > 0:
                social_index += social_value

            if props.get('декоративное сооружение', 0) > 0:
                social_index += social_value

            if props.get('количество общепит мест', 0) > 0 and self.all_food_places > 0:
                social_index += (props['количество общепит мест'] / self.all_food_places) * social_value

            # live index
            live_index = 0
            live_value = 100 / 2
            # процентное соотношение граждан проживающих +
            # процент недовольных людей чем-либо
            if props.get('численность жителей', 0) > 0:
                live_index += (1 - props.get('Обращение', 0) / props.get('численность жителей', 1)) * live_value

            # TODO вычесть обращения по кап ремонту
            if props.get('количество зданий', 0) > 0:
                live_index += (props['количество зданий младше 2000 года'] / props['количество зданий']) * live_value

            # heath_index
            heath_index = props['Индекс озеленения'] * 100
            if props.get('Индекс озеленения', 0) > 0:
                heath_index += 100 * props.get('Индекс озеленения', 0)

            # xy zoom
            index = social_index + live_index + heath_index

            props['index'] = index
            props['social_index'] = social_index
            props['live_index'] = live_index
            props['heath_index'] = heath_index

            all_indexes.append(index)

        all_indexes.sort()

        for quad_key, props in self.tiles_info.items():
            index = props['index']
            props['rank'] = (bisect.bisect_right(all_indexes, index) / len(all_indexes) * 100) // 20

    def get_tile_layers(self):
        if len(self.tiles_info) == 0:
            return []

        self.calculate_indexes()

        features = []

        for quad_key, props in self.tiles_info.items():
            feature = self.tiles_geometry.get(quad_key)
            if feature is None:
                tile = mercantile.quadkey_to_tile(quad_key)
                feature = mercantile.feature(tile)
                feature['properties'].pop('title', None)
                feature['geometry'] = shape(feature['geometry'])
                self.tiles_geometry[quad_key] = feature

            feature['properties'].update(props)
            features.append(feature)

        layers = [
            ('комплексный индекс', ('rank', 'index', 'social_index', 'live_index', 'heath_index')),
            ('социальный фактор', ('спортивная площадка', 'парк', 'декоративное сооружение', 'количество общепит мест')),
            ('факторы для проживания', ('численность жителей', 'количество зданий младше 2000 года', 'количество зданий', 'Обращение')),
            ('факторы здоровья', ('Индекс озеленения',)),
        ]

        layers_result = []
        for layer_name, property_columns in layers:
            layer_data = []

            for feature in features:
                properties = {
                    'id': feature['id'],
                    'geometry': feature['geometry'],
                }
                for property_column in property_columns:
                    properties[property_column] = feature['properties'].get(property_column, 0)

                layer_data.append(properties)

            gdf = gpd.GeoDataFrame(layer_data)
            gdf.fillna(0, inplace=True)

            layers_result.append((layer_name, gdf))

        for i, custom_geometry in enumerate(self.custom_geometries, start=1):
            layers_result.append((f"custom layer {i}", custom_geometry))

        weak_layer = self.get_possible_n_lowest_places()
        layers_result.append(weak_layer)

        return layers_result

    def get_possible_n_lowest_places(self):
        N = 10

        weak_places = sorted(self.tiles_info.items(), key=sort_dict)
        weak_places = weak_places[:N]

        weak_layers = [
            ('рекомендации на рассмотрение', ('rank', 'index', 'social_index', 'live_index', 'heath_index')),
        ]
        features = []
        for (quad_key, props) in weak_places:
            feature = self.tiles_geometry[quad_key]
            features.append(feature)

        weak_layers_result = []
        for layer_name, property_columns in weak_layers:
            layer_data = []

            for feature in features:
                properties = {
                    'id': feature['id'],
                    'geometry': feature['geometry'],
                }
                for property_column in property_columns:
                    properties[property_column] = feature['properties'].get(property_column, 0)

                layer_data.append(properties)

            gdf = gpd.GeoDataFrame(layer_data)
            gdf.fillna(0, inplace=True)

            weak_layers_result.append((layer_name, gdf))

        return weak_layers_result[0]


def sort_dict(row):
    _, props = row
    return props['index'], props['live_index'], props['heath_index'], props['social_index']
