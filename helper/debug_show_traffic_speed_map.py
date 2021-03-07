import os
import folium
from pathlib import Path
from helper.graph_reader import graph_reader
from helper.helper_time_range_index_to_str import time_range_index_to_str, time_range_index_to_time_range_str
from helper.global_var import GOOGLE_MAPS_API_KEY, SAVE_TYPE_PICKLE
import gmplot


def get_traffic_speed_data(single_road_speed, road_speed_time_range_start_index, road_speed_time_range_end_index,
                           time_slot_interval):
    """

    Collect all the non-zero data and compute the average as the road's speed

    Parameters
    ----------
    single_road_speed : list of float
        one row of the [speed matrix]
    road_speed_time_range_start_index : int
        The index of the start of the time range
    road_speed_time_range_end_index : int
        The index of the end of the time range (include the end time range)
    time_slot_interval : int
        The length of each time interval in minutes. The input number should be divisible by 1440 (24 hour * 60 min)
        by default it is 5 min

    Returns
    -------
    road_speed : float
        Average speed of the given road at given interval
    sample_speed : list of float
        Non-zero data that use to compute road_speed
    sample_time : list of float
        The corresponding time of the sample in sample_speed

    """
    sample_speed = []
    sample_time = []
    road_speed = 0
    i = 0
    if road_speed_time_range_start_index < 0:
        for index in range(len(single_road_speed)):
            if single_road_speed[index] > 0:
                i += 1
                road_speed += (single_road_speed[index] - road_speed) / i
                sample_speed.append(single_road_speed[index])
                sample_time.append(time_range_index_to_str(index, time_slot_interval))
    else:
        for index in range(road_speed_time_range_start_index, road_speed_time_range_end_index + 1):
            if single_road_speed[index] > 0:
                i += 1
                road_speed += (single_road_speed[index] - road_speed) / i
                sample_speed.append(single_road_speed[index])
                sample_time.append(time_range_index_to_str(index, time_slot_interval))

    return road_speed, sample_speed, sample_time


def get_traffic_speed_color(road_speed, speed_limit):
    """

    Output the color based on the speed and road speed limit

    Parameters
    ----------
    road_speed : float
        Average speed of the road
    speed_limit : int or float
        The speed limit of the road

    Returns
    -------
    String
        representing color in color hex triplet
    """
    # Consider NYC bus has average speed ~7 mph, and the average road speed limit in buffalo is around 30.
    # So we assume any bus that run faster then 0.2 * speed_limit is a "normal" speed, and the road has a good condition
    if speed_limit <= 0:
        speed_limit = 30
    if road_speed >= 0.2 * speed_limit:
        color = "#84ca50"  # Green
    elif road_speed >= 0.1 * speed_limit:
        color = "#f07d02"  # Yellow
    elif road_speed >= 0.05 * speed_limit:
        color = "#e60000"  # Red
    elif road_speed <= 0:
        color = "#a9acb8"  # Gray
    else:
        color = "#9e1313"  # Dark Red
    return color


def map_popup_generate(road_speed, sample_speed, sample_time):
    """
    Helper function generate OSM map popup

    Parameters
    ----------
    road_speed : float
        current road speed
    sample_speed : list of float
        The data that use to compute road_speed (more information can be found in get_traffic_speed_data
    sample_time : list of float
        The corresponding time of the sample in sample_speed

    Returns
    -------
    String
        HTML string for the popup page
    """
    if road_speed != 0:
        sample_text = ""
        for temp_speed, temp_time in zip(sample_speed, sample_time):
            sample_text = sample_text + "<td>{}</td><td>{:.2f}</td></tr><tr>".format(temp_time, temp_speed)
        html = '''Avg. speed: {:.2f}<br>Max speed: {:.2f}<br>Min speed: {:.2f}<br>
        Detail:<table border="1"><tr>{}</tr></table>'''.format(road_speed, max(sample_speed), min(sample_speed), sample_text)
    else:
        html = "No data"
    iframe = folium.IFrame(html, width=500, height=600)
    popup = folium.Popup(iframe, max_width=2650)
    return popup


def show_traffic_speed(final_way_table, final_node_table, road_speeds, time_range_start_index,
                       time_range_end_index, time_slot_interval, map_type="OSM"):
    """

    Parameters
    ----------
    final_node_table: Dictionary
        A dictionary that stored the node id and the latitude/longitude coordinates as a key value pair.
    final_way_table: Dictionary
        A dictionary that stored the way id and a list of node id's as a key value pair.
    road_speeds : Dictionary
        A dictionay that stored the [speed matrix] use way id as key and use list to store each row
    time_range_start_index : int
        The index of the start of the time range
    time_range_end_index : int
        The index of the end of the time range (include the end time range)
    time_slot_interval : int
        The length of each time interval in minutes. The input number should be divisible by 1440 (24 hour * 60 min)
        by default it is 5 min
    map_type : str, optional
        The map platform of the generate map. Could be GoogleMap or OSM, by default "OSM"

    Returns
    -------
    None
    """
    save_filename_list = ["way_types", "way_type_avg_speed_limit"]
    temp_map_dates = graph_reader(Path("graph/"), SAVE_TYPE_PICKLE, save_filename_list)
    way_types = temp_map_dates[0]
    way_type_avg_speed_limit = temp_map_dates[1]

    if map_type == "GoogleMap":
        return show_traffic_speed_googlemap(final_way_table, final_node_table, road_speeds, time_range_start_index,
                                            time_range_end_index, time_slot_interval, way_types,
                                            way_type_avg_speed_limit)
    elif map_type == "OSM":
        return show_traffic_speed_OSM(final_way_table, final_node_table, road_speeds, time_range_start_index,
                                      time_range_end_index, time_slot_interval, way_types, way_type_avg_speed_limit)
    else:
        print("Unknown map_type")
    return 0


def show_traffic_speed_OSM(final_way_table, final_node_table, road_speeds, time_range_start_index,
                           time_range_end_index, time_slot_interval, way_types, way_type_avg_speed_limit):
    """

    Parameters
    ----------
    final_node_table: Dictionary
        A dictionary that stored the node id and the latitude/longitude coordinates as a key value pair.
    final_way_table: Dictionary
        A dictionary that stored the way id and a list of node id's as a key value pair.
    road_speeds : Dictionary
        A dictionay that stored the [speed matrix] use way id as key and use list to store each row
    time_range_start_index : int
        The index of the start of the time range
    time_range_end_index : int
        The index of the end of the time range (include the end time range)
    time_slot_interval : int
        The length of each time interval in minutes. The input number should be divisible by 1440 (24 hour * 60 min)
        by default it is 5 min
    way_types : Dictionary
        A dictionary that stored the way id and the type of the way as a key value pair.
    way_type_avg_speed_limit : Dictionary
        A dictionary that stored the way type and the average speed limit of that type as a key value pair.

    Returns
    -------
    String
        The url to the map that generated
    """
    m = folium.Map(location=[42.89, -78.74], tiles="OpenStreetMap", zoom_start=10)

    for way, single_road_speed in road_speeds.items():
        road_speed, sample_speed, sample_time = \
            get_traffic_speed_data(single_road_speed, time_range_start_index, time_range_end_index,
                                   time_slot_interval)
        line_color = get_traffic_speed_color(road_speed,
                                             way_type_avg_speed_limit.get(way_types.get(way, "unclassified"), 30))
        points = []

        for waypoint in final_way_table[way]:
            points.append((final_node_table[waypoint][0], final_node_table[waypoint][1]))

        if len(points) != 0:
            folium.PolyLine(points,
                            popup=map_popup_generate(road_speed, sample_speed, sample_time, max_speed, min_speed),
                            tooltip="Avg. speed: {:.2f}".format(road_speed), color=line_color).add_to(m)

    time_range_str = time_range_index_to_time_range_str(time_range_start_index, time_range_end_index, "")

    # https://github.com/python-visualization/folium/issues/946
    # a way to show the map outside ipython note book
    temp_path = "debug/find_traffic_speed/{}.html".format(time_range_str)
    m.save(temp_path)
    url_path = "file://" + os.path.abspath(temp_path)
    return url_path


def show_traffic_speed_googlemap(final_way_table, final_node_table, road_speeds, time_range_start_index,
                                 time_range_end_index, time_slot_interval, way_types, way_type_avg_speed_limit):
    """

    Parameters
    ----------
    final_node_table: Dictionary
        A dictionary that stored the node id and the latitude/longitude coordinates as a key value pair.
    final_way_table: Dictionary
        A dictionary that stored the way id and a list of node id's as a key value pair.
    road_speeds : Dictionary
        A dictionay that stored the [speed matrix] use way id as key and use list to store each row
    time_range_start_index : int
        The index of the start of the time range
    time_range_end_index : int
        The index of the end of the time range (include the end time range)
    time_slot_interval : int
        The length of each time interval in minutes. The input number should be divisible by 1440 (24 hour * 60 min)
        by default it is 5 min
    way_types : Dictionary
        A dictionary that stored the way id and the type of the way as a key value pair.
    way_type_avg_speed_limit : Dictionary
        A dictionary that stored the way type and the average speed limit of that type as a key value pair.

    Returns
    -------
    String
        The url to the map that generated

    """
    if GOOGLE_MAPS_API_KEY == "":
        raise RuntimeError('Cant find GOOGLE_MAPS_API_KEY, please check helper/global_var.py')
    gmap = gmplot.GoogleMapPlotter(42.89, -78.74, 10, apikey=GOOGLE_MAPS_API_KEY)

    for way, single_road_speed in road_speeds.items():
        road_speed, sample_speed, sample_time = \
            get_traffic_speed_data(single_road_speed, time_range_start_index, time_range_end_index,
                                   time_slot_interval)
        line_color = get_traffic_speed_color(road_speed,
                                             way_type_avg_speed_limit.get(way_types.get(way, "unclassified"), 30))
        lats = []
        lngs = []

        for waypoint in final_way_table[way]:
            lats.append(final_node_table[waypoint][0])
            lngs.append(final_node_table[waypoint][1])

        if len(lats) != 0:
            gmap.plot(lats, lngs, edge_width=5, color=line_color)

    time_range_str = time_range_index_to_time_range_str(time_range_start_index, time_range_end_index, "")

    google_map_save_folder = Path(".") / "debug" / "find_traffic_speed-googleMap"
    if not os.path.isdir(google_map_save_folder):
        os.makedirs(google_map_save_folder, exist_ok=True)
    temp_path = google_map_save_folder / f"{time_range_str}.html"
    gmap.draw(temp_path)
    url_path = "file://" + os.path.abspath(temp_path)
    return url_path
