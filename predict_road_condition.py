import csv
import math
import os
import queue
import sys
import time
from helper.global_var import flag_debug, save_type_pickle
from helper.graph_reader import graph_reader
from datetime import datetime, timedelta
from pathlib import Path
from helper.debug_predict_road_condition_map import show_traffic_speed


def read_speed_matrix_from_file(date_str, interval=5, result_file_path="data/{0}/result/{0}_{1}_min_road.csv"):
    """
    This function will read the csv file and return a speed matrix.

    Parameters
    ----------
    date_str: string
        8-digit string represent the date using yyyyMMdd format e.g. 20200801

    interval: int
        The length of each time interval in minutes. The input number should be divisible by 1440 (24 hour * 60 min)
        by default it is 5 min.

    result_file_path: String
        The path (also the format) to the result csv files.
        {0} is the value of date_str
        {1} is the value of interval
        by default it will use the project's file format.

    Returns
    -------
    Return a 2-D list (matrix) that represent the speed matrix.

    """
    speed_matrix = {}
    filename = result_file_path.format(date_str, interval)
    with open(filename, newline='') as f:
        next(f)  # Skip first line
        lines = csv.reader(f)
        for line in lines:
            speed_matrix[int(line[0])] = list(map(float, line[1:]))
    return speed_matrix


def reassign_weight(config_weight, history_data_missing_idx_set):
    """
    This function will reassign the weight that has no data to those day that has data. This will make sure that the
    sum of the weight are still the same.

    Parameters
    ----------
    config_weight: List of float
        This parameter specifies the weight of each day's data when compute the weighted sum.

    history_data_missing_idx_set: Set of int
        This parameter specifies the index in config_weight where the corresponding day has no data. (whole day data are
         missing)

    Returns
    -------
    Return a List of float

    """
    remain_weight = 0.0
    total_weight = 0.0

    for i in range(len(config_weight)):
        if i not in history_data_missing_idx_set:
            remain_weight += config_weight[i]
        total_weight += config_weight[i]

    new_config_weight = []

    if remain_weight != 0:
        for i in range(len(config_weight)):
            if i not in history_data_missing_idx_set:
                new_config_weight.append((config_weight[i] / remain_weight) * total_weight)

    return new_config_weight


def estimate_missing_value(temp_history_speed, temp_need_estimate_idx, config_weight):
    """
    This function will use the weight to estimate the speed where the data is missing.
    This function work the same way as reassign_weight, but this function will use weight to compute the missing data,
    and reassign_weight just reassign the weight.

    Parameters
    ----------
    temp_history_speed: List of float
        This parameter contain the data of history_speed but some value is missing and need to estimate.

    temp_need_estimate_idx: Set of int
        This parameter specifies the index in temp_history_speed where the corresponding day has no data.

    config_weight: List of float
        This parameter specifies the weight of each day's data when compute the weighted sum.

    Returns
    -------
    Return a List of float
    """
    remain_weight = 0.0
    weighted_sum = 0.0
    for i in range(len(temp_history_speed)):
        if i not in temp_need_estimate_idx:
            remain_weight += config_weight[i]
            weighted_sum += temp_history_speed[i] * config_weight[i]
    if remain_weight != 0:
        weighted_sum = weighted_sum / remain_weight
        for i in temp_need_estimate_idx:
            temp_history_speed[i] = weighted_sum * config_weight[i]
    else:
        temp_history_speed = [0] * len(temp_history_speed)
    return temp_history_speed


def compute_predict_speed(temp_history_speed, config_weight):
    """
    This is a dot product of temp_history_speed and config_weight if we think temp_history_speed and config_weight as a
    vector.

    Parameters
    ----------
    temp_history_speed: List of float
        List of float that contain the data of history_speed.

    config_weight: List of float
        This parameter specifies the weight of each day's data when compute the weighted sum.

    Returns
    -------
    float that represent the predict speed
    """
    speed = 0.0
    for i in range(len(temp_history_speed)):
        speed += temp_history_speed[i] * config_weight[i]
    return speed


def get_history_speed_matrix_list(history_data_date_str, config_weight, interval, result_file_path):
    """
    This function will read all historical day's data given in history_data_date_str and return a list of speed matrix.

    Parameters
    ----------
    history_data_date_str: List of string
        List of date_str that represent the historical days that need to be load.
        date_str: 8-digit string represent the date using yyyyMMdd format e.g. 20200801

    config_weight: List of float
        This parameter specifies the weight of each day's data when compute the weighted sum.

    interval: int
        The length of each time interval in minutes. The input number should be divisible by 1440 (24 hour * 60 min)
        by default it is 5 min.

    result_file_path: String
        The path (also the format) to the result csv files.
        {0} is the value of date_str
        {1} is the value of interval
        by default it will use the project's file format.

    Returns
    -------
    history_speed_matrix_list: List of speed matrix
        The order of the speed matrix will be the same as the history_data_date_str unless that day's data is missing.

    config_weight:
        Return a config_weight that corresponding to the history_speed_matrix_list. If the data for some day is missing,
        the config_weight will be re-compute.
    """
    history_speed_matrix_list = []
    history_data_missing_idx_list = []
    for i in range(len(history_data_date_str)):
        date_str = history_data_date_str[i]
        temp_filepath = Path(result_file_path.format(date_str, interval))
        if os.path.exists(temp_filepath):
            history_speed_matrix_list.append(read_speed_matrix_from_file(date_str))
        else:
            history_data_missing_idx_list.append(i)
            if flag_debug:
                print(date_str, " missing")

    config_weight = reassign_weight(config_weight, set(history_data_missing_idx_list))
    return history_speed_matrix_list, config_weight


def get_way_id_set(history_speed_matrix_list):
    """
    This function will give a set of all existing way and a set of way that all speed matrix has.
    This usually won't matter, but in case the speed matrix is generated using different time's map, this may cause
    two speed matrix has different way.

    Parameters
    ----------
    history_speed_matrix_list: List of speed matrix
        List of speed matrix

    Returns
    -------
    full_way_id_set: Set of way_id
        A set that contain all way that exist in history_speed_matrix_list.

    usable_way_id_set: Set of way_id
        A set that only contain the way that exist in all speed matrix in history_speed_matrix_list.
    """
    full_way_id_set = set()
    usable_way_id_set = set()
    for speed_matrix in history_speed_matrix_list:
        temp_set = set(speed_matrix.keys())
        full_way_id_set = full_way_id_set | temp_set
        if len(usable_way_id_set) <= 0:
            usable_way_id_set = temp_set
        else:
            usable_way_id_set = usable_way_id_set & temp_set

    return full_way_id_set, usable_way_id_set


def estimate_no_data_road_speed_using_BFS(predict_speed_dict, way_graph, way_types, way_type_avg_speed_limit):
    """
    This function will find a non-zero way as starting point. Use BFS to visit all ways. If a way is missing, it will
    use near by way's speed to predict it's speed.

    Parameters
    ----------
    predict_speed_dict: Dictionary
        A dictionary that use way_id as key and the predict bus speed on that road at the given time as value.

    way_graph: Graph (Dictionary)
        A graph use way_id as the node of the graph and use [OSM's node] as the edge of the graph. Use adjacency list
        to represent the graph.

    way_types: Dictionary
        A dictionary that use way_id as key and the type of the way as the value

    way_type_avg_speed_limit: Dictionary
        A dictionary that use way_type as key and the average speed limit of that type of way as the value

    Returns
    -------
    predict_speed_dict: Dictionary
        A dictionary that use way_id as key and the predict bus speed on that road at the given time as value.
    """
    bfs_start_way = 0
    for way, speed in predict_speed_dict.items():
        if speed > 0:
            bfs_start_way = way
            break

    way_motorway = {}
    for way, way_type in way_types.items():
        way_motorway[way] = "motorway" in way_type

    bfs_explored = {bfs_start_way}
    bfs_to_explore = queue.Queue()
    bfs_to_explore.put(bfs_start_way)
    while not bfs_to_explore.empty():
        bfs_current_node = bfs_to_explore.get()
        bfs_current_node_motorway = way_motorway[bfs_current_node]
        if bfs_current_node not in predict_speed_dict:
            predict_speed_dict[bfs_current_node] = 0
        node_speed = predict_speed_dict[bfs_current_node]
        if node_speed <= 0:
            temp_sample = []
            for neighbor in way_graph[bfs_current_node]:
                neighbor_speed = predict_speed_dict.get(neighbor, 0)
                if neighbor_speed > 0:
                    if bfs_current_node_motorway == way_motorway[neighbor]:
                        temp_sample.append(neighbor_speed)
                    elif bfs_current_node_motorway:
                        # Some test shows that the the bus run 4~5 times faster on motorway then normal road.
                        temp_sample.append(4.5 * neighbor_speed)
            if len(temp_sample) > 0:
                predict_speed_dict[bfs_current_node] = sum(temp_sample) / len(temp_sample)
            else:
                predict_speed_dict[bfs_current_node] = \
                    way_type_avg_speed_limit[way_types.get(bfs_current_node, "unclassified")]

        for neighbor in way_graph[bfs_current_node]:
            if neighbor not in bfs_explored:
                bfs_to_explore.put(neighbor)
                bfs_explored.add(neighbor)

    return predict_speed_dict


def predict_road_condition(predict_timestamp=int(datetime.now().timestamp()), interval=5,
                           result_file_path="data/{0}/result/{0}_{1}_min_road.csv",
                           config_history_date=None, config_history_data_range=None, config_weight=None,):
    """
    This function will reading historical data and using weighted sum calculate the bus speed on the road at the
    given time.

    Parameters
    ----------
    predict_timestamp: timestamp
        10-digit timestamp, use current time if not provided

    interval: int
        The length of each time interval in minutes. The input number should be divisible by 1440 (24 hour * 60 min)
        by default it is 5 min.

    result_file_path: String
        The path (also the format) to the result csv files.
        {0} is a 8-digit date in yyyyMMdd format.
        {1} is the value of interval
        by default it will use the project's file format.

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
    A dictionary that use way_id as key and the predict bus speed on that road at the given time as value.
    When there is an error, it will return a dictionary with key "Error" and the detail of the error as the value

    """
    # TODO: This function could be implemented using pandas and numpy (Shiluo)
    # Check input, load data and preparation
    if config_history_date is None:
        config_history_date = [-1, -2, -3, -7, -14, -21, -28, -35, -42, -49, -56, -63, -70]
    if config_history_data_range is None:
        config_history_data_range = [-1, 1, -2, 2, -3, 3, -4, 4, -5, 5, -6, 6]
    if config_weight is None:
        config_weight = [0.08821194073566006, 0.08402736745847723, 0.09180261375018595, 0.09567173256541667,
                         0.06638586102785468, 0.057538022745280304, 0.03803083890311526, 0.08628806480829161,
                         0.08805171256460817, 0.08184255395533459, 0.07774612670061147, 0.06883249115674404,
                         0.06392337112461549]
    if len(config_history_date) != len(config_weight):
        return -1

    save_filename_list = ["way_graph", "way_types", "way_type_avg_speed_limit"]
    temp_map_dates = graph_reader(Path("graph/"), save_type_pickle, save_filename_list)
    way_graph = temp_map_dates[0]
    way_types = temp_map_dates[1]
    way_type_avg_speed_limit = temp_map_dates[2]

    predict_speed_dict = {}

    # Find the time of the predict, also find the range index in the day.
    predict_time = datetime.fromtimestamp(predict_timestamp)
    # predict_time_date_str = predict_time.strftime("%Y%m%d")
    interval_idx = math.floor((predict_time.hour * 3600 + predict_time.minute * 60 + predict_time.second) /
                              (interval * 60))

    # Prepare of load history data
    history_data_date_str = []
    for offset in config_history_date:
        history_data_date_str.append((predict_time + timedelta(days=offset)).strftime("%Y%m%d"))

    if flag_debug:
        print("Predict time: {}".format(predict_time.strftime("%Y-%m-%d %H:%M:%S")))
        print("History data date:{}".format(history_data_date_str))

    # Load history data
    history_speed_matrix_list, config_weight = get_history_speed_matrix_list(history_data_date_str, config_weight,
                                                                             interval, result_file_path)

    if len(history_speed_matrix_list) == 0:
        return {"Error": "No enough data for predict"}

    if flag_debug:
        print("{} day(s) load".format(len(history_speed_matrix_list)))

    full_way_id_set, usable_way_id_set = get_way_id_set(history_speed_matrix_list)

    # iterate every way that all speed_matrix has
    for way_id in usable_way_id_set:
        temp_history_speed = []
        temp_need_estimate_idx = set()
        for speed_matrix in history_speed_matrix_list:
            temp_speed = speed_matrix[way_id][interval_idx]
            if temp_speed <= 0:

                # Use near by data as the data for the target time
                for i in config_history_data_range:
                    temp_speed = speed_matrix[way_id][interval_idx + i]
                    if temp_speed > 0:
                        break

                # # Use near by data as the data for the target time, this will ignore the config_history_data_range
                # # and check all day's dta
                # temp_min_diff = 86401
                # for i in range(len(speed_matrix[way_id])):
                #     if speed_matrix[way_id][i] > 0:
                #         temp_diff = abs(i - interval_idx)
                #         if temp_diff < temp_min_diff:
                #             temp_min_diff = temp_diff
                #             temp_speed = speed_matrix[way_id][i]
                #         elif temp_diff > temp_min_diff:
                #             break

                if temp_speed <= 0:
                    temp_need_estimate_idx.add(len(temp_history_speed))

            temp_history_speed.append(temp_speed)

        # print(temp_history_speed)

        if len(temp_need_estimate_idx) >= len(config_weight):
            # all history day has no data for this way
            # we assign 0 as the speed for the road for now
            predict_speed_dict[way_id] = 0
        else:
            if 0 < len(temp_need_estimate_idx):
                # some day's data is missing, we estimate the data using weight.
                # what it really do is just re-assign the weight
                temp_history_speed = estimate_missing_value(temp_history_speed, temp_need_estimate_idx, config_weight)

            # Compute the speed using dot product
            predict_speed_dict[way_id] = compute_predict_speed(temp_history_speed, config_weight)

    # For those way that not all speed_matrix contain data, we assign 0 for now
    for way_id in (full_way_id_set - usable_way_id_set):
        predict_speed_dict[way_id] = 0

    # Use nearby way to estimate the way that has 0 as predict speed.
    predict_speed_dict = estimate_no_data_road_speed_using_BFS(predict_speed_dict, way_graph, way_types,
                                                               way_type_avg_speed_limit)

    if flag_debug:
        print(show_traffic_speed(predict_speed_dict, predict_timestamp))
        # print(predict_speed_dict)

    return predict_speed_dict


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("predict_road_condition.py [timestamp]")
        print("")
        print("Optional:")
        print("timestamp  : 10-digit timestamp, use current time if not provided")
        exit(0)
    timestamp = int(sys.argv[1])
    start = time.process_time()
    predict_road_condition(timestamp)
    if flag_debug:
        print("[Debug] Total runtime is %.3f s" % (time.process_time() - start))
