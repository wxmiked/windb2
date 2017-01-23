#!/usr/bin/env python3
#
#
# Mike Dvorak
# Postdoc
# UC Berkeley
# Civil and Environmental Engineering
# dvorak@berkeley.edu
#
# Created: 2013-07-09
# Modified: 2016-01-22
#
#
# Description: Inserts CSV files from Mesowest (mesowest.utah.edu). The CSV files are the type you get when you save
# the "CSV" files, which are actually html as "text" in Firefox.
#

# Add the WinDB2 lib
import os
import sys

dir = os.path.dirname(__file__)
sys.path.append(os.path.join(dir, '../'))

import csv
import re
import time
import sys
import math
from datetime import datetime, timedelta, tzinfo
import pytz
import urllib
import tempfile
from windb2 import windb2
from windb2.struct import winddata, insert
import argparse
from urllib.request import urlopen

def parseLocation(row):
    """Parses the location string at the beginning of the file.

Returns stationId, stationName, longitude, latitude"""

    # Rows look like this:
    # CALVP LOVELAND PASS 39.67472 -105.89389 3624 m CAIC
    r1 = re.match(b'^# (\w+) ([\(\)@\w /_-]+) ([0-9]+\.[0-9]+) ([-]*[0-9]+\.[0-9]+)', row)

    if r1 == None:
        raise ValueError("Location string didn't match: " + str(row))
    else:
        return r1.group(1), r1.group(2), r1.group(4), r1.group(3)


#
# Main executable
#

# Parse the arguments
parser = argparse.ArgumentParser()
parser.add_argument('dbHost', help='Database hostname')
parser.add_argument('dbUser', help='Database user')
parser.add_argument('dbName', help='Database name')
parser.add_argument("stationId", type=str, help="Mesowest code for observation.")
parser.add_argument("year", type=int, help="Year to download")
parser.add_argument("month", type=int, help="Month to download")
parser.add_argument("-o", "--overwrite", help="Replace data if the data for the time exists in the WinDB2",
                    action="store_true")
parser.add_argument('-p', '--port', type=int, default='5432', help='Port for WinDB2 connection')
args = parser.parse_args()


# Connect to the WinDB
windb2 = windb2.WinDB2(args.dbHost, args.dbName, args.dbUser, port=args.port)
windb2.connect()

# Set the times
startTime = datetime(args.year, args.month, 1).strftime('%Y%m%d%H%M')
if args.month > 12 or args.month < 1:
    raise ValueError('Illegal month num' + str(args.month))
elif args.month ==  12:
    endTime = (datetime(int(args.year) + 1, args.month + 1, 1) - timedelta(seconds=1)).strftime('%Y%m%d%H%M')
else:
    endTime = (datetime(args.year, args.month + 1, 1) - timedelta(seconds=1)).strftime('%Y%m%d%H%M')

# Download the file
tmpFile = tempfile.NamedTemporaryFile(mode='r+b',delete=False)
tmpFileName = tmpFile.name
url = "http://api.mesowest.net/v2/stations/timeseries?token=demotoken&stid={}&start={}&end={}&output=csv&units=english".format(args.stationId, startTime, endTime)
print('Downloading: ', url)
urlHandle = urlopen(url)
try:
    reader = urlHandle.read()
finally:
    # Write out the file
    print('Writing out the file to:', tmpFileName)
    tmpFile.write(reader)
    tmpFile.close()
    urlHandle.close()

# Open the Mesowest file to read as a plain old file first
print("Opening ", args.stationId)
reader = open(tmpFileName, "r")

# Get the location data
stationId = re.match('# STATION: (\w+)', reader.readline()).group(1)
stationName = re.match('# STATION NAME: (\w+)', reader.readline()).group(1)
latitude = re.match('# LATITUDE: ([0-9\\.\\-]+)', reader.readline()).group(1)
longitude = re.match('# LONGITUDE: ([0-9\\.\\-]+)', reader.readline()).group(1)
elevationFt = re.match('# ELEVATION \\[ft\\]: ([0-9]+)', reader.readline()).group(1)
state = re.match('# STATE: (\w+)', reader.readline()).group(1)

# Info
print('StationID: ', stationId)
print('Station name:', stationName)
print('Longitude: ', longitude)
print('Latitude: ', latitude)

# Make a dictionary of the column names as {'colName':colNum}
colNames = re.split(',',reader.readline())
colDict = {}
count = 0
for name in colNames:
    colDict[name.strip()] = count
    count += 1 

# Burn the units line
reader.readline()

# Convert the regular file to a CSV file
reader = csv.reader(reader)

# Insert all the rows of data
windData = []
count = 0
for row in reader:
    
    # Debug
    #print str(row)
    
    # Construct a timestamp, continuing on if there is a parse failure
    #t = datetime.strptime(row[colDict['Date_Time']], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=pytz.utc)
    #print(t)
    
    # Add data, if the wind speed and direction are not null
    if row[colDict['wind_speed_set_1']] != "" and row[colDict['wind_direction_set_1']] != "": 
        windData.append(winddata.WindData(row[colDict['Date_Time']], 10, float(row[colDict['wind_speed_set_1']]), float(row[colDict['wind_direction_set_1']])))
        
        # Increment count of valid data
        count += 1

# Info
print('Downloaded ', count, ' times of weather data.')

# Insert all of the data for that file. Necessary to do by file because of the large data sizes.
print('Inserting the surface data...')
insert.insertWindData(windb2, stationId, 'Mesowest', windData, longitude, latitude)

