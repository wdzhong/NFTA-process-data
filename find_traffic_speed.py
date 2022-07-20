import csv
import datetime
import math
import os
import pickle
import re
import sys
import time
from pathlib import Path

from tqdm import tqdm

from find_nearest_road import find_nearest_road, distance
from helper.debug_show_traffic_speed_map import show_traffic_speed
from helper.global_var import FLAG_DEBUG, SAVE_TYPE_JSON, SAVE_TYPE_PICKLE, CONFIG_SINGLE_DAY_FOLDER, \
    CONFIG_SINGLE_DAY_RESULT_FILE
from helper.graph_reader import graph_reader
from helper.helper_time_range_index_to_str import time_range_index_to_time_range_str


def find_traffic_speed(date_str, final_node_table, final_way_table, final_relation_table,
                       time_slot_interval=5, recent_data_time=0):
    """
    Get the road speed matrix

    Parameters
    ----------
    date_str: string
        8 digit number of the date_str in yyyyMMdd format (e.g. 20200731)

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

    time_slot_interval: Int
        The length of each time interval in minutes. The input number should be divisible by 1440 (24 hour * 60 min)
        by default it is 5 min

    recent_data_time: Int
        If not 0, the function will only use the new data within [recent_data_time (in minute)] from the current time

    Returns
    -------
    road_speeds: Map of [Int to [List of Int]]
        The lat and lng of the projection point from given point to the nearest road
    """

    time_slot_interval = int(time_slot_interval)
    if time_slot_interval <= 0 or time_slot_interval > 1440:
        raise RuntimeError('interval should be between (0, 1440]')
    if 1440 % time_slot_interval != 0:
        raise RuntimeError('interval is not divisible by 1440')

    max_index = int(1440 / time_slot_interval)

    data_directory = Path(CONFIG_SINGLE_DAY_FOLDER.format(date_str)) / "sorted"
    output_path = Path(CONFIG_SINGLE_DAY_RESULT_FILE.format(date_str, time_slot_interval))
    if recent_data_time > 0:
        output_path = output_path.with_name(output_path.stem + "__latest_{}_min_only".format(recent_data_time) +
                                            output_path.suffix)

    # This data structures will have the final result.
    # All of the keys will represent all of the ways that have a bus route go through them.
    road_speeds = {}

    # Many roads would get multiple data points.
    # The result is that we have to average speed.
    # My solution for this was to have an array of speeds and average them in the end.
    meta_speeds = {}

    for key, speed_samples in final_way_table.items():
        row = []
        for i in range(max_index):
            row.append([])
        meta_speeds.update({key: row})
        road_speeds.update({key: [0] * max_index})

    # used_ways = set()  #  declare but never used

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
    current_time = datetime.datetime.now()
    new_data_threshold_in_second_of_the_day = \
        (current_time.hour * 3600 + current_time.minute * 60 + current_time.second) - (recent_data_time * 60)

    for filename in tqdm(os.listdir(data_directory)):
        start_time = time.time()
        procressed_lines_data = []
        with open(data_directory / filename, "r", newline='') as csv_file:
            reader_csv_file = csv.reader(csv_file)

            # counter = 0  #declear but never used
            # points = []  #declear but never used
            # m = folium.Map(location=[42.89, -78.82], tiles="OpenStreetMap", zoom_start=12)

            # Takes the current data point and the next one and uses the pair
            # for each calculation of distance and speed.

            for temp_line in reader_csv_file:
                # print(temp_line[10])
                temp_total_second = int(temp_line[10][11:13]) * 3600 + int(temp_line[10][14:16]) * 60 + \
                                    int(temp_line[10][17:19])
                if recent_data_time > 0 and temp_total_second < new_data_threshold_in_second_of_the_day:
                    continue
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
            interval1 = math.floor(total_seconds1 / (time_slot_interval * 60))

            # line2 = lines[i + 1][:-1].split(',')
            route_id2 = procressed_lines_data[i + 1][0]
            lat2 = procressed_lines_data[i + 1][1]
            lng2 = procressed_lines_data[i + 1][2]
            total_seconds2 = procressed_lines_data[i + 1][3]
            interval2 = math.floor(total_seconds2 / (time_slot_interval * 60))

            # These are all disqualifying pairs.
            if interval1 != interval2:
                if not (2 < interval1 - interval2 < 2):
                    continue
                # print('different interval')
                # continue
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

            # interval1_real_time = interval1 * 15
            # print("{}:{}".format(interval1_real_time // 60, interval1_real_time % 60))

            possible_relations1 = set()
            if route_id1 in bus_route_to_relation_index:
                possible_relations1 = bus_route_to_relation_index[route_id1]
            else:
                for key, speed_samples in final_relation_table.items():
                    if str(route_id1) in speed_samples[1]['ref']:
                        possible_relations1.add(key)

            if len(possible_relations1) <= 0:
                if FLAG_DEBUG:
                    print("No possible_relations found in {}, route_id {}, line {}".format(filename, route_id1, i))
                continue

            projection1, way1 = find_nearest_road(final_node_table, final_way_table, final_relation_table,
                                                  possible_relations1, [lat1, lng1])
            if way1 < 0:
                if FLAG_DEBUG:
                    print("Error while running find_nearest_road in {}, line {}".format(filename, i))
                continue

            possible_relations2 = set()
            if route_id2 in bus_route_to_relation_index:
                possible_relations2 = bus_route_to_relation_index[route_id2]
            else:
                for key, speed_samples in final_relation_table.items():
                    if str(route_id2) in speed_samples[1]['ref']:
                        possible_relations2.add(key)

            if len(possible_relations2) <= 0:
                if FLAG_DEBUG:
                    print("No possible_relations found in {}, line {}".format(filename, i + 1))
                continue

            projection2, way2 = find_nearest_road(final_node_table, final_way_table, final_relation_table,
                                                  possible_relations2, [lat2, lng2])
            if way1 < 0:
                if FLAG_DEBUG:
                    print("Error while running find_nearest_road in {}, line {}".format(filename, i + 1))
                continue

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
                if interval1 == interval2:
                    meta_speeds[way1][interval1].append(speed)
                else:
                    meta_speeds[way1][interval1].append(speed)
                    meta_speeds[way1][interval2].append(speed)
                # used_ways.add(way1)
                # print('single speed: {}'.format(speed))
            else:
                if interval1 == interval2:
                    meta_speeds[way1][interval1].append(speed)
                    meta_speeds[way2][interval1].append(speed)
                else:
                    meta_speeds[way1][interval1].append(speed)
                    meta_speeds[way2][interval1].append(speed)
                    meta_speeds[way1][interval2].append(speed)
                    meta_speeds[way2][interval2].append(speed)
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
        # print("%s done, %d lines, %.3fs, %.3fs/100lines" % (
        #     filename, len(procressed_lines_data), end_time - start_time,
        #     (end_time - start_time) / len(procressed_lines_data) * 100))
        debug_prof_count[0] += len(procressed_lines_data)
        debug_prof_count[1] += end_time - start_time
        debug_prof_count[2] += 1
        # print(filename)
    if FLAG_DEBUG and debug_prof_count[0] != 0:
        print("All %d file processed, total %d lines, use %.2fs, %.4f/100lines" % (
            debug_prof_count[2], debug_prof_count[0], debug_prof_count[1],
            (debug_prof_count[1] * 100) / debug_prof_count[0]))
    else:
        print("All {} file processed".format(debug_prof_count[2]))
    for way, speed_samples in meta_speeds.items():
        # speed_intervals = []
        for i in range(len(speed_samples)):
            if len(speed_samples[i]) >= 1:
                road_speeds[way][i] = sum(speed_samples[i]) / len(speed_samples[i])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w+', newline='') as output_file:
        writer = csv.writer(output_file)
        temp_row = ["Road ID"]

        for i in range(max_index):
            temp_row.append(time_range_index_to_time_range_str(i, i + 1, time_slot_interval))

        writer.writerow(temp_row)

        for key, value in road_speeds.items():
            writer.writerow([key] + value)

    with open(output_path.with_suffix('.p'), 'wb') as f:
        pickle.dump(road_speeds, f)

    if FLAG_DEBUG and debug_prof_count[0] != 0:
        print("Generating map...")
        show_traffic_speed(final_way_table, final_node_table, road_speeds, -1, -1, time_slot_interval, "OSM")
        # for i in tqdm(range(0, 288, 12)):
        #     debug_show_traffic_speed(final_way_table, final_node_table, road_speeds, i, i + 11)

    return road_speeds


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("find_traffic_speed.py [date_str] <result path> <result format>")
        print("")
        print("Require:")
        print("date_str       : 8 digit number of the date_str")
        print("             it is the folder name in data/")
        print("")
        print("Optional:")
        print("Result path: the path to the folder that store the osm_interpreter files")
        print("             by default is: graph/")
        print("Save format: the format to save the result, by default is pickle")
        print("             possible value: JSON or pickle")
        exit(0)

    date_str = sys.argv[1]

    result_file_path = Path("graph")
    if len(sys.argv) >= 3:
        result_file_path = Path(sys.argv[2])

    save_type = SAVE_TYPE_PICKLE
    if len(sys.argv) >= 4:
        if sys.argv[3] == "JSON":
            save_type = SAVE_TYPE_JSON
        elif sys.argv[3] == "pickle":
            save_type = SAVE_TYPE_PICKLE
        else:
            print("invalid Save format")
            print("Save format: the format to save the result, by default is pickle")
            print("             possible value: JSON and pickle")
            exit(0)

    if save_type == SAVE_TYPE_PICKLE:
        print("Result type: pickle")
    elif save_type == SAVE_TYPE_JSON:
        print("Result type: JSON")

    save_filename_list = ["final_node_table", "final_way_table", "final_relation_table"]
    map_dates = graph_reader(result_file_path, save_type, save_filename_list)

    final_node_table = map_dates[0]
    final_way_table = map_dates[1]
    final_relation_table = map_dates[2]

    time_slot_interval = 5

    start_time = time.time()
    find_traffic_speed(date_str, final_node_table, final_way_table, final_relation_table,
                       time_slot_interval=time_slot_interval)
    end_time = time.time()
    print("Total time = %.3fs" % (end_time - start_time))
