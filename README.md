# Main Goal

The four jupyter notebook files here are used to interpret the information found in the merged csv data files and save them in a format that can better compute road speeds in Buffalo.

# osm_interpreter.ipynb

This notebook has the code to convert an osm file downloaded from openstreetmap and find all of the NFTA routes and save their information in a dictionary. For debugging purposes, the NFTA roads that are found are also plotted. Using pickle, 3 dictionaries and 1 list are saved.

1. final_node_table

final_node_table was a dictionary that stored the node id and the latitude/longitude coordinates as a key value pair.

2. final_way_table

final_way_table was a dictionary that stored the way id and a list of node id's as a key value pair.

3. final_relation_table

final_relation_table was a dictionary that stored the relation id and a tuple that had a list of nodes and ways and a list of tags. The list of nodes and ways were the stops and streets that made up a specific NFTA route. Nodes are usually included because the routes start and end at points that are generally not the natural endpoint of a road. The tags are useful because they possess information on the route like its name and what type of vehicle traverse the route (e.g. bus).

4. relations

relations is a list that contains the same information as final_relation_table, albeit in a less easily accessed form of a list of 3-tuples.

# find_nearest_road.ipynb

This jupyter notebook is not necessary for the final execution of the code, but it is useful for demoing and testing the effectiveness of the math I'm using for finding the nearest road to a specific latitude and longitude coordinate. Essentially, all of the ways (roads) within 0.006&deg; are found and then the projection of the point onto each of these ways is calculated. The closest projection is assumed to be the actual location of point and the road it is on is the nearest road.

The math for this takes advantage of the small scope of the area of Buffalo. Because of this, we can assume that latitude and longitude are a grid coordinate system and compute the vectors using latitude and longitude. This results in slight inaccuracies in measurement. However, for the final distance, the haversine formula is used to find the projection or end of a way that is closest to the point we have. The haversine formula is much closer to the true distance between points, though some inaccuracy remains due to rounding on the radius of the Earth.

The capability is accurate enough for our purposes and its ability is demonstrated in this jupyter notebook.

# reformat_data.ipynb

reformat_data.ipynb was made necessary in order to parse the data in a more convenient manner. The data is first separated by bus and then resorted by time, from earliest to latest. This was necessary to accurate plot the path and direction the bus travels in throughout the day.

# find_traffic_speed.ipynb

After the osm_interpreter.ipynb has been run at least once to generate the nodes, ways (roads), and relations (routes) of the Buffalo region and reformat_data.ipynb has been run on the data we wish to parse, we can execute the code in find_traffic_speed.ipynb.

Using 5 minute intervals, there are a total of 288 intervals that must be accounted for, so the final result is a dictionary. The keys are the way id's. The values are lists/arrays that have a length of 288, which is the number of intervals if we have 5 minute intervals for a whole day. Accordingly, [0] is the 00:00 - 00:05 interval up to [287], which is 11:55 - 00:00.

We take every consecutive datapoint in the same time interval and find the road, distance, and time between the two. The speed we find is added to the road(s) that are involved in the calculation.

After we go through every datapoint, we average the speeds we found for every road to get the final result.

The final result is a dictionary of road speeds with the pair (way id : average speed).

This dictionary is saved using pickle and can be reloaded at any time for future calculations.