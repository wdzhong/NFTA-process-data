import json
import pickle
from helper.global_var import SAVE_TYPE_JSON, SAVE_TYPE_PICKLE, FLAG_DEBUG


def graph_reader(graph_path, save_type, save_filename_list):
    """
    Read the file in graph folder by provide the file name (without suffix)
    The result will be return in a list with the order of save_filename_list

    Parameters
    ----------
    graph_path: Path
        The path of the graph folder

    save_type: int
        The type of the file, use the following variable from helper.global_var
        SAVE_TYPE_JSON or SAVE_TYPE_PICKLE

    save_filename_list: List of string
        List of filename (without suffix) that need to be read.

    Returns
    -------
    result_list: List
        A list containing the data read from the given files. The order is the same order as the save_filename_list
    """
    result_list = []
    for save_filename in save_filename_list:
        if save_type == SAVE_TYPE_PICKLE:
            temp_filepath = graph_path / "{}.p".format(save_filename)
            with open(temp_filepath, 'rb') as f:
                result_list.append(pickle.load(f))
                if FLAG_DEBUG:
                    print("{} loaded".format(temp_filepath))
        elif save_type == SAVE_TYPE_JSON:
            temp_filepath = graph_path / "{}.json".format(save_filename)
            with open(temp_filepath, 'r') as f:
                result_list.append(json.load(f))
                if FLAG_DEBUG:
                    print("{} loaded".format(temp_filepath))
    return result_list
