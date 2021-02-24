import math

def time_range_index_to_str(time_range_index, time_slot_interval, delimiter=":", offset=0):
    time_in_min = (time_range_index * time_slot_interval)+offset
    h = math.floor(time_in_min / 60) % 24
    m = math.floor(time_in_min % 60)
    return "{:0>2d}{}{:0>2d}".format(h, delimiter, m)


def time_range_index_to_time_range_str(time_range_start_index, time_range_end_index, time_slot_interval, delimiter=":"):
    if time_range_start_index < 0:
        return "all day average"

    return "{} - {}".format(time_range_index_to_str(time_range_start_index, time_slot_interval,
                                                    delimiter=delimiter),
                            time_range_index_to_str(time_range_end_index, time_slot_interval,
                                                    delimiter=delimiter, offset=-1))