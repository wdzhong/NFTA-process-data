
## All Routes of NFTA

[![All Routes](images/all_routes.jpg)](http://metro.nfta.com/)

But there is route `17` in the data. ~~The picture might be outdated.~~ Route `17` is a previously operating routes


## Goal

### First Stage
From the collected data during **one single day** (e.g., `data/20200730.csv`), get the traffic speed (or travel time) on each road segment during each time interval, and save it into a file named `data/20200730_road.csv`. If there is no data for certain road segment during certain time interval, leave it empty. On the other hand, if there are more than one values (e.g., two or more buses traveled on the same road segment during the same time interval), then use the average.

This table shows an example of the result for one day with time interval set to be 5 minutes.

| Road\Time   | 00:00 - 00:05 | 00:05 - 00:10  | 00:10 - 00:15 | ... | 23:55 - 00:00 |
| :---:       |    :----:   |     :---: | :---: | :---: | :---: |
| Road 1      |         | 30.5       |        | ... |
| Road 2      | 50.0      |        |    20.8   | ... | 40.3
| Road 3      |         |   40.7     |       | ... |
| ...         | ...        | ...         | ...    | ... | ...
| Road N      |    20.0     |   30.6     |     | ... | 40.5


### Final Goal

Infer the missing data using data imputation methods based on all historical data.


## Data format

The format of the data file is as follows,
![Data Format](images/Data_Feed.PNG)


### columns:

    'vehicle_id'
    'route_id_curr': the route number,
    'direction': possible values 0, 19, and 20, where 19 may denote inbound, and 20 for outbound.
    'block_id'
    'service_type'
    'deviation'
    'next_tp_est':
    'next_tp_sname':
    'next_tp_sched':
    'X': latitude
    'Y': longitude
    'location time':
    'route logon id'
    'block_num'
    'off route'
    'run_id'


## Process data

- [ ] Preprocess
  - [x] Single file
    - [x] Remove the last comma
    - [x] Remove the rows that have `vehicle_id >= 8000`
      - what are these?
      - According to [Wikipedia](https://en.wikipedia.org/wiki/NFTA_fleet#Buses) they are vehicle purchase during 1993 - 1996
    - [x] Remove the rows that have `route_id_curr == 0`
        - what are these?
    - [x] Remove the rows that have `route_id_curr > 111`
    - [x] Remove the rows that have `location time` out of time range that we are interested in, e.g., 6am to 9pm
  - [x] Merge the files under each folder (daily) into one single file, i.e., `yyyymmdd.csv`
    - [x] The columns that are useful and kept are: `vehicle_id`, `route_id_curr`,`direction`, `block_id`, `next_tp_est`, `next_tp_sname`, `next_tp_sched`, `X`, `Y`, `location time`, and the added columm `datatime` which is used for better readability.
    - [x] Sort the data based on `vehicle_id`, `route_id_curr`, `direction`, and `location time`.
- [ ] Get the travel time/speed on each road segment from the GPS data
  - [ ] Get all road segments (usually between road intersections) that are traveled by at least one bus route. The bus routes can be found [here](https://metro.nfta.com/). Road segments are directional.
    - [ ] Each road segments should be marked/denoted by a series of geographical points
    - [ ] Save road segments with information into files, e.g., `road segment ID`, `road intersection 1 ID`, `road intersection 2 ID`.
      - [ ] We need to mark/record/store road intersections first, e.g., `road intersection ID`, `latitude`, `longitude`
    - [ ] Create files to store the route information, including lists of `road segments ID`s in **inbound** and **outbound** directions. `json` should be a good choice.
      - One file to contain all routes, or one seperate file for each route
    - [ ] Show the road segments and intersections on Maps, e.g., my google maps.
    - [ ] Make use of tools like OpenStreetMap
    - [ ] Manually pick up
  - [ ] Map raw GPS data onto corresponding road segments
     - [ ] Make use of the fact that if a GPS point comes from a certain bus route, then it can only been mapped onto one road segment that belongs to that route.
     - [ ] Due to low sampling rate, there might be less than two points on certain road segment. Need to use interpolation and other ways to solve
  - [ ] Save the results so that
    - [ ] They can be easily loaded/used by other programs
    - [ ] They can be easily updated when there are new data coming in

The bus might stop at some location for a long period


## Implementation Details of the First Stage

The four jupyter notebook files here are used to interpret the information found in the merged csv data files and save them in a format that can better compute road speeds in Buffalo.

### osm_interpreter.ipynb

This notebook has the code to convert an osm file downloaded from openstreetmap and find all of the NFTA routes and save their information in a dictionary. For debugging purposes, the NFTA roads that are found are also plotted. Using pickle, 3 dictionaries and 1 list are saved.

1. final_node_table

final_node_table was a dictionary that stored the node id and the latitude/longitude coordinates as a key value pair.

2. final_way_table

final_way_table was a dictionary that stored```` the way id and a list of node id's as a key value pair.

3. final_relation_table

final_relation_table was a dictionary that stored the relation id and a tuple that had a list of nodes and ways and a list of tags. The list of nodes and ways were the stops and streets that made up a specific NFTA route. Nodes are usually included because the routes start and end at points that are generally not the natural endpoint of a road. The tags are useful because they possess information on the route like its name and what type of vehicle traverse the route (e.g. bus).

4. relations

relations is a list that contains the same information as final_relation_table, albeit in a less easily accessed form of a list of 3-tuples.

### find_nearest_road.ipynb

This jupyter notebook is not necessary for the final execution of the code, but it is useful for demoing and testing the effectiveness of the math I'm using for finding the nearest road to a specific latitude and longitude coordinate. Essentially, all of the ways (roads) within 0.006&deg; are found and then the projection of the point onto each of these ways is calculated. The closest projection is assumed to be the actual location of point and the road it is on is the nearest road.

The math for this takes advantage of the small scope of the area of Buffalo. Because of this, we can assume that latitude and longitude are a grid coordinate system and compute the vectors using latitude and longitude. This results in slight inaccuracies in measurement. However, for the final distance, the haversine formula is used to find the projection or end of a way that is closest to the point we have. The haversine formula is much closer to the true distance between points, though some inaccuracy remains due to rounding on the radius of the Earth.

The capability is accurate enough for our purposes and its ability is demonstrated in this jupyter notebook.

### reformat_data.ipynb

reformat_data.ipynb was made necessary in order to parse the data in a more convenient manner. The data is first separated by bus and then resorted by time, from earliest to latest. This was necessary to accurate plot the path and direction the bus travels in throughout the day.

### find_traffic_speed.ipynb

After the osm_interpreter.ipynb has been run at least once to generate the nodes, ways (roads), and relations (routes) of the Buffalo region and reformat_data.ipynb has been run on the data we wish to parse, we can execute the code in find_traffic_speed.ipynb.

Using 5 minute intervals, there are a total of 288 intervals that must be accounted for, so the final result is a dictionary. The keys are the way id's. The values are lists/arrays that have a length of 288, which is the number of intervals if we have 5 minute intervals for a whole day. Accordingly, [0] is the 00:00 - 00:05 interval up to [287], which is 11:55 - 00:00.

We take every consecutive datapoint in the same time interval and find the road, distance, and time between the two. The speed we find is added to the road(s) that are involved in the calculation.

After we go through every datapoint, we average the speeds we found for every road to get the final result.

The final result is a dictionary of road speeds with the pair (way id : average speed).

This dictionary is saved using pickle and can be reloaded at any time for future calculations.
