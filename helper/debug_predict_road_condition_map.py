import os
import folium

from helper.debug_show_traffic_speed_map import get_traffic_speed_color
from helper.graph_reader import graph_reader
from helper.global_var import GOOGLE_MAPS_API_KEY, SAVE_TYPE_PICKLE
from datetime import datetime
from pathlib import Path
import gmplot


def show_traffic_speed(road_speeds, timestamp, map_type="OSM"):
    graph_need_read = ["way_types", "way_type_avg_speed_limit", "final_node_table", "final_way_table"]
    temp_map_dates = graph_reader(Path("graph"), SAVE_TYPE_PICKLE, graph_need_read)
    way_types = temp_map_dates[0]
    way_type_avg_speed_limit = temp_map_dates[1]
    final_node_table = temp_map_dates[2]
    final_way_table = temp_map_dates[3]

    if map_type == "GoogleMap":
        return show_traffic_speed_googlemap(final_way_table, final_node_table, road_speeds, timestamp)
    elif map_type == "OSM":
        return show_traffic_speed_OSM(final_way_table, final_node_table, road_speeds, timestamp, way_types,
                                      way_type_avg_speed_limit)
    else:
        print("Unknown map_type")
    return 0


def show_traffic_speed_OSM(final_way_table, final_node_table, road_speeds, timestamp, way_types,
                           way_type_avg_speed_limit):
    m = folium.Map(location=[42.89, -78.74], tiles="OpenStreetMap", zoom_start=10)

    for way, single_road_speed in road_speeds.items():
        line_color = get_traffic_speed_color(single_road_speed,
                                             way_type_avg_speed_limit.get(way_types.get(way, "unclassified"), 30))
        points = []
        if way in final_way_table:
            for waypoint in final_way_table[way]:
                points.append((final_node_table[waypoint][0], final_node_table[waypoint][1]))

            if len(points) != 0:
                folium.PolyLine(points,
                                tooltip="Speed: {:.2f}".format(single_road_speed), color=line_color).add_to(m)

    # https://github.com/python-visualization/folium/issues/946
    # a way to show the map outside ipython note book
    temp_path = "debug/predict_road_condition/{}.html".format(
        datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H%M%S"))
    m.save(temp_path)
    url_path = "file://" + os.path.abspath(temp_path)
    return url_path


def show_traffic_speed_googlemap(final_way_table, final_node_table, road_speeds, timestamp, way_types,
                                 way_type_avg_speed_limit):
    if GOOGLE_MAPS_API_KEY == "":
        raise RuntimeError('Cant find GOOGLE_MAPS_API_KEY, please check helper/globle_var.py')
    gmap = gmplot.GoogleMapPlotter(42.89, -78.74, 10, apikey=GOOGLE_MAPS_API_KEY)

    for way, single_road_speed in road_speeds.items():
        line_color = get_traffic_speed_color(single_road_speed,
                                             way_type_avg_speed_limit.get(way_types.get(way, "unclassified"), 30))
        lats = []
        lngs = []

        for waypoint in final_way_table[way]:
            lats.append(final_node_table[waypoint][0])
            lngs.append(final_node_table[waypoint][1])

        if len(lats) != 0:
            gmap.plot(lats, lngs, edge_width=5, color=line_color)

    temp_path = "debug/find_traffic_speed-googleMap/{}.html".format(
        datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H%M%S"))
    gmap.draw(temp_path)
    url_path = "file://" + os.path.abspath(temp_path)
    return url_path
