import shutil
import sys
sys.path.append('./')
import process_data
import reformat_data
import find_traffic_speed
from datetime import datetime, timedelta
from pathlib import Path
from helper.global_var import SAVE_TYPE_PICKLE, CONFIG_SINGLE_DAY_FOLDER
from helper.graph_reader import graph_reader

if __name__ == '__main__':
    date_str = (datetime.today() + timedelta(-1)).strftime('%Y%m%d')
    # date_str = "20200130"
    data_root = Path(".") / 'data'
    process_data.preprocess_data(date_str, overwrite=True, min_file_size=10, archive_after_preprocess=True)
    reformat_data.reformat_by_bus(date_str)
    reformat_data.sort_reformat_data(date_str)

    save_filename_list = ["final_node_table", "final_way_table", "final_relation_table"]
    map_dates = graph_reader(Path("graph"), SAVE_TYPE_PICKLE, save_filename_list)
    final_node_table = map_dates[0]
    final_way_table = map_dates[1]
    final_relation_table = map_dates[2]

    time_slot_intervals = [5, 15]
    for interval in time_slot_intervals:
        find_traffic_speed.find_traffic_speed(date_str, final_node_table, final_way_table, final_relation_table,
                                              time_slot_interval=interval)
    sorted_dir = Path(CONFIG_SINGLE_DAY_FOLDER.format(date_str)) / "sorted"
    shutil.rmtree(sorted_dir)
