import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import List
import helper.global_var as global_var
import pandas as pd
from tqdm import tqdm


def load_data_file(data_path: Path, columns: List[str]) -> pd.DataFrame:
    """
    Load and filter one raw data file.

    Parameters
    ----------
    data_path: Path
        The path of the data file to load

    columns: List[str]
        A list of strings denote the headers of each column.

    Returns
    -------
    DataFrame: The DataFrame obj that contains the data.
    """

    data = pd.read_csv(data_path, sep=',', header=None)

    assert len(columns) == data.shape[1] - 1, f"{data_path}'s columns are unexpected"
    data = data.drop(columns=data.columns[-1])  # data = data.drop(data.columns[-1], axis=1)

    data.columns = columns

    # remove lines with 8000 <= vehicle_id < 9000, these vehicle are paratransit vehicle
    data = data[(data.vehicle_id < 8000) | (data.vehicle_id >= 9000)]

    # remove lines with route_id_curr == 0
    # what does route_id_curr == 0 mean?
    data = data[data.route_id_curr != 0]

    # remove lines with route_id_curr == 17
    # route 17 doesn't exist
    data = data[data.route_id_curr != 17]
    # route 45 91 99 are also in the raw data but not exist

    data = data[data.route_id_curr <= 111]
    # As of Feb 4, 2021 the largest route number is 111
    # But for history data, 216 is the largest route number all time
    # 216 - McKinley Mall-Gowanda (stopped May 1, 2012)

    # filter time
    data = data[data.apply(lambda row: global_var.PROCESS_DATA_START_TIME <=
                                       datetime.fromtimestamp(row['location time']).hour <=
                                       global_var.PROCESS_DATA_END_TIME, axis=1)]

    return data


def merge_data_files(columns: List[str], data_root: Path, all_in_one_file: Path, min_file_size):
    """
    Merge all files under one directory and save the result to the given file.

    Parameters
    ----------
    columns: List[str]
        A list of strings denote the headers of each column.

    data_root: Path
        The Path of the data directory

    all_in_one_file: Path
        The full path of the file to store the merged data.
    """
    # print(f"\nstart merging data under {data_root}")
    # print("loading...")
    all_data = []
    small_file_count = 0
    for data_filename in tqdm(sorted(os.listdir(data_root)), desc="Merging {}".format(data_root), unit="file",
                              position=1):
        data_path = os.path.join(data_root, data_filename)
        # the file might be empty, if so, ignore it
        if os.stat(data_path).st_size <= min_file_size:
            small_file_count += 1
            continue
        data = load_data_file(data_path, columns)
        all_data.append(data)

    if small_file_count > 0:
        print("number of too small files: {}".format(small_file_count))

    # print("Concatenate..")
    all_in_one = pd.concat(all_data, ignore_index=True)
    # print(all_in_one.shape)

    grouped = all_in_one.groupby(['vehicle_id', 'route_id_curr'])
    groups = dict(list(grouped))

    for key, value in groups.items():
        value = value.sort_values(by=['location time'])

    # print("sorting..")
    all_in_one = all_in_one.sort_values(by=['vehicle_id', 'route_id_curr', 'direction', 'location time'])

    all_in_one['X'] = all_in_one['X'].apply(lambda x: round(x, 6))
    all_in_one['Y'] = all_in_one['Y'].apply(lambda x: round(x, 6))

    all_in_one['datetime'] = all_in_one['location time'].apply(lambda x: datetime.fromtimestamp(x))

    all_in_one_selected = all_in_one[['vehicle_id', 'route_id_curr', 'direction', 'block_id', 'next_tp_est',
                                      'next_tp_sname', 'next_tp_sched', 'X', 'Y', 'location time', 'datetime']]

    all_in_one_selected = all_in_one_selected.drop_duplicates()

    # print(f"saving to {all_in_one_file}")
    all_in_one_selected.to_csv(all_in_one_file, index=False)


def preprocess_data(date_str: str, overwrite: bool = False, min_file_size: int = 10) -> None:
    """
    Preprocess data under given directory.

    Parameters:
    ----------
    date_str: string
        8 digit number of the date_str in yyyyMMdd format (e.g. 20200731)

    overwrite: bool, default is False
        If True, then re-preprocess all files; Otherwise, skip the folders that have already been processed before.

    min_file_size: int, default is 10
        Ignore files whose size is smaller than this limit. Unit is byte.

    Returns:
    --------
    None
    """
    # print(f"Start preprocessing: {data_root}, overwrite: {overwrite}")
    # print(f"ignore files whose size is smaller than {min_file_size} byte.")

    columns = ['vehicle_id', 'route_id_curr', 'direction', 'block_id', 'service_type', 'deviation', 'next_tp_est',
               'next_tp_sname', 'next_tp_sched', 'X', 'Y', 'location time', 'route logon id', 'block_num',
               'off route', 'run_id']

    full_path = Path(global_var.CONFIG_RAW_DATA_FOLDER.format(date_str))
    if full_path.is_dir():
        merged_file = Path(global_var.CONFIG_ALL_DAY_RAW_DATA_FILE.format(date_str))
        if not merged_file.is_file() or overwrite:
            merge_data_files(columns, full_path, merged_file, min_file_size)
        else:
            print(f"ignore {full_path} files smaller than {min_file_size} byte")


def get_routes_from_file(data_file: Path):
    """
    Get the routes that show up in a single data file.

    Parameters
    ----------
    data_file: Path
        The path of the data file to get the routes.

    Returns
    -------
    set[int]: A set of routes
    """
    data = pd.read_csv(data_file, sep=",")
    routes = set(data['route_id_curr'].values.tolist())
    return routes


def routes_showing_up(data_root=global_var.CONFIG_DATA_FOLDER):
    """
    Get all routes that show up in all data files under the given directory.
    One certain route does not need to show up in each and every data file.

    Parameters
    ----------
    data_root: Path
        The root of the merged data files.
    """
    data_root = Path(data_root)
    routes = set()
    for name in os.listdir(data_root):
        full_name_without_sub_folder = data_root / name
        if os.path.isdir(full_name_without_sub_folder):
            for sub_folder_name in os.listdir(full_name_without_sub_folder):
                re_result = re.match(r"[0-9]{8}\.csv", str(sub_folder_name))
                full_name = full_name_without_sub_folder / sub_folder_name
                if re_result is None:
                    print("Skip file", full_name)
                    continue
                cur_routes = get_routes_from_file(full_name)
                routes = routes.union(cur_routes)

    routes = list(routes)
    routes.sort()
    print(f"all routes: {routes}\tcount: {len(routes)}")


def data_statistic(data_root=global_var.CONFIG_DATA_FOLDER):
    """
    Get some statistical results for the merged data file under the data root.

    Parameters
    ----------
    data_root: Path
        The root of the merged data files.
    """
    routes_showing_up(data_root)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("process_data.py <date_str>")
        print("")
        print("Require:")
        print("date_str       : 8 digit number of the date_str")
        print("             it is the folder name in data/")
        exit(0)
    date = sys.argv[1]
    print(date)
    preprocess_data(date, overwrite=True, min_file_size=10)
    # data_statistic()
