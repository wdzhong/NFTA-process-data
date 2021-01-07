import csv
import pickle
import time
import math
import os
import sys
import json
import re
from find_nearest_road import find_nearest_road, distance

save_type_JSON = 1
save_type_pickle = 2


def find_traffic_speed(final_node_table, final_way_table, final_relation_table, data_directory, output_path):
    """
    Get the road speed matrix

    Parameters
    ----------
    final_node_table: Dict
        A dictionary that stored the node id and the latitude/longitude coordinates as a key value pair.

    final_way_table: Dict
        A dictionary that stored the way id and a list of node id's as a key value pair.

    final_relation_table:
        final_relation_table is a dictionary that stored the relation id and a tuple that had a list of nodes and ways
        and a list of tags. The list of nodes and ways were the stops and streets that made up a specific NFTA route.
        Nodes are usually included because the routes start and end at points that are generally not the natural
        endpoint of a road. The tags are useful because they possess information on the route like its name and what
        type of vehicle traverse the route (e.g. bus).

    data_directory: String
        The path of where the sorted data store

    output_path: String
        The path of where the road speed matrix output. It should be a csv file.

    Returns
    -------
    road_speeds: Map of [Int to [List of Int]]
        The lat and lng of the projection point from given point to the nearest road
    """
    # This data structrue will have the final result.
    # All of the keys will represent all of the ways that have a bus route go through them.
    road_speeds = {}

    # Many roads would get multiple data points.
    # The result is that we have to average speed.
    # My solution for this was to have an array of speeds and average them in the end.
    meta_speeds = {}

    for key, speed_samples in final_way_table.items():
        row = []
        # 24 hours * 60 min/hour / 5 min intervals = 288
        for i in range(288):
            row.append([])
        meta_speeds.update({key: row})
        road_speeds.update({key: [0] * 288})

    # used_ways = set()  #declear but never used

    bus_route_to_relation_index = {}
    for relation_index, relation_detail in final_relation_table.items():
        re_result = re.match(r"[0-9]+", relation_detail[1]['ref'])
        if re_result is None:
            continue
        temp_route = int(re_result.group())
        if temp_route not in bus_route_to_relation_index:
            bus_route_to_relation_index[temp_route] = set()
        bus_route_to_relation_index[temp_route].add(relation_index)

    debug_prof_count = [0, 0, 0]
    for filename in os.listdir(data_directory):
        start_time = time.time()

        procressed_lines_data = []
        with open(data_directory + filename, "r", newline='') as csv_file:
            reader_csv_file = csv.reader(csv_file)

            interval1 = -1
            # counter = 0  #declear but never used
            # points = []  #declear but never used
            # m = folium.Map(location=[42.89, -78.82], tiles="OpenStreetMap", zoom_start=12)

            # Takes the current data point and the next one and uses the pair
            # for each calculation of distance and speed.
            for temp_line in reader_csv_file:
                temp_total_second = int(temp_line[10][11:13]) * 3600 + int(temp_line[10][14:16]) * 60 + \
                                    int(temp_line[10][17:19])
                temp_data = [int(temp_line[1]),  # route_id
                             float(temp_line[7]),  # lat
                             float(temp_line[8]),  # lng
                             temp_total_second,  # total_seconds
                             int(temp_total_second / 300)]  # interval
                # temp_data[4] = math.floor(temp_data[3] / 300)
                procressed_lines_data.append(temp_data)

        for i in range(len(procressed_lines_data) - 1):
            # line1 = lines[i][:-1].split(',')
            route_id1 = procressed_lines_data[i][0]
            lat1 = procressed_lines_data[i][1]
            lng1 = procressed_lines_data[i][2]
            total_seconds1 = procressed_lines_data[i][3]
            interval1 = math.floor(total_seconds1 / 300)

            # line2 = lines[i + 1][:-1].split(',')
            route_id2 = procressed_lines_data[i + 1][0]
            lat2 = procressed_lines_data[i + 1][1]
            lng2 = procressed_lines_data[i + 1][2]
            total_seconds2 = procressed_lines_data[i + 1][3]
            interval2 = math.floor(total_seconds2 / 300)

            # These are all disqualifying pairs.
            if interval1 != interval2:
                # print('different interval')
                continue
            if total_seconds1 == total_seconds2:
                # print('same time')
                continue
            if lat1 == lat2 and lng1 == lng2:
                # print('same position')
                continue
            if lat1 >= 99.0 and lng1 >= 999.0:
                # print('bad location 1')
                continue
            if lat2 >= 99.0 and lng1 >= 999.0:
                # print('bad location 2')
                continue
            if route_id1 != route_id2:
                # this usually works but it may fail if the bus takes an unofficial road to the new bus route
                # start location， so I skip
                continue

            possible_relations1 = set()
            if route_id1 in bus_route_to_relation_index:
                possible_relations1 = bus_route_to_relation_index[route_id1]
            else:
                for key, speed_samples in final_relation_table.items():
                    if str(route_id1) in speed_samples[1]['ref']:
                        possible_relations1.add(key)
            projection1, way1 = find_nearest_road(final_node_table, final_way_table, final_relation_table,
                                                  possible_relations1, [lat1, lng1])

            possible_relations2 = set()
            if route_id2 in bus_route_to_relation_index:
                possible_relations2 = bus_route_to_relation_index[route_id2]
            else:
                for key, speed_samples in final_relation_table.items():
                    if str(route_id2) in speed_samples[1]['ref']:
                        possible_relations2.add(key)
            projection2, way2 = find_nearest_road(final_node_table, final_way_table, final_relation_table,
                                                  possible_relations2, [lat2, lng2])

            # print('{}:{}'.format(way,projection))
            # print('{}:{}'.format(way2,projection2))
            # print('{},{}'.format(lat,lng))

            speed = distance(projection1, projection2) / (total_seconds2 - total_seconds1)
            # km/s -> mph
            if speed == 0:
                continue
            speed = speed / 1.60934 * 3600

            # This code gives the same speed to all ways between the start location and the end location of the bus
            # route. I see very few places where this could fail, but if there is a -<=>- looking path the wrong
            # path may be used
            # See route 67, which openstreetmap marks as a backtrack for evidence of this problem
            if way1 == way2:
                meta_speeds[way1][interval1].append(speed)
                # used_ways.add(way1)
                # print('single speed: {}'.format(speed))
            else:
                meta_speeds[way1][interval1].append(speed)
                meta_speeds[way2][interval1].append(speed)
                # used_ways.add(way1)
                # used_ways.add(way2)

                '''
                This code took the current bus route, and then found the start and end street locations and then set
                the average speed for each street and all the streets inbetween on the route to the same speed. The
                method worked reasonably but route 67 (and maybe some others I didn't see) has a circular path and
                sometimes the wrong path was taken and their speeds were set incorrectly.

                for relation in possible_relations:
                    if way in final_relation_table[relation][0] and way2 in final_relation_table[relation][0]:
                        indices = final_relation_table[relation][0]
                        traversed = False
                        for i in range(len(indices)):

                            if indices[i] == way or indices[i] == way2:
                                traversed = not traversed
                                meta_speeds[indices[i]][interval].append(speed)
                                #print('start or end {} (way {}): {}'.format(traversed,indices[i],speed))
                                used_ways.add(indices[i])
                            elif traversed == True:
                                meta_speeds[indices[i]][interval].append(speed)
                                #print('inbetween (way {}): {}'.format(indices[i],speed))
                                used_ways.add(indices[i])
                        break
                '''

            '''
            print(meta_speeds[way])
            print(meta_speeds[way2])

            for node in final_way_table[way]:
                folium.Marker(final_node_table[node]).add_to(m)
            folium.Marker(projection).add_to(m)
            folium.Marker([lat,lng],icon=folium.Icon(color='red',icon_color='#FFFF00')).add_to(m)

            for node in final_way_table[way2]:
                folium.Marker(final_node_table[node]).add_to(m)
            folium.Marker(projection2).add_to(m)
            folium.Marker([lat2,lng2],icon=folium.Icon(color='red', icon_color='#FFFF00')).add_to(m)
            break
            '''
        end_time = time.time()
        print("%s done, %d lines, %.3fs, %.3fs/100lines" % (
            filename, len(procressed_lines_data), end_time - start_time,
            (end_time - start_time) / len(procressed_lines_data) * 100))
        debug_prof_count[0] += len(procressed_lines_data)
        debug_prof_count[1] += end_time - start_time
        debug_prof_count[2] += 1
        # print(filename)
    print("All %d file processed, total %d lines, use %.2fs, %.4f/100lines" % (
        debug_prof_count[2], debug_prof_count[0], debug_prof_count[1],
        (debug_prof_count[1] * 100) / debug_prof_count[0]))

    for way, speed_samples in meta_speeds.items():
        speed_intervals = []
        for i in range(len(speed_samples)):
            if len(speed_samples[i]) >= 1:
                road_speeds[way][i] = sum(speed_samples[i]) / len(speed_samples[i])

    with open(output_path, 'w+', newline='') as output_file:
        writer = csv.writer(output_file)
        temp_row = ["Road ID"]
        for h in range(24):
            for m in range(0, 60, 5):
                if m < 55:
                    temp_row.append("{0:0>2d}:{1:0>2d} - {0:0>2d}:{2:0>2d}".format(h, m, m + 5))
                else:
                    if h < 23:
                        temp_row.append("{0:0>2d}:{1:0>2d} - {2:0>2d}:{3:0>2d}".format(h, m, h + 1, 0))
                    else:
                        temp_row.append("{0:0>2d}:{1:0>2d} - {2:0>2d}:{3:0>2d}".format(h, m, 0, 0))
        writer.writerow(temp_row)

        for key, value in road_speeds.items():
            writer.writerow([key] + value)

    return road_speeds


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("find_traffic_speed.py [date] <result path> <result format>")
        print("")
        print("Require:")
        print("date       : 8 digit number of the date")
        print("             it is the folder name in data/")
        print("")
        print("Optional:")
        print("Result path: the path to the folder that store the osm_interpreter files")
        print("             by default is: graph/")
        print("Save format: the format to save the result, by default is pickle")
        print("             possible value: JSON or pickle")
        exit(0)

    date = sys.argv[1]

    result_file_path = "graph/"
    if len(sys.argv) >= 3:
        result_file_path = sys.argv[2]

    save_type = save_type_pickle
    if len(sys.argv) >= 4:
        if sys.argv[3] == "JSON":
            save_type = save_type_JSON
        elif sys.argv[3] == "pickle":
            save_type = save_type_pickle
        else:
            print("invalid Save format")
            print("Save format: the format to save the result, by default is pickle")
            print("             possible value: JSON and pickle")
            exit(0)

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
        temp_filepath = result_file_path + "final_relation_table.json"
        with open(temp_filepath, 'r') as f:
            final_relation_table = json.load(f)
            print("%s loaded" % temp_filepath)
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
        temp_filepath = result_file_path + "final_relation_table.p"
        with open(temp_filepath, 'rb') as f:
            final_relation_table = pickle.load(f)
            print("%s loaded" % temp_filepath)
        # temp_filepath = result_file_path + "relations.p"
        # with open(temp_filepath, 'rb') as f:
        #     relations = pickle.load(f)
        #     print("%s loaded" % temp_filepath)

    data_directory = 'data/{}/sorted/'.format(date)
    output_path = "data/{}_road.csv".format(date)

    start_time = time.time()
    find_traffic_speed(final_node_table, final_way_table, final_relation_table, data_directory, output_path)
    end_time = time.time()
    print("Total time = %.3fs" % (end_time - start_time))
