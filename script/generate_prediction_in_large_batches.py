import json
from tqdm import tqdm
import sys

sys.path.append('./')
from helper.global_var import FLAG_DEBUG, SAVE_TYPE_PICKLE, PREDICT_ROAD_CONDITION_CONFIG_HISTORY_DATE, \
    PREDICT_ROAD_CONDITION_CONFIG_HISTORY_DATA_RANGE, PREDICT_ROAD_CONDITION_CONFIG_WEIGHT
from pathlib import Path
from helper.helper_time_range_index_to_str import time_range_index_to_str, time_range_index_to_time_range_str
import predict_road_condition
from helper.global_var import SAVE_TYPE_PICKLE
from helper.graph_reader import graph_reader
from datetime import datetime, timedelta


def predict_speed_dict_to_json(predict_speed_dict, target_date_str, time_slot_interval, interval_idx,
                               final_way_table, way_types, way_type_avg_speed_limit,
                               save_path="cache/predict_result/{0}/{1}/{2}.json"):
    output_dict = {
        "generate_timestr": datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
        "generate_timestamp": int(datetime.today().timestamp()),
        "time_slot_interval": time_slot_interval,
        "interval_idx": interval_idx,
        "predict_time_range": "{:s}-{:s}-{:s} {}".format(target_date_str[:4], target_date_str[4:6], target_date_str[6:],
                                                         time_range_index_to_time_range_str(interval_idx,
                                                                                            interval_idx + 1,
                                                                                            time_slot_interval)),
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

    temp_filepath = Path(save_path.format(target_date_str, time_slot_interval, interval_idx))
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
    # Check input, load data and preparation
    if len(config_history_date) != len(config_weight):
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
        predict_speed_dict_to_json(predict_speed_dict, predict_time_date_str, interval, interval_idx,
                                   final_way_table, way_types, way_type_avg_speed_limit)

    return 0


if __name__ == '__main__':
    generate_way_structure_json()
    generate_prediction_in_large_batches(1596110400, interval=15)  # 2020 / 07 / 30
    generate_prediction_in_large_batches(1596196800, interval=15)  # 2020 / 07 / 31
    generate_prediction_in_large_batches(1596283200, interval=15)  # 2020 / 08 / 01

