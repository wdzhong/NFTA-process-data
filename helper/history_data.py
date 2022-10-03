import time
from datetime import datetime, timedelta

import numpy as np

from helper.global_var import CONFIG_SINGLE_DAY_RESULT_FILE


def get_history_data(current_timestamp, ways_list, interval, hours, days, weeks):
    return np.hstack([get_recent_hours_data(current_timestamp, ways_list, hours, interval),
                      get_recent_days_data(current_timestamp, ways_list, days, interval),
                      get_recent_weeks_data(current_timestamp, ways_list, weeks, interval)])


def get_recent_hours_data(current_timestamp, ways_list, hours, interval):
    current_time = datetime.fromtimestamp(current_timestamp)
    # print(current_time)
    end_interval_index = round_down_to_interval_index(current_time, interval)
    start_interval_index = end_interval_index - int((hours * 60) // interval)
    # print(start_interval_index, end_interval_index)
    if hours >= 24:
        raise ValueError("hours should be less than 24 hours")
    task_infos = []
    if start_interval_index < 0:
        max_index = 1440 // 15
        task_infos.append([current_time - timedelta(days=1), start_interval_index + max_index, max_index - 1])
        task_infos.append([current_time, 0, end_interval_index])
    else:
        task_infos.append([current_time, start_interval_index, end_interval_index])
    results = []
    for i in task_infos:
        results.append(get_history_data_by_interval_range(i[0], i[1], i[2], ways_list, interval))
    if len(task_infos) > 1:
        result = np.hstack(results)
    else:
        result = results[0]
    # print(result.shape)
    # print(result)
    return result


def get_recent_days_data(current_timestamp: int, ways_list, days: int, interval):
    current_time = datetime.fromtimestamp(current_timestamp)
    # print(current_time)
    interval_index = round_down_to_interval_index(current_time, interval)
    # print(interval_index)
    task_infos = []
    for i in range(1, days + 1):
        task_infos.append([current_time - timedelta(days=i), interval_index])
    results = []
    for i in task_infos:
        results.append(get_history_data_by_interval_range(i[0], i[1], i[1] + 1, ways_list, interval))
    if len(task_infos) > 1:
        result = np.hstack(results)
    else:
        result = results[0]
    # print(result.shape)
    # print(result)
    return result


def get_recent_weeks_data(current_timestamp: int, ways_list, weeks: int, interval):
    current_time = datetime.fromtimestamp(current_timestamp)
    # print(current_time)
    interval_index = round_down_to_interval_index(current_time, interval)
    # print(interval_index)
    task_infos = []
    for i in range(1, weeks + 1):
        task_infos.append([current_time - timedelta(weeks=i), interval_index])
    results = []
    for i in task_infos:
        results.append(get_history_data_by_interval_range(i[0], i[1], i[1] + 1, ways_list, interval))
    if len(task_infos) > 1:
        result = np.hstack(results)
    else:
        result = results[0]
    # print(result.shape)
    # print(result)
    return result


def get_history_data_by_interval_range(current_time, start_interval_index, end_interval_index, ways_list, interval):
    date_str = get_date_str(current_time)
    result_file_path = CONFIG_SINGLE_DAY_RESULT_FILE.format(date_str, interval)
    day_data = np.genfromtxt(result_file_path, delimiter=",", skip_header=1)

    way_id_to_matrix_row = get_way_id_to_matrix_row(day_data)

    day_data = np.delete(day_data, 0, axis=1)
    day_data = day_data[:, start_interval_index:end_interval_index]

    temp_result = np.zeros((len(ways_list), end_interval_index - start_interval_index))

    for row_index in range(0, len(ways_list)):
        way_id = ways_list[row_index]
        temp_result[row_index] = day_data[way_id_to_matrix_row[way_id]]

    return temp_result


def round_down_to_interval_index(current_time, interval):
    current_time = current_time + (current_time.min - current_time) % timedelta(minutes=interval)
    minutes_since_midnight = int((current_time - current_time.replace(hour=0, minute=0, second=0, microsecond=0))
                                 .total_seconds() // 60 // interval)
    return minutes_since_midnight


def get_way_id_to_matrix_row(day_data):
    way_id_to_matrix_row = {}
    counter = 0
    for j in day_data:
        way_id_to_matrix_row[int(j[0])] = counter
        counter += 1
    return way_id_to_matrix_row


def get_date_str(dt):
    return dt.strftime('%Y%m%d')


if __name__ == '__main__':
    dt = "2022-01-20 13:00:01"
    timestamp = int(time.mktime(time.strptime(dt, "%Y-%m-%d %H:%M:%S")))

    np.set_printoptions(precision=0, suppress=True)
    print(get_history_data(timestamp, [4374873,
                                       8845290,
                                       8845489,
                                       9277724,
                                       12271510,
                                       12271513,
                                       12275208,
                                       12280542,
                                       12281636,
                                       12282712], 15, 2, 5, 2))
