import helper.api_key as api_key

# When it is True, the program will return more things for debug purpose
FLAG_DEBUG = False
# find_nearest_road debug will print lot more information then a general debug print. It is config by a separate flag
FLAG_FIND_NEAREST_ROAD_DEBUG = False

# Google Map API key for generate map
# Get API key https://developers.google.com/maps/documentation/javascript/get-api-key
GOOGLE_MAPS_API_KEY = api_key.GOOGLE_MAPS_API_KEY

# File path setting

# Unless otherwise stated,
# {0} represent date_str: 8 digit number of the date_str in yyyyMMdd format (e.g. 20200731)
# {1} represent interval: The length of each time interval in minutes. The input number should be divisible by 1440
#                         (24 hour * 60 min) by default it is 5 min
CONFIG_DATA_FOLDER = "data/"
CONFIG_SINGLE_DAY_FOLDER = "data/{0}"
CONFIG_ALL_DAY_RAW_DATA_FILE = "data/{0}/{0}.csv"
CONFIG_RAW_DATA_FOLDER = "data/{0}/raw"
CONFIG_SINGLE_DAY_RESULT_FILE = "data/{0}/result/{0}_{1}_min_road.csv"

# save_type
SAVE_TYPE_JSON = 1
SAVE_TYPE_PICKLE = 2

# process_data
# The program will only read the data from PROCESS_DATA_START_TIME to PROCESS_DATA_END_TIME
PROCESS_DATA_START_TIME = 0
PROCESS_DATA_END_TIME = 24

# predict_road_condition
# See predict_road_condition() in predict_road_condition.py for more detail of each variable
PREDICT_ROAD_CONDITION_CONFIG_HISTORY_DATE = [-1, -2, -3, -7, -14, -21, -28, -35, -42, -49, -56, -63, -70]
PREDICT_ROAD_CONDITION_CONFIG_HISTORY_DATA_RANGE = [-1, 1, -2, 2, -3, 3, -4, 4, -5, 5, -6, 6]
PREDICT_ROAD_CONDITION_CONFIG_WEIGHT = [0.08821194073566006, 0.08402736745847723, 0.09180261375018595,
                                        0.09567173256541667, 0.06638586102785468, 0.057538022745280304,
                                        0.03803083890311526, 0.08628806480829161, 0.08805171256460817,
                                        0.08184255395533459, 0.07774612670061147, 0.06883249115674404,
                                        0.06392337112461549]

# generate_prediction_in_large_batches (GPILB)
# See save_path in predict_speed_dict_to_json() in script/generate_prediction_in_large_batches.py for more detail
# This variable also use in retrieve_traffic_data() in homepage.py
GPILB_CACHE_PATH = "cache/predict_result/{0}/{1}/{2}.json"
