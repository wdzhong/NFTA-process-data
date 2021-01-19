import json
import pickle
from helper.global_var import save_type_JSON, save_type_pickle


def graph_writer(graph_path, save_type, save_filename_list, save_variable_list):
    """
    Read the file in graph folder by provide the file name (without suffix)
    The result will be return in a list with the order of save_filename_list

    Parameters
    ----------
    graph_path: Path
        The path of the graph folder

    save_type: int
        The type of the file, use the following variable from helper.global_var
        save_type_JSON or save_type_pickle

    save_filename_list: List of string
        List of filename (without suffix) that need to be save.

    save_variable_list: List
        List of value/variable that need to be save.

    Returns
    -------
    0
        No return
    """
    for save_filename, save_variable in zip(save_filename_list, save_variable_list):
        if save_type == save_type_pickle:
            temp_filepath = graph_path / "{}.p".format(save_filename)
            with open(temp_filepath, 'wb') as f:
                pickle.dump(save_variable, f)
                print("{} saved".format(temp_filepath))
        elif save_type == save_type_JSON:
            temp_filepath = graph_path / "{}.json".format(save_filename)
            with open(temp_filepath, 'w') as f:
                json.dump(save_variable, f, indent=2)
                print("{} saved".format(temp_filepath))
    return 0
