import os
import platform
import re

import sys
import time
from osm_handler import OSMHandler
from helper.graph_writer import graph_writer
from pathlib import Path
from helper.global_var import flag_debug, save_type_JSON, save_type_pickle


def debug_show_all_route(relations, final_node_table, final_way_table):
    """
    For debugging purposes, I plot all of the routes I saved, showing that I have all of the NFTA bus routes.

    Parameters
    ----------
    relations: List
        A list that contains the same information as final_relation_table, albeit in a less easily accessed form of a
        list of 3-tuples.

    final_node_table: Dict
        A dictionary that stored the node id and the latitude/longitude coordinates
        as a key value pair.

    final_way_table: Dict
        A dictionary that stored the way id and a list of node id's as a key value pair.

    Returns
    -------
    An URL link to the saved map file, can be open in the browser
    """
    import folium
    import random

    m = folium.Map(location=[42.89, -78.74], tiles="OpenStreetMap", zoom_start=10)

    print("[Debug] All route:")
    for relation in relations:
        line_color = '#{}'.format(hex(random.randint(0, 16777215))[2:])
        print("[Debug] - %s" % relation[2]['name'])
        for index in relation[1]:
            points = []
            if index in final_way_table:
                for waypoint in final_way_table[index]:
                    points.append((final_node_table[waypoint][0], final_node_table[waypoint][1]))
            elif index in final_node_table:
                points.append((final_node_table[index][0], final_node_table[index][1]))
            if len(points) != 0:
                folium.PolyLine(points, tooltip=relation[2]['name'], color=line_color).add_to(m)
    # https://github.com/python-visualization/folium/issues/946
    # a way to show the map outside ipython note book
    temp_path = "debug/map_of_all_route.html"
    m.save(temp_path)
    url_path = "file://" + os.path.abspath(temp_path)
    return url_path


def get_map_data(map_file, result_file_path, save_type):
    """
    Get the routes data from OSM file

    Parameters
    ----------
    map_file: Path
        The path of the osm file

    result_file_path: Path
        The path of the folder to save the result file.

    save_type: int
        The type to store the file, use the following variable
        save_type_JSON or save_type_pickle

    Returns
    -------
    final_node_table: Dict
        A dictionary that stored the node id and the latitude/longitude coordinates
        as a key value pair.

    final_way_table: Dict
        A dictionary that stored the way id and a list of node id's as a key value pair.

    final_relation_table: Dict
        A dictionary that stored the relation id and a tuple that had a list of nodes and ways and a list of tags.
        The list of nodes and ways were the stops and streets that made up a specific NFTA route. Nodes are usually
        included because the routes start and end at points that are generally not the natural endpoint of a road.
        The tags are useful because they possess information on the route like its name and what type of vehicle
        traverse the route (e.g. bus).

    relations: List
        A list that contains the same information as final_relation_table, albeit in a less easily accessed form of a
        list of 3-tuples.
    """
    osmhandler = OSMHandler()
    osmhandler.apply_file(str(map_file))

    latitudes = []
    longitudes = []
    ways = []
    relations = []
    node_table = {}
    way_table = {}
    final_node_table = {}
    final_way_table = {}
    final_relation_table = {}
    used_nodes = set()
    used_ways = set()
    way_tag_table = {}

    for node in osmhandler.nodes:
        latitudes.append(node[2].lat)
        longitudes.append(node[2].lon)
        node_table.update({node[1]: [node[2].lat, node[2].lon]})
    if flag_debug:
        print("[Debug] len(latitudes) = %d" % len(latitudes))

    for way in osmhandler.ways:
        ways.append(way)
        way_table.update({way[0]: way[1]})
        way_tag_table.update({way[0]: way[2]})
        # print(way[2])
    if flag_debug:
        print("[Debug] len(ways) = %d" % len(ways))

    # In the OSMHandler, I only saved relations that had NFTA in the name,
    # but I still had to save all of the nodes and ways because they don't
    # have additional information to tell me which ones I will use.
    # Here, I only save the nodes and ways that are found in the relations
    # that I'm actually going to use.

    for relation in osmhandler.relations:
        relations.append(relation)
        for index in relation[1]:
            if index in way_table:
                used_ways.add(index)
                # print(index)
                for waypoint in way_table[index]:
                    used_nodes.add(waypoint)
                    # print('({},{})'.format(node_table[waypoint][0],node_table[waypoint][1]))
            elif index in node_table:
                used_nodes.add(index)
                # print('({},{})'.format(node_table[index][0], node_table[index][1]))
    if flag_debug:
        print("[Debug] len(used_nodes) = %d" % len(used_nodes))
        print("[Debug] len(used_nodes) = %d" % len(used_ways))

    # Saves the final important nodes, ways, and relations to a format that is
    # more practical for my purposes: the dictionary.

    for key, value in node_table.items():
        if key in used_nodes:
            final_node_table.update({key: value})

    for key, value in way_table.items():
        if key in used_ways:
            final_way_table.update({key: value})

    for relation in relations:
        final_relation_table.update({relation[0]: [relation[1], relation[2]]})

    if flag_debug:
        print("[Debug] len(final_node_table) = %d" % len(final_node_table))
        print("[Debug] len(final_way_table)= %d" % len(final_way_table))
        print("[Debug] len(final_relation_table) = %d" % len(final_relation_table))
        print("[Debug] Map of all route: ", debug_show_all_route(relations, final_node_table, final_way_table))

    # Create a graph that use [OSM's way] as the node of the graph
    # and use [OSM's node] as the edge of the graph
    node_to_way_mapping = {}
    way_graph_by_set = {}
    for way in final_way_table:
        for node in final_way_table[way]:
            if node not in node_to_way_mapping:
                node_to_way_mapping[node] = {way}
            else:
                node_to_way_mapping[node].add(way)

    for node, ways in node_to_way_mapping.items():
        if len(ways) > 1:
            for way in ways:
                for way_other in (ways - {way}):
                    if way in way_graph_by_set:
                        way_graph_by_set[way].add(way_other)
                    else:
                        way_graph_by_set[way] = {way_other}

    # Convert the graph to a adjacency list format data structure
    way_graph_by_list = {}
    for key, value in way_graph_by_set.items():
        if key in final_way_table:
            way_graph_by_list[key] = list(value)

    # Create a dictionary that use way_id as key and store the type of the way, store in way_types
    # (the type of the way is mark as "highway" tag in OSM)
    # Also we compute the average speed limit for each type of the road and store in the way_type_avg_speed_limit
    way_types = {}
    way_type_avg_speed_limit = {}
    for key, value in way_graph_by_set.items():
        if "highway" in way_tag_table[key]:
            way_type = way_tag_table[key]["highway"]
            way_types[key] = way_type

            if way_type not in way_type_avg_speed_limit:
                way_type_avg_speed_limit[way_type] = []

            if "maxspeed" in way_tag_table[key]:
                re_result = re.search(r"\d*", way_tag_table[key]["maxspeed"])
                if re_result is None:
                    continue
                way_type_avg_speed_limit[way_type].append(int(re_result.group()))

    # To simplify the result, we round the result to the nearest multiple of 5.
    for key, value in way_type_avg_speed_limit.items():
        if len(value) != 0:
            way_type_avg_speed_limit[key] = 5 * round(sum(value) / len(value) / 5)
        else:
            way_type_avg_speed_limit[key] = 0


    # Save data to files
    save_filename_list = ["final_node_table", "final_way_table", "final_relation_table", "relations", "way_graph",
                          "way_types", "way_type_avg_speed_limit"]
    save_variable_list = [final_node_table, final_way_table, final_relation_table, relations, way_graph_by_list,
                          way_types, way_type_avg_speed_limit]
    graph_writer(result_file_path, save_type, save_filename_list, save_variable_list)

    return final_node_table, final_way_table, final_relation_table, relations


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("osm_interpreter.py <map file> [result path] [result format]")
        print("")
        print("Require:")
        print("Map file   : the path of the osm file")
        print("")
        print("Optional:")
        print("Result path: the path to the folder that store the result files")
        print("             by default is: graph/")
        print("Save format: the format to save the result, by default is pickle")
        print("             possible value: JSON and pickle")
        exit(0)

    map_file = Path(sys.argv[1])
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

    print("Map File   : %s" % map_file)
    print("Result path: %s" % result_file_path)
    if save_type == save_type_pickle:
        print("Result type: pickle")
    elif save_type == save_type_JSON:
        print("Result type: JSON")

    start = time.process_time()
    get_map_data(map_file, result_file_path, save_type)
    if flag_debug:
        print("[Debug] Total runtime is %.3f s" % (time.process_time() - start))
    print("Done")

    # Todo: This bug needs to be fixed. (Shiluo)
    if platform.system() != "Windows":
        exit(0)
    else:
        print("")
        print("Known BUG:")
        print("For some unknown reason, this python script cannot close correctly on some Windows")
        print("Killing the program ...")
        os.kill(os.getpid(), 9)
