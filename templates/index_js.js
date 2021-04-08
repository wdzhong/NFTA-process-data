let way_and_points = null;
let map;
let polylines;  // save the Google Maps polyline "handlers" (list of object) s.t. we can clear them when needed.

function onload_func() {
    // set the value of the datetime picker
    document.getElementById("datetime_picker").value = new Date().toISOString().slice(0, 19);
    window.setInterval(current_time_update, 500);
    window.setInterval(function ()
    {get_traffic_for_given_time(new Date().getTime().toString().substr(0,10));}, 60000);
    load_way_structure()

}

function initMap() {
    map = new google.maps.Map(document.getElementById("map"), {
        center: {lat: 42.89, lng: -78.74},
        zoom: 12,
    });
}

/**
 * Get the traffic information back from the backend based on the value of the datetime picker.
 * And plot the traffic condition on the Google Maps.
 */
function get_traffic_for_given_time(timestamp) {
    console.log("Get traffic condition button clicked!");
    console.log(timestamp);  // e.g., 2021-03-03T20:30
    // A number representing the milliseconds elapsed since January 1, 1970, 00:00:00 UTC, e.g., 1614821400000

    const time_interval = '15';  // TODO: get the value from the UI
    const query_str = '/get_traffic_data/' + timestamp + '/' + time_interval;
    ajaxGetRequest(query_str, get_traffic_for_selected_time_callback);
}

function get_traffic_for_selected_time_callback(raw_json){
    let traffic_info = JSON.parse(raw_json);
    // console.log(traffic_info);
    // console.log(traffic_info['road_speed'][0]['points']);
    clear_polylines_from_google_maps();
    plot_traffic_on_google_maps(traffic_info['road_speed']);
}

/**
 * Load the way structure, i.e., way id and the associated points.
 */
function load_way_structure() {
    ajaxGetRequest("static/mapdata/way_structure.json", load_way_structure_callback);
}

/**
 *
 * @param raw_json {string} way_structure - {way_id: [[Latitude, Longitude], [Latitude, Longitude], ... ]}
 */
function load_way_structure_callback(raw_json){
    way_and_points = JSON.parse(raw_json);
    get_traffic_for_given_time(new Date().getTime().toString().substr(0,10));
}

/**
 * Plot the traffic conditions on the Google Maps.
 * @param {Object} road_speed - {way_id: {'speed': float, 'speed_ratio': float}}
 * @return null
 */
async function plot_traffic_on_google_maps(road_speed) {
    polylines = [];
    const way_ids = Object.keys(way_and_points);
    let way_length = way_ids.length
    for (let i = 0; i < way_length; i++) {
        const points = way_and_points[way_ids[i]];
        let coordinates = [];
        for (let i = 0; i < points.length; i++) {
            coordinates.push({lat: points[i][0], lng: points[i][1]});
        }
        // const speed = road_speed[i]['speed'];
        const speed_ratio = road_speed[way_ids[i]]['speed_ratio'];

        const polyline = new google.maps.Polyline({
            path: coordinates,
            geodesic: true,
            strokeColor: get_color_based_on_speed(speed_ratio),
            strokeOpacity: 1.0,
            strokeWeight: 4,
        });
        polyline.setMap(map);
        polylines.push(polyline);
    }
}

/**
 * Clear/Remove the existing polylines from the map.
 */
function clear_polylines_from_google_maps() {
    console.log("Clear maps");
    if (polylines === undefined) return;
    for (let i = 0; i < polylines.length; i++) {
        polylines[i].setMap(null);
    }
}

/**
 * Get the line color based on the traffic condition.
 * @param {float} speed_ratio - The ratio between the traffic speed and the speed limit of that road segment.
 * @return {string} the color of the line.
 */
function get_color_based_on_speed(speed_ratio) {
    // TODO: adjust the thresholds; maybe add more levels
    if (speed_ratio < 0.2) {
        return "#FF0000";
    }
    if (speed_ratio < 0.4) {
        return "#eb9c34";
    }
    return "#34eb95";
}

function current_time_update() {
    document.getElementById('clock').innerHTML = new Date().toLocaleTimeString('en-US')
}

function addZero(i) {
    if (i < 10) {
        i = "0" + i
    }  // add zero in front of numbers < 10
    return i;
}

function ajaxPostRequest(path, data, callback) {
    let request = new XMLHttpRequest();
    request.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            callback(this.response);
        }
    };
    request.open("POST", path);
    request.send(data);
}

function ajaxGetRequest(path, callback) {
    let request = new XMLHttpRequest();
    request.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            callback(this.response);
        }
    };
    request.open("GET", path);
    request.send();
}