#!/usr/bin/env python
#
#
# Mike Dvorak
# Sailor's Energy
# mike@sailorsenergy.com
#
# Created: 2008-10-28
# Modified: 2015-12-24
#
#
# Description: Inserts NDBC buoy data into a PostgreSQL wind database.
#

# Add the WinDB2 lib
import os
import sys

dir = os.path.dirname(__file__)
sys.path.append(os.path.join(dir, '../'))

import dap
import dap.client
import time
import pytz
import string
import numpy
import argparse
from windb2 import windb2, insert
from windb2.struct import winddata
from datetime import datetime

# Parse the arguments
parser = argparse.ArgumentParser()
parser.add_argument('dbHost', help='Database hostname')
parser.add_argument('dbUser', help='Database user')
parser.add_argument('dbName', help='Database name')
parser.add_argument("obs_name", type=str, help="NDBC code for observation.")
parser.add_argument("height", type=str, help="")
parser.add_argument("yearNum", type=str, help="")
parser.add_argument("dataFlavor", type=str, choices=["stdmet", "cwind", "curryear"], help="")
parser.add_argument("-n", "--noDataDownload", action="store_true",
                    help="Do not download data, just insert the existing station.dat file.")
parser.add_argument("-o", "--overwrite", help="Replace data if the data for the time exists in the WinDB2",
                    action="store_true")
parser.add_argument('-p', '--port', type=int, default='5432', help='Port for WinDB2 connection')
args = parser.parse_args()

# Connect to the WinDB
windb2 = windb2.WinDB2(args.dbHost, args.dbName, args.dbUser, port=args.port)
windb2.connect()

# Create the WinDB2 inserter
inserter = insert.Insert(windb2)

# See if we are supposed to download the data
dataDownload = not args.noDataDownload

# Info
print("Downloading ", args.yearNum, ' ', args.dataFlavor, ' data for NDBC: ', args.obs_name)

# Get the buoy windSpd dataset from NDBC (variable called 'cwind')
# url = 'http://dods.ndbc.noaa.gov/cgi-bin/nph-dods/dods/cwind/' + args.obs_name + '/' + args.obs_name + 'c' + args.yearNum + '.nc'
if args.dataFlavor == 'stdmet':
    url = 'http://dods.ndbc.noaa.gov/thredds/dodsC/data/stdmet/' + string.lower(args.obs_name) + '/' + string.lower(
        args.obs_name) + 'h' + args.yearNum + '.nc'
elif args.dataFlavor == 'cwind':
    url = 'http://dods.ndbc.noaa.gov/thredds/dodsC/data/cwind/' + string.lower(args.obs_name) + '/' + string.lower(
        args.obs_name) + 'c' + args.yearNum + '.nc'
elif args.dataFlavor == 'curryear':
    url = 'http://dods.ndbc.noaa.gov/thredds/dodsC/data/stdmet/' + string.lower(args.obs_name) + '/' + string.lower(
        args.obs_name) + 'h9999.nc'

try:
    dataset = dap.client.open(url)
except dap.exceptions.ServerError:
    print("Invalid URL: " + url)
    sys.exit(-2)

# Info
print("Downloading data from: ", url)

# Print out the keys
print(dataset.keys())

# Get long/lat
long = dataset['longitude'][0]
lat = dataset['latitude'][0]

# Download the time
timeVar = dataset['time']
print("time shape: ", str(timeVar.shape))
print("time dim: ", str(timeVar.dimensions))
print("time units: ", str(timeVar.units))

# Debug
print("The longitude, latitude = " + str(long) + ", " + str(lat))

# Download the windspeed data
windSpd = dataset['wind_spd']

# Debug
windVar = dataset['wind_spd']
print("windSpd shape: ", str(windVar.shape))
print("windSpd dim: ", str(windVar.dimensions))
print("windSpd units: ", str(windVar.units))

# Download the buoy data for that year
filename = str(args.obs_name) + "c" + args.yearNum + ".dat"
f = open(filename, "w")

# Get all the time and windsped series for the year
if dataDownload:
    # print "Downloading all of the time"
    t = dataset['time'][:]
    print("Downloading all of the wind speeds")
    windSpd = dataset['wind_spd'][:]
    windDir = dataset['wind_dir'][:]
else:
    print('Not downloading any data....')
    time = numpy.zeros(0)
    windSpd = numpy.zeros(0)
    windDir = numpy.zeros(0)

# Loop through all times in the year
count = 0
windData = []
for i in range(windSpd.shape[0]):

    # Make sure this is the correct year (really only useful for downloading "real-time" data)
    currTime = datetime.utcfromtimestamp(t[i]).replace(tzinfo=pytz.utc)
    if currTime < datetime.strptime(args.yearNum + '-01-01 00:00:00', "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.utc):
        continue

    # Make sure we don't have a dummy value
    pgSqlTime = str(time.strftime("%Y-%m-%d %H:%M:%SZ", time.gmtime(t[i])))
    if windSpd[i] != 99.0 and windDir[i] != 999:

        windData.append(winddata.WindData(currTime, args.height, windSpd[i], windDir[i]))

        # Debug
        if count % 1000 == 0:
            print("Passing time: " + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(t[i])))

        # Move on to the next
        count += 1

# Close the file
f.close()

# Insert the data, using a 1000 m tolerance because the NDBC stations have varying precision for their coordinates
# over various years
inserter.insert_wind_data(args.obs_name, "National Data Buoy Center", windData, longitude=long, latitude=lat,
                          replace_data=args.overwrite)
