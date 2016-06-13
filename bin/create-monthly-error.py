#!/usr/bin/env python3
#
#
# Mike Dvorak
# Stanford University
# dvorak@stanford.edu
#
# Created: 2007-07-11
# Modified: 2015-12-24
#
#
# Description: This script creates a four pane plot of the average
# windspeed of the buoy and nearest WRF points, grouped by hour in the
# day.  It also creates a .csv file of the standard deviation,
# normalized gross error, normalized bias, and the root mean square
# error.
# 

import os
import sys
dir = os.path.dirname(__file__)
sys.path.append(os.path.join(dir, '../'))
from windb2.model.wrf import plot
from windb2.model.wrf import error
import re
import numpy
import datetime
import argparse
import logging
from windb2 import windb2

# Logging
logging.basicConfig(level=logging.DEBUG)

parser = argparse.ArgumentParser(description='creates a four pane plot of the average windspeed of the buoy and ' +
                                             'nearest WRF points, grouped by hour in the day.  It also creates a .csv ' +
                                             'file of the standard deviation, normalized gross error, normalized bias, ' +
                                             'and the root mean square error.')

# Set the DB name
parser.add_argument('dbHost', help='Database hostname')
parser.add_argument('dbUser', help='Database user')
parser.add_argument('dbName', help='Database name')
parser.add_argument('year', type=int, help='4 digit year')
parser.add_argument('months', type=str, help='Single of comma-separted list of months')
parser.add_argument('timeDeltaMinutes', type=int, help='Frequency of observation that should be compared to WRF')
parser.add_argument('buoyRangeLowHeight', type=int, help='Lowest height that should be compared')
parser.add_argument('buoyRangeHighHeight', type=int, help='Highest height that should be compared')
parser.add_argument('wrfHeight', type=int, help='Height of WRF that should be compared')
parser.add_argument('noteForRecord', help='Note that will be kept in error table')
parser.add_argument('-p', '--port', type=int, default='5432', help='Port for WinDB2 connection')
args = parser.parse_args()

# Try parse the months, which could be a single integer or a csv list of integers
try:
    months = [int(args.months)]
except ValueError:
    logging.debug('month string: ' + args.months)
    months = []
    for month in re.findall(r'\d+', args.months):
        months.append(int(month))

# Connect to the WinDB
windb2 = windb2.WinDB2(args.dbHost, args.dbName, args.dbUser, port=args.port)
windb2.connect()

# Get all the domain numbers of the WRF runs
windb2.curs.execute("SELECT key FROM domain WHERE datasource LIKE '%WRF%'")
wrfDomains = windb2.curs.fetchall()

# For each domain, find the WRF points closest to the buoys
for domain in wrfDomains:

    # Set the results
    wrfDomain = domain[0]

    logging.info('Running the calculation for WRF domain: {}'.format(wrfDomain))
    wrfBuoyResults = error.findBuoysInProximityToWRFPoints(wrfDomain, windb2.curs)

    # Print out the results
    print("wrfDomain,buoyName,year,month,wrfAvg,buoyAvg,nge,nb,rmse,bias,percentComplete,wrfStddev,buoyStddev")
    logging.debug("wrfkey,\tbuoydomain,\tbuoykey,\tdistmeters")
    for wrfBouyPair in wrfBuoyResults:

        # Assign the results
        wrfKey = wrfBouyPair[0]
        buoyDomain = wrfBouyPair[1]
        buoyKey = wrfBouyPair[2]
        distMeters = wrfBouyPair[3]
        logging.debug("\t {} \t\t {} \t\t {}".format(wrfBouyPair[1], wrfBouyPair[2], wrfBouyPair[3]))

        # Get the name of the buoy
        buoyNameSql = "SELECT name FROM domain WHERE key=" + str(buoyDomain)
        windb2.curs.execute(buoyNameSql)
        buoyName = windb2.curs.fetchone()[0]

        # Calculate the error for each WRF point and buoy pair
        # Add this back into the query to use the cutoff  b.speed>=1.5 AND\
        for month in months:

            # Calculate the buoy error for this month
            startTime = datetime.datetime(args.year, month, 1)
            if month < 12:
                endTime = datetime.datetime(args.year, month + 1, 1)
            elif month == 12:
                endTime = datetime.datetime(args.year + 1, 1, 1)
            percentComplete = error.calculateBuoyErrorForPeriod(windb2.conn, wrfDomain, wrfKey, args.wrfHeight,
                                                                        buoyDomain, args.buoyRangeLowHeight,
                                                                        args.buoyRangeHighHeight,
                                                                        startTime, endTime, args.noteForRecord)

            # Create the plot of the wrf and buoy wind speeds is more than 50% complete
            logging.info("Dataset: {}% complete".format(percentComplete))
            if percentComplete > 10:
                plot.plotBuoyWRFWindSpeedPerMonth(args.year, month, args.timeDeltaMinutes, wrfDomain, wrfKey,
                                                        args.wrfHeight, buoyDomain, windb2.curs)
            else:
                continue


            #
            # CREATE BUOY AND WRF HISTOGRAMS
            #


            # Get the buoy name
            sql = " SELECT name FROM domain WHERE key=" + str(buoyDomain)

            # Execute the query
            windb2.curs.execute(sql)

            # Get the results
            buoyName = windb2.curs.fetchone()[0]



            # Create the histogram of the buoy
            sql = " SELECT speed FROM wind_" + str(buoyDomain) \
                  + " WHERE date_part('month',t)=" + str(month) + \
                  " AND date_part('year',t)=" + str(args.year) + " AND height>=" + str(args.buoyRangeLowHeight) + \
                  " AND height<=" + str(args.buoyRangeHighHeight)

            # Execute the query
            windb2.curs.execute(sql)

            # Get the results, continuing on if there is an IndexError (means no results)
            try:
                timeSeriesToPlot = numpy.array(windb2.curs.fetchall())[:, 0]
            except IndexError:
                logging.warning("WARNING (histogram): There were no buoy data in ", str(args.year), "-", str(month),
                                " buoy domain ", str(buoyDomain), " that matched")
                continue

            # Create the plot
            outputName = buoyName + "   " + str(args.year) + "-" + str(month)
            plot.createHistogramForTimePeriod(timeSeriesToPlot, 20, "orange", outputName, outputName)

            # Create the histogram of WRF at the closest location
            sql = " SELECT m.speed \
                 FROM wind_" + str(domain[0]) + " m \
                 WHERE m.geomkey=" + str(wrfKey) + " AND \
                 m.height=" + str(args.wrfHeight) + " AND \
                 date_part('month',m.t)=" + str(month) + " AND \
                 date_part('year',m.t)=" + str(args.year)

            # Execute the query
            windb2.curs.execute(sql)

            # Get the results
            timeSeriesToPlot = numpy.array(windb2.curs.fetchall())[:, 0]

            # Make sure there is actually WRF data to plot
            if len(timeSeriesToPlot) == 0:
                logging.warning("WARNING: There were no WRF data in ", str(args.year), "-", str(month), " WRF domain ",
                                str(wrfDomain), "at ", str(args.wrfHeight), " m that matched")
                continue

            # Create the plot
            outputName = "WRF domain " + str(domain[0]) + " near " + buoyName + " " + str(args.year) + "-" + str(month)
            plot.createHistogramForTimePeriod(timeSeriesToPlot, 20, "green", outputName, outputName)

sys.exit(0)
