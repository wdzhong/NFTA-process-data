from datetime import datetime, timedelta
import os
import pdb
import numpy as np
import pandas as pd


def combine_data_in_range(start_time, end_time, interval):
    """Combine the result data within the given range.

    Parameters
    ----------
    start_time : _type_
        _description_
    end_time : _type_
        _description_
    interval : _type_
        _description_
    """
    root = "data/"

    input_date_format = "%m/%d/%Y"
    start = datetime.strptime(start_time, input_date_format)
    end = datetime.strptime(end_time, input_date_format)

    date_rage = [start + timedelta(days=i) for i in range((end - start).days + 1)]

    # TODO: need to load the graph and get the number of points, in case of network changing
    number_of_nodes = 2795
    number_of_intervals = 24 * 60 // interval

    data = []
    filename_date_format = "%Y%m%d"

    for date in date_rage:
        print(date.strftime(input_date_format))
        print(date.strftime(filename_date_format))
        folder_name = date.strftime(filename_date_format)
        csv_filename = f"{folder_name}_{interval}_min_road.csv"
        csv_file = os.path.join(root, folder_name, "result", csv_filename)
        if os.path.isfile(csv_file):
            df = pd.read_csv(csv_file, skiprows=0)
            arr = df.iloc[:, 1:].to_numpy().transpose()
        else:
            arr = np.zeros((number_of_intervals, number_of_nodes))
        data.append(arr)

    # data.shape: [number_of_days, number_of_intervals, number_of_nodes]
    res = np.concatenate(data)  # res.shape: [number_of_days * number_of_intervals, number_of_nodes]
    res = np.expand_dims(res, -1)

    # save the combined data to file
    output_filename = start.strftime(filename_date_format) + "-" + end.strftime(filename_date_format) + ".npz"
    output_folder = os.path.join(root, "combined_traffic_data")
    if not os.path.isdir(output_folder):
        os.mkdir(output_folder)
    output_file = os.path.join(output_folder, output_filename)
    mask = np.zeros_like(res)
    mask[res != 0] = 1
    with open(output_file, 'wb') as f:
        # np.save(f, res)
        np.savez(f, data=res, mask=mask)

    return res


if __name__ == "__main__":
    combine_data_in_range("07/30/2020", "08/02/2020", 15)
