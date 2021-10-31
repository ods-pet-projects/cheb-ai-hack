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

from utils import MapData, load_new_appeal_by_df
from metrics import Metrics
from file_uploader import upload_file

app = Flask(__name__,
    static_url_path='',
    static_folder='static',
    template_folder='templates'
)
cors = CORS(app)

layer_metrics = Metrics()


def load_config():
    with open('map_config.json', 'r') as fd:
        return json.load(fd)

@app.get('/')
def get_main_page():
    layers_result = layer_metrics.get_tile_layers()

    social_group = []
    live_group = []
    health_group = []
    description = 'Недостаточно развита социальная среда'

    if layers_result:
        weak = layers_result[-1]
        gdf = weak[1]
        for i, row in gdf.iterrows():
            if row.social_index <=row.live_index and row.social_index <= row.heath_index:
                social_group.append(row.id)
            elif row.live_index <= row.social_index and row.live_index <= row.heath_index:
                live_group.append(row.id)

            elif row.live_index <= row.social_index and row.live_index <= row.heath_index:
                health_group.append(row.id)

    context = {'social_group': social_group, 'live_group': live_group, 'health_group': health_group}

    return render_template('page.html', **context)


@app.get('/map')
def get_map_data():
    geo = KeplerGl(height=1000, data={}, show_docs=False, config=load_config())

    layers_result = layer_metrics.get_tile_layers()
    for layer_name, gdf in layers_result:
        geo.add_data(data=gdf, name=layer_name)

    return geo._repr_html_()


@app.post('/upload')
def upload_new_appeals():
    uploaded_file = request.files.get('file')
    data_type = request.form['data_type']
    file_ext = uploaded_file.filename.split('.')[-1]
    file_content = StringIO(uploaded_file.stream.read().decode())
    try:
        upload_file(file_content, file_ext, data_type, layer_metrics)
    except Exception as exp:
        print(exp)

    return redirect('/')
    # return render_template('page.html')




if __name__ == '__main__':
    app.run(port=5051)
