import os
from datetime import datetime

import pandas as pd
from tqdm import tqdm


def load_data_file(data_root, data_filename, columns):
    """
    TODO:
    """
    get_datetime_from_filename(data_filename)

    data_path = os.path.join(data_root, data_filename)
    data = pd.read_csv(data_path, sep=',', header=None)

    assert len(columns) == data.shape[1] - 1, f"{data_path}'s columns are unexpected"
    data = data.drop(columns=data.columns[-1])  # data = data.drop(data.columns[-1], axis=1)

    data.columns = columns

    # remove lines with vehicle_id >= 8000
    data = data[data.vehicle_id < 8000]

    # remove lines with route_id_curr == 0
    # what does route_id_curr == 0 mean?
    data = data[data.route_id_curr != 0]

    data = data[data.route_id_curr <= 111]  # the current largest route number is 111

    # filter time
    # focus on time range between 6am and 9pm
    # since the traffic condition outside of this range is not that interesting
    start_time = 6
    end_time = 21
    data = data[data.apply(lambda row: 6 <= datetime.fromtimestamp(row['location time']).hour <= 21, axis=1)]
    return data


def merge_data_files(columns, data_root, all_in_one_file):
    """
    TODO
    """
    print(f"start merging data under {data_root}")
    min_file_size = 1000
    print(f"ignore files whose size is smaller than {min_file_size} byte.")
    print("loading...")
    all_data = []
    small_file_count = 0
    for data_filename in tqdm(sorted(os.listdir(data_root))):
        # print(data_filename)
        data_path = os.path.join(data_root, data_filename)
        # the file might be empty, if so, ignore it
        if os.stat(data_path).st_size <= min_file_size:
            # print(f"{data_path}'s size is too small.'")
            small_file_count += 1
            continue
        # print(data_path)
        data = load_data_file(data_root, data_filename, columns)
        all_data.append(data)

    print(f"number of too small files: {small_file_count}")

    print("Concatenate..")
    all_in_one = pd.concat(all_data, ignore_index=True)
    # print(all_in_one.shape)

    grouped = all_in_one.groupby(['vehicle_id', 'route_id_curr'])
    groups = dict(list(grouped))

    for key, value in groups.items():
        value = value.sort_values(by=['location time'])

    print("sorting..")
    all_in_one = all_in_one.sort_values(by=['vehicle_id', 'route_id_curr', 'direction', 'location time'])

    all_in_one['X'] = all_in_one['X'].apply(lambda x: round(x, 6))
    all_in_one['Y'] = all_in_one['Y'].apply(lambda x: round(x, 6))

    all_in_one['datetime'] = all_in_one['location time'].apply(lambda x: datetime.fromtimestamp(x))

    all_in_one_selected = all_in_one[['vehicle_id', 'route_id_curr', 'direction', 'block_id', 'next_tp_est', 'next_tp_sname', 'next_tp_sched', 'X', 'Y', 'location time', 'datetime']]

    all_in_one_selected = all_in_one_selected.drop_duplicates()

    print(f"saving to {os.path.join(os.getcwd(), all_in_one_file)}")
    all_in_one_selected.to_csv(all_in_one_file, index=False)

    return all_in_one_selected


if __name__ == "__main__":
    all_in_one_file = 'all_in_one.csv'

    if not os.path.isfile(all_in_one_file):
        columns = ['vehicle_id', 'route_id_curr', 'direction', 'block_id', 'service_type', 'deviation', 'next_tp_est', 'next_tp_sname', 'next_tp_sched', 'X', 'Y', 'location time', 'route logon id', 'block_num', 'off route', 'run_id']

        data_root = '../download_data/data'
        # data_root = os.path.join(os.getcwd(), 'data')
        data = merge_data_files(columns, data_root, all_in_one_file)
    else:
        data = pd.read_csv(all_in_one_file, sep=',')

    routes = list(set(data['route_id_curr'].values.tolist()))
    routes = sorted(routes)
    print(f"all routes: {routes}\tcount: {len(routes)}")  # 59
