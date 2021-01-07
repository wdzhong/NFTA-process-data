import csv
import os
from pathlib import Path

import sys


def reformat_by_bus(date):
    """
    This cell breaks a compiled dataset into each individual bus per day.

    The data is named based on the day, so as long as the naming convention remains,
    you only have to change the day variable to match new datafiles and reformatting
    should work flawlessly.

    This part of the code separates the data into different files based on bus.

    Parameters
    ----------
    date: string
        8 digit number of the date. It should be a folder name in data
    """
    Path('data/{}/unsorted/'.format(date)).mkdir(parents=True, exist_ok=True)
    output = {}
    csv_writers = {}
    with open('data/{}.csv'.format(date), "r", newline='') as csv_file:
        reader_csv_file = csv.reader(csv_file)

        for row in csv_writers:
            bus_id = row[0]

            if bus_id not in output:
                output[bus_id] = open('data/{}/unsorted/{}.csv'.format(date, bus_id), 'w+', newline='')
                csv_writers[bus_id] = csv.writer(output[bus_id])

            csv_writers[bus_id].writerow(row)

    for bus_id, outputfd in output.items():
        outputfd.close()

    return 0


def sort_reformat_data(date):
    """
    This cell reorganizes the lines by time.

    This code sorts all of the separated bus data by time.

    Parameters
    ----------
    date: string
        8 digit number of the date. It should be a folder name in data
    """
    root = 'data/{}/'.format(date)
    unsorted_dir = root + 'unsorted/'
    sorted_dir = root + 'sorted/'
    Path(sorted_dir).mkdir(parents=True, exist_ok=True)

    for filename in os.listdir(unsorted_dir):
        data = []
        with open('{}{}'.format(unsorted_dir,filename), "r", newline='') as csv_file:
            unsort_csv_file = csv.reader(csv_file)
            data = list(unsort_csv_file)
            data = sorted(data, key=lambda x: x[9])
        with open('{}{}'.format(sorted_dir,filename), 'w+', newline='') as csv_file:
            sorted_csv_file = csv.writer(csv_file)
            for i in data:
                sorted_csv_file.writerow(i)
    return 0




if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("reformat_data.py [date]")
        print("")
        print("Require:")
        print("date       : 8 digit number of the date")
        print("             it is the folder name in data/")
        exit(0)
    date = sys.argv[1]
    reformat_by_bus(date)
    sort_reformat_data(date)
    print("Done")