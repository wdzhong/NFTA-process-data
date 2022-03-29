import os
import re
import sys
from pathlib import Path
from tqdm import tqdm
sys.path.append('./')
import process_data
import reformat_data
import find_traffic_speed
from helper.global_var import SAVE_TYPE_PICKLE
from helper.graph_reader import graph_reader
from datetime import datetime


if __name__ == '__main__':
    data_root = Path(".") / 'data'

    save_filename_list = ["final_node_table", "final_way_table", "final_relation_table"]
    map_dates = graph_reader(Path("graph"), SAVE_TYPE_PICKLE, save_filename_list)
    final_node_table = map_dates[0]
    final_way_table = map_dates[1]
    final_relation_table = map_dates[2]

    today_str = (datetime.today()).strftime('%Y%m%d')
    for date_str in tqdm(os.listdir(data_root), unit="folder", position=-1):
        re_result = re.match(r"[0-9]{8}", str(date_str))
        if re_result is not None:
            if date_str != today_str:
                # print("python3.6 find_traffic_speed.py {}".format(date_str))
                # process_data part
                process_data.preprocess_data(date_str, overwrite=True, min_file_size=10, archive_after_preprocess=True,
                                             skip_if_archived=False)


                # reformat_data part
                reformat_data.reformat_by_bus(date_str)
                reformat_data.sort_reformat_data(date_str)

                # find_traffic_speed part
                time_slot_intervals = [5, 15]
                for interval in time_slot_intervals:
                    find_traffic_speed.find_traffic_speed(date_str, final_node_table, final_way_table,
                                                          final_relation_table, time_slot_interval=interval)
