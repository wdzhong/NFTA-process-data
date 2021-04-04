import json
import os
import shutil
import sys
import time

from tqdm import tqdm

sys.path.append('./')
from helper.global_var import FLAG_DEBUG, PREDICT_ROAD_CONDITION_CONFIG_HISTORY_DATE, \
    PREDICT_ROAD_CONDITION_CONFIG_HISTORY_DATA_RANGE, PREDICT_ROAD_CONDITION_CONFIG_WEIGHT
from pathlib import Path
from helper.helper_time_range_index_to_str import time_range_index_to_time_range_str
import predict_road_condition
from helper.global_var import SAVE_TYPE_PICKLE
from helper.graph_reader import graph_reader
from datetime import datetime, timedelta


def get_output_dict(predict_speed_dict, predict_time, time_slot_interval, interval_idx,
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
    save_filename_list = ["way_types", "way_type_avg_speed_limit", "final_way_table"]
    temp_map_dates = graph_reader(Path("graph/"), SAVE_TYPE_PICKLE, save_filename_list)
    way_types = temp_map_dates[0]
    way_type_avg_speed_limit = temp_map_dates[1]
    final_way_table = temp_map_dates[2]

    interval_idx = (target_dt.hour * 60 + target_dt.minute) // time_slot_interval

    return get_output_dict(predict_speed_dict, target_dt, time_slot_interval, interval_idx, final_way_table,
                           way_types, way_type_avg_speed_limit)


def predict_speed_dict_to_json(predict_speed_dict, predict_time, time_slot_interval, interval_idx,
                               final_way_table, way_types, way_type_avg_speed_limit,
                               save_path="cache/predict_result/{0}/{1}/{2}.json"):
    """
    TODO:
    """
    output_dict = get_output_dict(predict_speed_dict, predict_time, time_slot_interval, interval_idx,
                                  final_way_table, way_types, way_type_avg_speed_limit)
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
    TODO:
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
                                   final_way_table, way_types, way_type_avg_speed_limit)

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

    day_offsets = [0, 1, 2, 3, 4, 5, 6, 7]
    start = time.process_time()
    for day_offset in day_offsets:
        timestamp = current_timestamp + (day_offset * 86400)  # 24 hour * 60 min * 60 sec = 86400 s = 1 day
        generate_prediction_in_large_batches(timestamp, interval=15)
    if FLAG_DEBUG:
        print("[Debug] Total runtime is %.3f s" % (time.process_time() - start))

    generate_way_structure_json()
    # generate_prediction_in_large_batches(1596110400, interval=15)  # 2020 / 07 / 30
    # generate_prediction_in_large_batches(1596196800, interval=15)  # 2020 / 07 / 31
    # generate_prediction_in_large_batches(1596283200, interval=15)  # 2020 / 08 / 01
