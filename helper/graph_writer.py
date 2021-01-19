import json
import pickle
from helper.global_var import save_type_JSON, save_type_pickle


def graph_writer(result_file_path, save_type, save_filename_list, save_variable_list):
    for save_filename, save_variable in zip(save_filename_list, save_variable_list):
        if save_type == save_type_pickle:
            temp_filepath = result_file_path / "{}.p".format(save_filename)
            with open(temp_filepath, 'wb') as f:
                pickle.dump(save_variable, f)
                print("{} saved".format(temp_filepath))
        elif save_type == save_type_JSON:
            temp_filepath = result_file_path / "{}.json".format(save_filename)
            with open(temp_filepath, 'w') as f:
                json.dump(save_variable, f, indent=2)
                print("{} saved".format(temp_filepath))
    return 0
