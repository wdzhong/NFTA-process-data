import pickle
import folium
import os
import sys
import json
import math

flag_debug = True


# haversine formula for more precise distance calculation
def distance(point1, point2):
    """
    Get the distance between two point in km (kilometers)

    Parameters
    ----------
    point1: List of int
        Longitude and Latitude of first point

    point2：List of int
        Longitude and Latitude of first point

    Returns
    -------
    distance: float
        The distance between the two point in km (kilometers)
    """
    # Radius of earth at latitude 42.89 + elevation of buffalo, ny
    radius = 6368.276 + 0.183

    lat1, lng1 = point1
    lat2, lng2 = point2

    theta1 = math.radians(lat1)
    theta2 = math.radians(lat2)
    phi1 = math.radians(lng1)
    phi2 = math.radians(lng2)

    result = 2 * radius * math.asin(math.sqrt(
        math.sin((theta2 - theta1) / 2) ** 2 + math.cos(theta1) * math.cos(theta2) * math.sin((phi2 - phi1) / 2) ** 2))

    return result


def get_close_road(final_node_table, final_way_table, datapoint, margin=0.006):
    """
    Get the closest road for given datapoint

    Parameters
    ----------
    datapoint: List of int
        Longitude and Latitude of the given point

    margin：float
        the range of the nodes we will get (in degree), by default is 0.006
        Experimentally determined a +- value of .006 just by looking at the largest space between nodes

    Returns
    -------
    way: int
        The id of the way that closest to the given point

    """
    proximal_nodes = {}

    # adds all nodes within margin(0.006) degrees of the datapoint
    for key, value in final_node_table.items():
        if datapoint[0] + margin > value[0] > datapoint[0] - margin:
            if datapoint[1] + margin > value[1] > datapoint[1] - margin:
                proximal_nodes.update({key: value})

    if flag_debug:
        print("[Debug] len(proximal_nodes) = %d" % len(proximal_nodes))
        m = folium.Map(location=datapoint, tiles="OpenStreetMap", zoom_start=18)
        folium.Marker(datapoint, popup='datapoint').add_to(m)
        for key, value in proximal_nodes.items():
            folium.Marker(value).add_to(m)
        temp_path = "debug/map_of_nearby_nodes.html"
        m.save(temp_path)
        url_path = "file://" + os.path.abspath(temp_path)
        print("[Debug] Map of all nearby nodes: ", url_path)

    # Finds the ways that have nodes within margin(0.006) degrees of the datapoint
    proximal_ways = {}
    # proximal_nodes_key_set = set(proximal_nodes.keys())
    for key, value in final_way_table.items():
        for node in value:
            if node in proximal_nodes:
                proximal_ways.update({key: value})
                break

    if flag_debug:
        print("[Debug] len(proximal_ways) = %d" % len(proximal_ways))
        m = folium.Map(location=datapoint, tiles="OpenStreetMap", zoom_start=18)
        folium.Marker(datapoint, popup='datapoint').add_to(m)
        for key, value in proximal_ways.items():
            points = []
            for node in value:
                points.append(final_node_table[node])
            folium.PolyLine(points).add_to(m)
        temp_path = "debug/map_of_nearby_way.html"
        m.save(temp_path)
        url_path = "file://" + os.path.abspath(temp_path)
        print("[Debug] Map of all nearby road(way): ", url_path)

    min_dist = math.inf
    min_way = -1
    min_projection = []

    # For each road, I calculate the projection of the datapoint onto the road using dot product.
    # The minimum distance using haversine formula determines which point I calculate is closest
    # to the datapoint. If the projection is off the road (the road stops before the vector), it
    # will not be considered. Instead, the distance of the end of the road will be used.
    for key, value in proximal_ways.items():
        for i in range(len(value) - 1):
            a = final_node_table[value[i]]
            b = final_node_table[value[i + 1]]
            c = datapoint

            temp_distance = distance(a, c)
            if temp_distance < min_dist:
                min_dist = temp_distance
                min_way = key
                min_projection = a

            temp_distance = distance(b, c)
            if temp_distance < min_dist:
                min_dist = temp_distance
                min_way = key
                min_projection = b

            u = [b[0] - a[0], b[1] - a[1]]
            v = [c[0] - a[0], c[1] - a[1]]

            projection = [0, 0]
            projection[0] = (u[0] * v[0] + u[1] * v[1]) / (u[0] ** 2 + u[1] ** 2) * u[0] + a[0]
            projection[1] = (u[0] * v[0] + u[1] * v[1]) / (u[0] ** 2 + u[1] ** 2) * u[1] + a[1]

            if min(a[0], b[0]) <= projection[0] <= max(a[0], b[0]) and \
                    min(a[1], b[1]) <= projection[1] <= max(a[1], b[1]):
                temp_distance = distance(projection, c)
                if temp_distance < min_dist:
                    if flag_debug:
                        print("[Debug] distance(projection, c) = %d" % temp_distance)
                    min_dist = temp_distance
                    min_way = key
                    min_projection = projection

    if flag_debug:
        m = folium.Map(location=datapoint, tiles="OpenStreetMap", zoom_start=18)
        folium.Marker(datapoint, popup='datapoint', icon=folium.Icon(color='green')).add_to(m)
        folium.Marker(min_projection, popup='projection', icon=folium.Icon(color='red', icon_color='#FFFF00')).add_to(m)
        tamp_way = []
        for node in proximal_ways[min_way]:
            # print(distance(final_node_table[node],point1))
            folium.Marker(location=final_node_table[node]).add_to(m)
            tamp_way.append(final_node_table[node])
        folium.PolyLine(tamp_way).add_to(m)
        print("[Debug] Min distance to road: ", min_dist)
        temp_path = "debug/map_of_nearest_road.html"
        m.save(temp_path)
        url_path = "file://" + os.path.abspath(temp_path)
        print("[Debug] Map of nearest_road: ", url_path)

    return min_way


save_type_JSON = 1
save_type_pickle = 2

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage:")
        print("find_traffic_speed.py <Longitude> <Latitude> <osm_interpreter path> <osm_interpreter format>")
        print("")
        print("Require:")
        print("Longitude  : the longitude of the given points")
        print("Latitude   : the Latitude of the given points")
        print("")
        print("Optional:")
        print("Result path: the path to the folder that store the osm_interpreter files")
        print("             by default is: graph/")
        print("Save format: the format to save the result, by default is pickle")
        print("             possible value: JSON or pickle")
        exit(0)

    datapoint = [0, 0]
    datapoint[0] = float(sys.argv[1])
    datapoint[1] = float(sys.argv[2])

    if(datapoint[0] > 90 or datapoint[0] < -90 or datapoint[1] > 180 or datapoint[1] < -180):
        print("Invalid Latitude and/or Longitude")
        exit(0)

    result_file_path = "graph/"
    if len(sys.argv) >= 4:
        result_file_path = sys.argv[1]

    save_type = save_type_pickle
    if len(sys.argv) >= 5:
        if sys.argv[2] == "JSON":
            save_type = save_type_JSON
        elif sys.argv[2] == "pickle":
            save_type = save_type_pickle
        else:
            print("invalid Save format")
            print("Save format: the format to save the result, by default is pickle")
            print("             possible value: JSON and pickle")
            exit(0)

    print("datapoint  : %s" % datapoint)
    print("Result path: %s" % result_file_path)
    if save_type == save_type_pickle:
        print("Result type: pickle")
    elif save_type == save_type_JSON:
        print("Result type: JSON")

    if save_type == save_type_JSON:
        temp_filepath = result_file_path + "final_node_table.json"
        with open(temp_filepath, 'r') as f:
            final_node_table = json.load(f)
            print("%s loaded" % temp_filepath)
        temp_filepath = result_file_path + "final_way_table.json"
        with open(temp_filepath, 'r') as f:
            final_way_table = json.load(f)
            print("%s loaded" % temp_filepath)
        # temp_filepath = result_file_path + "final_relation_table.json"
        # with open(temp_filepath, 'r') as f:
        #     final_relation_table = json.load(f)
        #     print("%s loaded" % temp_filepath)
        # temp_filepath = result_file_path + "relations.json"
        # with open(temp_filepath, 'r') as f:
        #     relations = json.load(f)
        #     print("%s loaded" % temp_filepath)

    elif save_type == save_type_pickle:
        temp_filepath = result_file_path + "final_node_table.p"
        with open(temp_filepath, 'rb') as f:
            final_node_table = pickle.load(f)
            print("%s loaded" % temp_filepath)
        temp_filepath = result_file_path + "final_way_table.p"
        with open(temp_filepath, 'rb') as f:
            final_way_table = pickle.load(f)
            print("%s loaded" % temp_filepath)
        # temp_filepath = result_file_path + "final_relation_table.p"
        # with open(temp_filepath, 'rb') as f:
        #     final_relation_table = pickle.load(f)
        #     print("%s loaded" % temp_filepath)
        # temp_filepath = result_file_path + "relations.p"
        # with open(temp_filepath, 'rb') as f:
        #     relations = pickle.load(f)
        #     print("%s loaded" % temp_filepath)

    get_close_road(final_node_table, final_way_table, datapoint)
