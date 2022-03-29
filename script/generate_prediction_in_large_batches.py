import json
import os
import shutil
import sys
import time

from tqdm import tqdm

sys.path.append('./')
from helper.global_var import FLAG_DEBUG, PREDICT_ROAD_CONDITION_CONFIG_HISTORY_DATE, \
    PREDICT_ROAD_CONDITION_CONFIG_HISTORY_DATA_RANGE, PREDICT_ROAD_CONDITION_CONFIG_WEIGHT, GPILB_CACHE_PATH
from pathlib import Path
from helper.helper_time_range_index_to_str import time_range_index_to_time_range_str
import predict_road_condition
from helper.global_var import SAVE_TYPE_PICKLE
from helper.graph_reader import graph_reader
from datetime import datetime, timedelta


def get_output_dict(predict_speed_dict, predict_time, time_slot_interval, interval_idx,
                    final_node_table, final_way_table, way_types, way_type_avg_speed_limit):

    output_dict = {
        "boundaries": {
            "lat1": 42.233307124,  # Hard code boundaries for now
            "lon1": -78.835716683,
            "lat2": 43.15842251,
            "lon2": -78.76853003
        },
        "date": datetime.today().strftime('%m/%d/%Y'),
        "time": datetime.today().strftime('%I:%M:%S %p'),
        "timestamp": int(datetime.today().timestamp()),
        "time_slot_interval": time_slot_interval,
        "interval_idx": interval_idx,
        "predict_time_range": "{:0>4d}-{:0>2d}-{:0>2d} {}".format(predict_time.year, predict_time.month,
                                                                  predict_time.day,
                                                                  time_range_index_to_time_range_str(interval_idx,
                                                                                                     interval_idx + 1,
                                                                                                     time_slot_interval)
                                                                  ),
        "links": []
    }

    for way_id, single_road_speed in predict_speed_dict.items():
        speed_limit = way_type_avg_speed_limit[way_types.get(way_id, "unclassified")]
        if speed_limit > 0:
            speed_ratio = single_road_speed / speed_limit
        else:
            speed_ratio = 1.0

        if way_id not in final_way_table:
            continue

        way_dict = {
            "status": road_condition_to_color(speed_ratio),
            "points": get_node_list(way_id, final_way_table, final_node_table)
        }

        output_dict["links"].append(way_dict)
    return output_dict


def get_output_dict_old(predict_speed_dict, predict_time, time_slot_interval, interval_idx,
                        final_way_table, way_types, way_type_avg_speed_limit):

    output_dict = {
        "generate_timestr": datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
        "generate_timestamp": int(datetime.today().timestamp()),
        "time_slot_interval": time_slot_interval,
        "interval_idx": interval_idx,
        "predict_time_range": "{:0>4d}-{:0>2d}-{:0>2d} {}".format(predict_time.year, predict_time.month,
                                                                  predict_time.day,
                                                                  time_range_index_to_time_range_str(interval_idx,
                                                                                                     interval_idx + 1,
                                                                                                     time_slot_interval)
                                                                  ),
        "road_speed": {}
    }
    for way, single_road_speed in predict_speed_dict.items():
        speed_limit = way_type_avg_speed_limit[way_types.get(way, "unclassified")]
        if speed_limit > 0:
            speed_ratio = single_road_speed / speed_limit
        else:
            speed_ratio = 1.0
        if way in final_way_table:
            way_dict = {
                "speed": round(single_road_speed, 2),
                "speed_ratio": round(speed_ratio, 2)
            }

            output_dict["road_speed"][way] = way_dict
    return output_dict


def get_output_dict_with_less_parameter(predict_speed_dict, target_dt, time_slot_interval):
    save_filename_list = ["way_types", "way_type_avg_speed_limit", "final_way_table", "final_node_table"]
    temp_map_dates = graph_reader(Path("graph/"), SAVE_TYPE_PICKLE, save_filename_list)
    way_types = temp_map_dates[0]
    way_type_avg_speed_limit = temp_map_dates[1]
    final_way_table = temp_map_dates[2]
    final_node_table = temp_map_dates[3]

    interval_idx = (target_dt.hour * 60 + target_dt.minute) // time_slot_interval

    return get_output_dict(predict_speed_dict, target_dt, time_slot_interval, interval_idx,final_node_table,
                           final_way_table, way_types, way_type_avg_speed_limit)


def predict_speed_dict_to_json(predict_speed_dict, predict_time, time_slot_interval, interval_idx,
                               final_node_table, final_way_table, way_types, way_type_avg_speed_limit,
                               save_path=GPILB_CACHE_PATH):
    """
    Get the predict speed dict and save it into a file in JSON format

    Parameters
    ----------
    predict_speed_dict: Dictionary
        Return of predict_road_condition.compute_speed_dict()
        A dictionary that use way_id as key and the predict bus speed on that road at the given time as value.
        When there is an error, it will return a dictionary with key "Error" and the detail of the error as the value

    predict_time: datetime
        Time of predict in datetime format

    time_slot_interval:Int
        The length of each time interval in minutes. The input number should be divisible by 1440 (24 hour * 60 min)
        by default it is 5 min.

    interval_idx: Int
        The index of the period of the predict_timestamp in predict_road_condition

    final_node_table: Dict
        A dictionary that stored the node id and the latitude/longitude coordinates as a key value pair.

    final_way_table: Dict
        A dictionary that stored the way id and a list of node id's as a key value pair.

    way_types: Dictionary
        A dictionary that use way_id as key and the type of the way as the value

    way_type_avg_speed_limit: Dictionary
        A dictionary that use way_type as key and the average speed limit of that type of way as the value

    save_path: String
        path where the json file save
        {0} is a 8-digit date_str in yyyyMMdd format.
        {1} is the value of interval
        {2} is the interval_idx
        by default it will use the project's file format.

    Returns
    -------
    None
    """
    output_dict = get_output_dict(predict_speed_dict, predict_time, time_slot_interval, interval_idx,
                                  final_node_table, final_way_table, way_types, way_type_avg_speed_limit)
    temp_filepath = Path(save_path.format(predict_time.strftime("%Y%m%d"), time_slot_interval, interval_idx))
    temp_filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(temp_filepath, 'w') as f:
        # json.dump(output_dict, f, indent=2)
        json.dump(output_dict, f)
    return 0


def generate_way_structure_json(save_path="static/mapdata/way_structure.json"):
    save_filename_list = ["final_node_table", "final_way_table"]
    temp_map_dates = graph_reader(Path("graph/"), SAVE_TYPE_PICKLE, save_filename_list)
    final_node_table = temp_map_dates[0]
    final_way_table = temp_map_dates[1]
    way_structure = {}
    for way, waypoints in final_way_table.items():
        points = []
        for waypoint in waypoints:
            points.append([final_node_table[waypoint][0], final_node_table[waypoint][1]])
        way_structure[way] = points

    temp_filepath = Path(save_path)
    temp_filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(temp_filepath, 'w') as f:
        # json.dump(output_dict, f, indent=2)
        json.dump(way_structure, f)
    return 0


def generate_prediction_in_large_batches(predict_timestamp=int(datetime.now().timestamp()), interval=5,
                                         result_file_path="data/{0}/result/{0}_{1}_min_road.csv",
                                         config_history_date=PREDICT_ROAD_CONDITION_CONFIG_HISTORY_DATE,
                                         config_history_data_range=PREDICT_ROAD_CONDITION_CONFIG_HISTORY_DATA_RANGE,
                                         config_weight=PREDICT_ROAD_CONDITION_CONFIG_WEIGHT):
    """
    Generate prediction in large batches (in day(s))

    predict_timestamp: int (timestamp)
        10-digit timestamp, use current time if not provided
        This timestamp will be use to get the date ONLY

    interval: int
        The length of each time interval in minutes. The input number should be divisible by 1440 (24 hour * 60 min)
        by default it is 5 min.

    config_history_date: List of int
        This parameter specifies which historical days of data the function needs to use in the computation. It should
        be a List of int, where each int means the offset of the day that need predict. e.g. -1 means yesterday
        by default it will use a predetermined configuration

    config_history_data_range: List of int
        This parameter specifies the range and the order of using the nearby data to replace the missing data. If the
        value is [-1, 1] and if the data we are looking for located on the ith index is missing. We will try to use the
        value at i-1 or i+1 as the data located in ith index.
        by default it will use a predetermined configuration

    config_weight: List of float
        This parameter specifies the weight of each day's data when compute the weighted sum.
        by default it will use a predetermined configuration

    Returns
    -------
    None

    """
    # Check input, load data and preparation
    if len(config_history_date) != len(config_weight):
        print("error: len(config_history_date) != len(config_weight)")
        return -1

    save_filename_list = ["way_graph", "way_types", "way_type_avg_speed_limit", "final_node_table", "final_way_table"]
    temp_map_dates = graph_reader(Path("graph/"), SAVE_TYPE_PICKLE, save_filename_list)
    way_graph = temp_map_dates[0]
    way_types = temp_map_dates[1]
    way_type_avg_speed_limit = temp_map_dates[2]
    final_node_table = temp_map_dates[3]
    final_way_table = temp_map_dates[4]

    # Find the time of the predict, also find the range index in the day.
    predict_time = datetime.fromtimestamp(predict_timestamp)
    predict_time_date_str = predict_time.strftime("%Y%m%d")

    # Prepare of load history data
    history_data_date_str = []
    for offset in config_history_date:
        history_data_date_str.append((predict_time + timedelta(days=offset)).strftime("%Y%m%d"))

    if FLAG_DEBUG:
        print("Predict time: {}".format(predict_time.strftime("%Y-%m-%d %H:%M:%S")))
        print("History data date_str:{}".format(history_data_date_str))

    # Load history data
    history_speed_matrix_list, config_weight = \
        predict_road_condition.get_history_speed_matrix_list(history_data_date_str, config_weight, interval,
                                                             result_file_path)

    if len(history_speed_matrix_list) == 0:
        print({"Error": "No enough data for predict"})
        return {"Error": "No enough data for predict"}

    if FLAG_DEBUG:
        print("{} day(s) load".format(len(history_speed_matrix_list)))

    full_way_id_set, usable_way_id_set = predict_road_condition.get_way_id_set(history_speed_matrix_list)

    for interval_idx in tqdm(range(int(1440 / interval))):
        # print(interval_idx, time_range_index_to_str(interval_idx, interval))
        predict_speed_dict = \
            predict_road_condition.compute_speed_dict(interval, interval_idx, history_speed_matrix_list,
                                                      full_way_id_set,
                                                      usable_way_id_set, config_history_data_range, config_weight,
                                                      way_graph, way_types, way_type_avg_speed_limit)
        predict_speed_dict_to_json(predict_speed_dict, predict_time, interval, interval_idx,
                                   final_node_table, final_way_table, way_types, way_type_avg_speed_limit)

    return 0


def clean_old_files(day_before_clean=7, cache_root="cache/predict_result"):
    cache_root = Path(cache_root)
    current_time = datetime.now()
    for name in os.listdir(cache_root):
        full_path = cache_root / name
        if os.path.isdir(full_path):
            if len(name) >= 8:
                date_of_folder = datetime(int(name[0:4]), int(name[4:6]), int(name[6:8]))
                if (current_time - date_of_folder).days > day_before_clean:
                    print("Delete {} due to it is {} day(s) before today".format(full_path, day_before_clean))
                    shutil.rmtree(full_path)


def road_condition_to_color(speed_ratio):
    if speed_ratio < 0.1:
        return "#b52f3b"
    elif speed_ratio < 0.2:
        return "#da8015"
    elif speed_ratio < 0.3:
        return "#f2b021"
    elif speed_ratio < 0.4:
        return "#e5ce72"
    elif speed_ratio < 0.5:
        return "#b9cb67"
    else:
        return "#34eb95"


def get_node_list(way_id, final_way_table, final_node_table):
    if way_id not in final_way_table:
        return []

    result = []
    for node_id in final_way_table[way_id]:
        if node_id not in final_node_table:
            continue
        result.append(final_node_table[node_id])
    return result


if __name__ == '__main__':
    if len(sys.argv) < 1:
        print("Usage:")
        print("./script/generate_prediction_in_large_batches.py [timestamp]")
        print("")
        print("Optional:")
        print("timestamp  : 10-digit timestamp, use current time if not provided")
        exit(0)
    if len(sys.argv) >= 2:
        current_timestamp = int(sys.argv[1])
    else:
        current_timestamp = int(datetime.now().timestamp())

    clean_old_files()
    current_timestamp = 1643010848

    day_offsets = [0, 1, 2, 3, 4, 5, 6, 7]
    start = time.process_time()
    for day_offset in day_offsets:
        timestamp = current_timestamp + (day_offset * 86400)  # 24 hour * 60 min * 60 sec = 86400 s = 1 day
        generate_prediction_in_large_batches(timestamp, interval=15)
    if FLAG_DEBUG:
        print("[Debug] Total runtime is %.3f s" % (time.process_time() - start))

    # generate_way_structure_json()
    # generate_prediction_in_large_batches(1596110400, interval=15)  # 2020 / 07 / 30
    # generate_prediction_in_large_batches(1596196800, interval=15)  # 2020 / 07 / 31
    # generate_prediction_in_large_batches(1596283200, interval=15)  # 2020 / 08 / 01
