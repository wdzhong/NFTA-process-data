import csv
import time
import math
import os
import sys
import re
import folium
from helper.global_var import flag_debug, save_type_JSON, save_type_pickle
from find_nearest_road import find_nearest_road, distance
from helper.graph_reader import graph_reader
from pathlib import Path
from tqdm import tqdm


def debug_get_traffic_speed_data(single_road_speed, road_speed_time_range_start_index, road_speed_time_range_end_index,
                                 time_slot_interval):
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
                sample_time.append(debug_time_range_index_to_str(index, time_slot_interval))
    else:
        for index in range(road_speed_time_range_start_index, road_speed_time_range_end_index+1):
            if single_road_speed[index] > 0:
                i += 1
                road_speed += (single_road_speed[index] - road_speed) / i
                sample_speed.append(single_road_speed[index])
                sample_time.append(debug_time_range_index_to_str(index, time_slot_interval))

    max_speed = 0
    min_speed = 9999
    for i in sample_speed:
        if i <= min_speed:
            min_speed = i
        if i >= max_speed:
            max_speed = i

    return road_speed, sample_speed, sample_time, max_speed, min_speed


def debug_get_traffic_speed_color(road_speed):
    if road_speed >= 20:
        color = "#84ca50"  # Green
    elif road_speed >= 10:
        color = "#f07d02"  # Yellow
    elif road_speed >= 5:
        color = "#e60000"  # Red
    elif road_speed <= 0:
        color = "#a9acb8"  # Gray
    else:
        color = "#9e1313"  # Dark Red
    return color


def debug_map_popup_generate(road_speed, sample_speed, sample_time, max_speed, min_speed):
    if road_speed != 0:
        sample_text = ""
        for temp_speed, temp_time in zip(sample_speed, sample_time):
            sample_text = sample_text + "<td>{}</td><td>{:.2f}</td></tr><tr>".format(temp_time, temp_speed)
        html = '''Avg. speed: {:.2f}<br>Max speed: {:.2f}<br>Min speed: {:.2f}<br>
        Detail:<table border="1"><tr>{}</tr></table>'''.format(road_speed, max_speed, min_speed, sample_text)
    else:
        html = "No data"
    iframe = folium.IFrame(html,  width=500, height=600)
    popup = folium.Popup(iframe, max_width=2650)
    return popup


def debug_show_traffic_speed(final_way_table, final_node_table, road_speeds, time_range_start_index,
                             time_range_end_index, time_slot_interval):

    m = folium.Map(location=[42.89, -78.74], tiles="OpenStreetMap", zoom_start=10)

    for way, single_road_speed in road_speeds.items():
        road_speed, sample_speed, sample_time, max_speed, min_speed = \
            debug_get_traffic_speed_data(single_road_speed, time_range_start_index, time_range_end_index,
                                         time_slot_interval)
        line_color = debug_get_traffic_speed_color(road_speed)
        points = []

        for waypoint in final_way_table[way]:
            points.append((final_node_table[waypoint][0], final_node_table[waypoint][1]))

        if len(points) != 0:
            folium.PolyLine(points,
                            popup=debug_map_popup_generate(road_speed, sample_speed, sample_time, max_speed, min_speed),
                            tooltip="Avg. speed: {:.2f}".format(road_speed), color=line_color).add_to(m)

    time_range_str = time_range_index_to_time_range_str(time_range_start_index, time_range_end_index, "")

    # https://github.com/python-visualization/folium/issues/946
    # a way to show the map outside ipython note book
    temp_path = "debug/find_traffic_speed/{}.html".format(time_range_str)
    m.save(temp_path)
    url_path = "file://" + os.path.abspath(temp_path)
    return url_path


def debug_time_range_index_to_str(time_range_index, time_slot_interval, delimiter=":", offset=0):
    time_in_min = (time_range_index * time_slot_interval)+offset
    h = math.floor(time_in_min / 60) % 24
    m = math.floor(time_in_min % 60)
    return "{:0>2d}{}{:0>2d}".format(h, delimiter, m)


def time_range_index_to_time_range_str(time_range_start_index, time_range_end_index, time_slot_interval, delimiter=":"):
    if time_range_start_index < 0:
        return "all day average"

    return "{} - {}".format(debug_time_range_index_to_str(time_range_start_index, time_slot_interval,
                                                          delimiter=delimiter),
                            debug_time_range_index_to_str(time_range_end_index, time_slot_interval,
                                                          delimiter=delimiter, offset=-1))


def find_traffic_speed(final_node_table, final_way_table, final_relation_table, data_directory, output_path,
                       time_slot_interval=5):
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

    time_slot_interval: Int
        The length of each time interval in minutes. The input number should be divisible by 1440 (24 hour * 60 min)
        by default it is 5 min

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

    # This data structrue will have the final result.
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
            interval1 = math.floor(total_seconds1 / (time_slot_interval * 60))

            # line2 = lines[i + 1][:-1].split(',')
            route_id2 = procressed_lines_data[i + 1][0]
            lat2 = procressed_lines_data[i + 1][1]
            lng2 = procressed_lines_data[i + 1][2]
            total_seconds2 = procressed_lines_data[i + 1][3]
            interval2 = math.floor(total_seconds2 / (time_slot_interval * 60))

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
        # print("%s done, %d lines, %.3fs, %.3fs/100lines" % (
        #     filename, len(procressed_lines_data), end_time - start_time,
        #     (end_time - start_time) / len(procressed_lines_data) * 100))
        debug_prof_count[0] += len(procressed_lines_data)
        debug_prof_count[1] += end_time - start_time
        debug_prof_count[2] += 1
        # print(filename)
    print("All %d file processed, total %d lines, use %.2fs, %.4f/100lines" % (
        debug_prof_count[2], debug_prof_count[0], debug_prof_count[1],
        (debug_prof_count[1] * 100) / debug_prof_count[0]))

    for way, speed_samples in meta_speeds.items():
        # speed_intervals = []
        for i in range(len(speed_samples)):
            if len(speed_samples[i]) >= 1:
                road_speeds[way][i] = sum(speed_samples[i]) / len(speed_samples[i])

    with open(output_path, 'w+', newline='') as output_file:
        writer = csv.writer(output_file)
        temp_row = ["Road ID"]

        for i in range(max_index):
            temp_row.append(time_range_index_to_time_range_str(i, i + 1, time_slot_interval))

        writer.writerow(temp_row)

        for key, value in road_speeds.items():
            writer.writerow([key] + value)

    if flag_debug:
        print("Generating map...")
        debug_show_traffic_speed(final_way_table, final_node_table, road_speeds, -1, -1, time_slot_interval)
        # for i in tqdm(range(0, 288, 12)):
        #     debug_show_traffic_speed(final_way_table, final_node_table, road_speeds, i, i + 11)

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

    result_file_path = Path("graph")
    if len(sys.argv) >= 3:
        result_file_path = Path(sys.argv[2])

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

    save_filename_list = ["final_node_table", "final_way_table", "final_relation_table"]
    map_dates = graph_reader(result_file_path, save_type, save_filename_list)

    final_node_table = map_dates[0]
    final_way_table = map_dates[1]
    final_relation_table = map_dates[2]

    time_slot_interval = 5
    data_directory = Path('data/{}/sorted/'.format(date))
    Path("data/{}/result".format(date)).mkdir(parents=True, exist_ok=True)
    output_path = Path("data/{}/result/{}_{}_min_road.csv".format(date, date, time_slot_interval))

    start_time = time.time()
    find_traffic_speed(final_node_table, final_way_table, final_relation_table, data_directory, output_path,
                       time_slot_interval)
    end_time = time.time()
    print("Total time = %.3fs" % (end_time - start_time))
