import json
import pickle
from helper.global_var import save_type_JSON, save_type_pickle

def graph_reader(result_file_path, save_type, save_filename_list):
    result_list = []
    for save_filename in save_filename_list:
        if save_type == save_type_pickle:
            temp_filepath = result_file_path / "{}.p".format(save_filename)
            with open(temp_filepath, 'rb') as f:
                result_list.append(pickle.load(f))
                print("{} loaded".format(temp_filepath))
        elif save_type == save_type_JSON:
            temp_filepath = result_file_path / "{}.json".format(save_filename)
            with open(temp_filepath, 'r') as f:
                result_list.append(json.load(f))
                print("{} loaded".format(temp_filepath))
    return result_list
