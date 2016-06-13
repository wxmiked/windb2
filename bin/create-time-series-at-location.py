#!/usr/bin/env python3
#
#
# Mike Dvorak
# Sailor's Energy
# mike@sailorsenergy.com
#
# Created: 2013-05-24
# Modified: 2015-10-19
#
#
# Description: This script creates a time series of at a specific long,lat coordinate over a given time period.
#
import os
import sys
dir = os.path.dirname(__file__)
sys.path.append(os.path.join(dir, '../'))
import argparse
from windb2.model.wrf import error
from windb2 import windb2
import pytz
import datetime
import numpy
import csv

# Set all the relevant args
parser = argparse.ArgumentParser(description='This script creates a time series of at a specific long,lat coordinate over a given time period')
parser.add_argument('dbHost', help='WinDB host')
parser.add_argument('dbUser', help='WinDB user')
parser.add_argument('dbName', help='WinDB name')
parser.add_argument('domain', help='WRF domain')
parser.add_argument('longitude', help='longitude is in degrees E (W is negative) and latitude is in degrees N (S is negative)')
parser.add_argument('latitude', help='latitude in degrees')
parser.add_argument('height', help='height in meters')
parser.add_argument('startDateIncl', help='start date inclusive in ISO form e.g. 2015-10-19')
parser.add_argument('startTimeIncl', help='start hour inclusive and minute in UTC e.g. 00:00')
parser.add_argument('endDateExcl', help='end date exclusive includes in ISO form e.g. 2015-10-19')
parser.add_argument('endTimeExcl', help='end hour and minute exclusive in UTC e.g. 00:00')
parser.add_argument('-p', '--port', type=int, default='5432', help='Port for WinDB2 connection')
args = parser.parse_args()

# Extract the time stamps
startTimeStampIncl = (datetime.datetime.strptime(args.startDateIncl + ' ' + args.startTimeIncl, "%Y-%m-%d %H:%M")).replace(tzinfo=pytz.utc)
endTimeStampExcl = (datetime.datetime.strptime(args.endDateExcl + ' ' + args.endTimeExcl, "%Y-%m-%d %H:%M")).replace(tzinfo=pytz.utc)


# Open the database
windb2 = windb2.WinDB2(args.dbHost, args.dbName, args.dbUser, port=args.port)
windb2.connect()

# Find the closest WRF point to the data
geomKey,distanceM = error.findWRFPointNearLongLat(args.domain, args.longitude, args.latitude, windb2.curs)

# Info
print("Found a data point geomkey=", geomKey, " in domain=", args.domain, " ", distanceM, "-meters from the long,lat=", args.longitude, ",", args.latitude)

# Get the buoy stats
sql = "SELECT t as t_utc, speed as speed_mps, direction " + \
             "FROM wind_" + str(args.domain) + " " + \
             "WHERE geomkey=" + str(geomKey) + " AND height=" + str(args.height) + \
                  " AND t>='" + str(startTimeStampIncl) + "' AND t<timestamp'" + str(endTimeStampExcl) + "' " + \
             "ORDER BY t_utc"
print("Executing: ", sql)
windb2.curs.execute(sql)
windSpeeds = numpy.array(windb2.curs.fetchall())

# Create the CSV file
outputName = 'wind-time-series-' + args.dbHost + '-' + args.dbName + '-domain-' + args.domain + '-height-' + \
             args.height + 'm-' + args.longitude + ','  + args.latitude + \
              str(startTimeStampIncl).replace(' ','_') + '-to-' + str(endTimeStampExcl).replace(' ','_') + '.csv'
with open(outputName, 'w') as csvfile:
    fieldNames = ['t_utc', 'speed_mps', 'direction']
    csvWriter = csv.DictWriter(csvfile, quotechar="'", quoting=csv.QUOTE_MINIMAL, fieldnames=fieldNames)
    csvWriter.writeheader()
    for row in windSpeeds:
        csvWriter.writerow({'t_utc': row[0], 'speed_mps': row[1], 'direction': row[2]})