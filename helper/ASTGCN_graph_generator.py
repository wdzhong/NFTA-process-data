import csv
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

from helper.distance import distance_accurate
from helper.graph_reader import graph_reader
from helper.global_var import SAVE_TYPE_JSON
from sklearn.cluster import AgglomerativeClustering


def get_average(data):
    return sum(data) / len(data)


def compute_distance(way_id, neighbor, ways_location):
    point1 = ways_location[str(way_id)]
    point2 = ways_location[str(neighbor)]
    return distance_accurate(point1, point2) * 0.621371192  # km to mile


def get_ways_location(final_node_table, final_way_table):
    ways_location = {}
    for way_id, nodes in final_way_table.items():
        lat = []
        lon = []
        for node in nodes:
            lat.append(final_node_table[str(node)][0])
            lon.append(final_node_table[str(node)][1])
        lat_avg = get_average(lat)
        lon_avg = get_average(lon)
        ways_location[way_id] = [lat_avg, lon_avg]
    return ways_location


def get_ASTGCN_graph(output_csv_path, final_node_table, final_way_table, way_graph):
    ways_location = get_ways_location(final_node_table, final_way_table)
    with open(output_csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["from", "to", "distance"])
        for way_id, neighbors in way_graph.items():
            for neighbor in neighbors:
                row_data = [way_id, neighbor, compute_distance(way_id, neighbor, ways_location)]
                writer.writerow(row_data)
    return


def get_ASTGCN_sub_graph(output_csv_path, final_node_table, final_way_table, way_graph):
    ways_location = get_ways_location(final_node_table, final_way_table)
    way_id_to_dataset = []
    dataset = []
    for way_id, location in ways_location.items():
        way_id_to_dataset.append(way_id)
        dataset.append(location)

    dataset_matrix = np.array(dataset)
    np.set_printoptions(threshold=np.inf)
    np.set_printoptions(linewidth=np.inf)
    np.set_printoptions(suppress=True)

    sub_graph_parameter = 11
    sc = AgglomerativeClustering(n_clusters=sub_graph_parameter)
    sc.fit(dataset_matrix)
    result = sc.labels_
    plt.figure(figsize=(6, 6))

    plot_data = {}
    grouping_information = {}
    for point, way_id,  group in zip(dataset, way_id_to_dataset, result):
        if group not in plot_data:
            plot_data[group] = []
            grouping_information[group] = set()
        plot_data[group].append(point)
        grouping_information[group].add(int(way_id))

    temp_data = []
    for key, value in plot_data.items():
        temp_data.append([key, value])
    plot_data = temp_data
    plot_data = sorted(plot_data, key=lambda a: a[0])
    for value in plot_data:
        temp_value = np.asarray(value[1])
        plt.scatter(temp_value[:, 1], temp_value[:, 0], marker='o',
                    label='Group {} ({})'.format(value[0], len(value[1])))
    figname = "AgglomerativeClustering, n_clusters={}".format(sub_graph_parameter)
    plt.title(figname)
    plt.legend()
    plt.savefig("debug/" + figname + ".png")
    plt.show()
    plt.cla()
    plt.close()

    # 12281461 93405445 True
    for group_id, ways in grouping_information.items():
        with open(output_csv_path.format(group_id), 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["from", "to", "distance"])
            for way_id in ways:
                neighbors = way_graph[str(way_id)]
                for neighbor in neighbors:
                    if neighbor not in ways:
                        continue
                    row_data = [way_id, neighbor, compute_distance(way_id, neighbor, ways_location)]
                    writer.writerow(row_data)
    return


if __name__ == '__main__':
    save_type = SAVE_TYPE_JSON
    result_file_path = Path("graph")

    save_filename_list = ["final_node_table", "final_way_table", "way_graph"]
    map_dates = graph_reader(result_file_path, save_type, save_filename_list)

    final_node_table = map_dates[0]
    final_way_table = map_dates[1]
    way_graph = map_dates[2]

    # get_ASTGCN_graph("graph/NFTA.csv",final_node_table, final_way_table, way_graph)

    get_ASTGCN_sub_graph("graph/NFTA_sub_graph_{0}.csv",final_node_table, final_way_table, way_graph)