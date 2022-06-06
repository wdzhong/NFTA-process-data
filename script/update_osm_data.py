from pathlib import Path

import requests
from tqdm import tqdm

from helper.global_var import SAVE_TYPE_PICKLE, SAVE_TYPE_JSON
from osm_interpreter import get_map_data


def update_osm_data(map_file):
    map_data_url = "https://download.geofabrik.de/north-america/us/new-york-latest.osm.pbf"
    r = requests.get(map_data_url, stream=True)
    with open(map_file, "wb") as f:
        for chunk_data in tqdm(r.iter_content(chunk_size=10240)):
            if chunk_data:
                f.write(chunk_data)


if __name__ == '__main__':
    map_file = Path("map/new-york-latest.osm.pbf")
    result_file_path = Path("graph")

    update_osm_data(map_file)
    get_map_data(map_file, result_file_path, SAVE_TYPE_PICKLE)
    get_map_data(map_file, result_file_path, SAVE_TYPE_JSON)
