
## All Routes of NFTA

[![All Routes](images/all_routes.jpg)](http://metro.nfta.com/)

But there is route `17` in the data. The picture might be outdated.


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
    - [ ] Make use of tools like OpenStreetMap
    - [ ] Manually pick up
  - [ ] Map raw GPS data onto corresponding road segments
     - [ ] Make use of the fact that if a GPS point comes from a certain bus route, then it can only been mapped onto one road segment that belongs to that route.
     - [ ] Due to low sampling rate, there might be less than two points on certain road segment. Need to use interpolation and other ways to solve
  - [ ] Save the results so that
    - [ ] They can be easily loaded/used by other programs
    - [ ] They can be easily updated when there are new data coming in

The bus might stop at some location for a long period
