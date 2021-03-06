'''
To run:

$ python homepage.py
'''
from pathlib import Path
import datetime
import json

from flask import Flask, render_template, request, jsonify
app = Flask(__name__)


@app.route("/")
def home_page():
    # return "Hello, world!"
    example_embed = "Welcome!"
    return render_template("index.html", embed=example_embed)


@app.route("/get_traffic_data/<timestamp>/<time_interval>")
def retrieve_traffic_data(timestamp, time_interval):
    """
    Get the traffic data for the given timestamp (at the nearest time interval/slot) and time_interval.

    Parameters
    ----------
    timestamp: str
        A timestamp that is in iso format, e.g., 2020-07-30T12:00

    time_interval: str
        The time interval size that the user has selected, e.g., 15, 30, and 45.

    Returns
    -------
    Serilized Json object, containing traffic data, which has the following format,
    {
        "generate_timestr": "2021-03-02 19:52:44",
        "generate_timestamp": 1614732764, .
        "time_slot_interval": 15,
        "interval_idx": 0,
        "predict_time_range": "2020-07-30 00:00 - 00:14",
        "road_speed": [{"points": [[42.9597583, -78.8131567], [42.9599607, -78.812652], [42.9601687, -78.812126], [42.9605557, -78.811146], [42.9613168, -78.809176], [42.9613743, -78.8090273]],
                        "speed": 16.274295463111194,
                        "speed_ratio": 0.46497987037460553},
                        ...
                      ]
    }
    """
    # retrieve traffic at the specific timestamp (during the nearest interval)
    print(timestamp)
    dt = datetime.datetime.fromisoformat(timestamp)

    # find the nearest interval of the timestamp based on the time_interval size
    interval_id = get_nearest_interval(dt, int(time_interval))

    # TODO: use global (constant) path
    # data_path = Path('.') / 'cache' / 'predict_result' / '20200730' / '15' / '48.json'
    data_path = Path('.') / 'cache' / 'predict_result' / dt.strftime('%Y%m%d') / time_interval / f'{interval_id}.json'
    print(data_path)
    with open(data_path, 'r') as fp:
        data = json.load(fp)

    return jsonify(data)  # serialize and use JSON headers


def get_nearest_interval(dt: datetime.datetime, interval_size: int) -> int:
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
    total_minutes = dt.hour * 60 + dt.minute + (1 if dt.second else 0)
    return total_minutes // interval_size

app.run(debug=True)


'''
references

https://flask.palletsprojects.com/en/1.1.x/quickstart/#a-minimal-application

https://towardsdatascience.com/talking-to-python-from-javascript-flask-and-the-fetch-api-e0ef3573c451

https://becominghuman.ai/full-stack-web-development-python-flask-javascript-jquery-bootstrap-802dd7d43053

https://www.jitsejan.com/python-and-javascript-in-flask.html
'''
