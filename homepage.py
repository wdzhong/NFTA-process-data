'''
To run:

$ python homepage.py
'''
import json
import pickle
from datetime import datetime, timedelta
from pathlib import Path

from flask import Flask, render_template, jsonify

import predict_road_condition
import script.generate_prediction_in_large_batches as predict_result_helper
from helper.global_var import SAVE_TYPE_PICKLE, GOOGLE_MAPS_API_KEY, GPILB_CACHE_PATH
from helper.graph_reader import graph_reader

app = Flask(__name__)
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = timedelta(hours=3)


@app.route("/")
def home_page():
    return render_template("index.html", google_map_api_key=GOOGLE_MAPS_API_KEY)

@app.route("/index_js.js")
def home_page_js():
    return render_template("index_js.js")


@app.route("/get_traffic_data/<timestamp>/<time_interval>")
def retrieve_traffic_data(timestamp, time_interval):
    """
    Get the traffic data for the given timestamp (at the nearest time interval/slot) and time_interval.

    Parameters
    ----------
    timestamp: str
        A 10 digit timestamp

    time_interval: str
        The time interval size that the user has selected, e.g., 15, 30, and 45.

    Returns
    -------
    Serialized Json object, containing traffic data, which has the following format,
    {
        "generate_timestr": "2021-03-02 19:52:44",
        "generate_timestamp": 1614732764, .
        "time_slot_interval": 15,
        "interval_idx": 0,
        "predict_time_range": "2020-07-30 00:00 - 00:14",
        "road_speed": {way_id: {"speed": 16.274295463111194,
                                "speed_ratio": 0.46497987037460553},
                        ...
                      }
    }
    """
    # retrieve traffic at the specific timestamp (during the nearest interval)
    # print(timestamp)
    dt_target = datetime.fromtimestamp(int(timestamp))
    dt_now = datetime.now()
    time_interval = int(time_interval)

    dt_diff_min = int((dt_target - dt_now).seconds / 60)
    dt_diff_day = int((dt_target.date() - dt_now.date()).days)

    if dt_diff_day >= 0:
        if dt_diff_min <= 120:
            # Less than 2 hours
            return jsonify({"error": "no_data"})
        else:
            # find the nearest interval of the timestamp based on the time_interval size
            interval_idx = get_nearest_interval(dt_target, time_interval)

            data_path = Path(GPILB_CACHE_PATH.format(dt_target.strftime('%Y%m%d'), time_interval,
                                                     interval_idx))
            if data_path.is_file():
                with open(data_path, 'r') as fp:
                    data = json.load(fp)
            else:
                predict_speed_dict = predict_road_condition.predict_road_condition(dt_target.timestamp(),
                                                                                   interval=int(time_interval))
                data = predict_result_helper.get_output_dict_with_less_parameter(predict_speed_dict, dt_target,
                                                                                 time_interval)

            return jsonify(data)  # serialize and use JSON headers
    else:
        # Past time, can use existing data
        interval_idx = get_nearest_interval(dt_target, time_interval)
        date_str = dt_target.strftime("%Y%m%d")
        temp_filepath_csv = Path("data/{0}/result/{0}_{1}_min_road.csv".format(date_str, time_interval))
        temp_filepath_p = temp_filepath_csv.with_suffix('.p')
        speed_matrix = {}
        if temp_filepath_p.is_file():
            with open(temp_filepath_p, 'rb') as f:
                speed_matrix = pickle.load(f)
        elif temp_filepath_csv.is_file():
            speed_matrix = predict_road_condition.read_speed_matrix_from_file(temp_filepath_csv)
        else:
            return jsonify({"error": "no_data"})
        predict_speed_dict = {}
        for way_id, his_speeds in speed_matrix.items():
            predict_speed_dict[way_id] = his_speeds[interval_idx]

        save_filename_list = ["way_graph", "way_types", "way_type_avg_speed_limit"]
        temp_map_dates = graph_reader(Path("graph/"), SAVE_TYPE_PICKLE, save_filename_list)
        way_graph = temp_map_dates[0]
        way_types = temp_map_dates[1]
        way_type_avg_speed_limit = temp_map_dates[2]
        predict_speed_dict = predict_road_condition.estimate_no_data_road_speed_using_BFS(predict_speed_dict, way_graph,
                                                                                          way_types,
                                                                                          way_type_avg_speed_limit)
        data = predict_result_helper.get_output_dict_with_less_parameter(predict_speed_dict, dt_target, time_interval)
        return jsonify(data)


@app.route("/load_way_structure")
def load_way_structure():
    """
    Answer the call from frontend to load and send back the way structure, i.e., {way_id: [points]}.

    Returns
    -------
    json
        A json object (python dictionary)
    """
    way_structure_path = Path('.') / 'static' / 'mapdata' / 'way_structure.json'
    with open(way_structure_path, 'r') as fp:
        way_structure = json.load(fp)
    return jsonify(way_structure)


def get_nearest_interval(dt: datetime, interval_size: int) -> int:
    """
    Get the nearest time interval that the datetime falls in.

    Parameters
    ----------
    dt: datetime
        The datetime object

    interval_size: int
        The size of each time interval

    Returns
    -------
    int: the index of the interval that the given datetime falls in.
    """
    total_minutes = dt.hour * 60 + dt.minute
    return total_minutes // interval_size


if __name__ == '__main__':
    # app.run(host="** host here **", port=443,
    #         ssl_context=("ssl_certificate/** pem file here **.pem",
    #                      "ssl_certificate/** key file here **.key"),
    #         debug=True)
    app.run(host="localhost", port=82, debug=True)

'''
references

https://flask.palletsprojects.com/en/1.1.x/quickstart/#a-minimal-application

https://towardsdatascience.com/talking-to-python-from-javascript-flask-and-the-fetch-api-e0ef3573c451

https://becominghuman.ai/full-stack-web-development-python-flask-javascript-jquery-bootstrap-802dd7d43053

https://www.jitsejan.com/python-and-javascript-in-flask.html
'''
