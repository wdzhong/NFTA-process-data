
## All Routes of NFTA

[![All Routes](images/all_routes.jpg)](http://metro.nfta.com/)

But there is route `17` in the data. The picture might be outdated.


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
