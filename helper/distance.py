import math

# def compute_poly_fit(deg, delta):
#     x = []
#     y = []
#     temp_x = 41.0
#
#     while temp_x <= 44.0:
#         x.append(temp_x/100.0)
#         y.append(math.cos(math.radians(temp_x/100.0)))
#         temp_x += delta
#
#     poly_function = np.polyfit(x, y, deg)
#     print(poly_function)
#     print(np.poly1d(poly_function))
#     return 0
# when deg = 3, delta = 0.001, we get following result
#                3             2
# y = 6.665e-09 x - 0.0001523 x + 1.237e-09 x + 1
# when deg = 2, delta = 0.001, we get following result
#                       2
# y = - 1.52304519e-04 x + -2.37416349e-09 x + 1


def distance(point1, point2):
    """
    A faster approach to compute distance, avoid using any sin and cos

    Get the distance between two point in km (kilometers)
    haversine formula for more precise distance calculation

    Parameters
    ----------
    point1: List of int
        Longitude and Latitude of first point

    point2: List of int
        Longitude and Latitude of first point

    Returns
    -------
    distance: float
        The distance between the two point in km (kilometers)
    """
    # Radius of earth at latitude 42.89 + elevation of buffalo, ny
    radius = 6368.276 + 0.183
    cos_poly = [6.66455110e-09, -1.52313017e-04, 1.23684191e-09, 1.00000000e+00]

    lat1, lng1 = point1
    lat2, lng2 = point2

    dx = lng2 - lng1
    dy = lat2 - lat1
    avg_lat = (lat1 + lat2) / 2
    x = (cos_poly[0] * avg_lat * avg_lat * avg_lat
         + cos_poly[1] * avg_lat * avg_lat
         + cos_poly[2] * avg_lat
         + cos_poly[3]) * math.radians(dx) * radius
    y = math.radians(dy) * radius

    result = math.sqrt(x * x + y * y)

    # old_result = distance_old(point1, point2)
    # print(result, "vs", old_result, "diff", result - old_result)

    return result


def distance_accurate(point1, point2):
    """
    Get the distance between two point in km (kilometers)
    haversine formula for more precise distance calculation

    Parameters
    ----------
    point1: List of int
        Longitude and Latitude of first point

    point2: List of int
        Longitude and Latitude of first point

    Returns
    -------
    distance: float
        The distance between the two point in km (kilometers)
    """
    # Radius of earth at latitude 42.89 + elevation of buffalo, ny
    radius = 6368.276 + 0.183

    lat1, lng1 = point1
    lat2, lng2 = point2

    theta1 = math.radians(lat1)
    theta2 = math.radians(lat2)
    phi1 = math.radians(lng1)
    phi2 = math.radians(lng2)

    result = 2 * radius * math.asin(math.sqrt(
        math.sin((theta2 - theta1) / 2) ** 2 + math.cos(theta1) * math.cos(theta2) * math.sin((phi2 - phi1) / 2) ** 2))

    return result