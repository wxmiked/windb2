#!/usr/bin/env python3
#
#
# Mike Dvorak
# Sail Tactics, LLC
# mike@sailorsenergy.com
#
# Created: 2015-10-30
# Modified: 2016-12-20
#
#
# Description: Inserts a hourly MERRA2 netCDF file into a WinDB2
#


import logging
import time
import sys
import numpy
import argparse
from windb2 import windb2
from windb2.struct.geovariable import GeoVariable
from datetime import datetime, timedelta
from netCDF4 import Dataset, num2date
import re

# Logging
logging.basicConfig(level=logging.WARNING)

# Parse the arguments
parser = argparse.ArgumentParser()
parser.add_argument("dbHost", type=str, help="Hostname of WinDB")
parser.add_argument("dbUser", type=str, help="User of WinDB")
parser.add_argument("dbName", type=str, help="Database name of WinDB")
parser.add_argument("vars", type=str, help="CSV list of MERRA2 variable names e.g. \"u50m,v50m\"")
parser.add_argument("ncFile", type=str, help="MERRA2 netCDF file")
args = parser.parse_args()

# Open the netCDF file
ncfile = Dataset(args.ncFile, 'r')

# Get the times
timevar = ncfile.variables['time']
timearr = num2date(timevar[:], units=timevar.units)

# Get the coordinates
longitudearr = ncfile.variables['lon'][:]
latitudearr = ncfile.variables['lat'][:]

# # Get the variables to read
# varsToInsert = []
# for var in re.findall('([a-z]+)([0-9]*)([a-z]*)',args.vars):
#




# Open the WinDB
curs, conn = windb2.connect(args.dbHost, args.dbName, args.dbUser)

# Iterate through all the dates
currDate = args.dateStartIncl
u50m = {}
v50m = {}
while currDate <= args.dateEndIncl:

    # Info
    print(currDate.date())

    # Date specific format
    urlEnd = currDate.strftime('%Y/%m/MERRA' + merraStreamNumber(currDate) + '.prod.assim.tavg1_2d_slv_Nx.%Y%m%d.hdf')

    try:
        logging.debug('Downloading: ' + urlStart + urlEnd)
        dataset = pydap.client.open_url(urlStart + urlEnd)
    except pydap.exceptions.ServerError:
        logging.error("Invalid URL: " + urlStart + urlEnd)
        sys.exit(-2)
    except Exception: # See if we've overloaded the server and if waiting helps
        logging.error('Caught exception probably from NASA. Waiting 3 minutes before continuing...')
        time.sleep(180)
        dataset = pydap.client.open_url(urlStart + urlEnd)


    # Get the long/lat coords for the first use
    if currDate == args.dateStartIncl:

        # Download the coordinates
        longitude = dataset['XDim_EOS']
        latitude = dataset['YDim_EOS']

        longitudeIndex = numpy.argwhere(numpy.around(longitude, 3) == numpy.around(args.longitude, 3))[0, 0]
        latitudeIndex = numpy.argwhere(numpy.around(latitude, 3) == numpy.around(args.latitude, 3))[0, 0]

        # Debug
        logging.debug('Found coordinate: (longIndex, latIndex) = (' + str(longitudeIndex) + ',' + str(latitudeIndex) + ')')
        logging.debug('Found coordinate: (long, lat) = (' + str(longitude[longitudeIndex][0]) + ',' + str(latitude[latitudeIndex][0]) + ')')

        # Make sure that the coordinates are valid
        if longitudeIndex.shape == (0, 1) or latitudeIndex.shape == (0, 1):
            logging.error('Coordinate that you gave do not exist in the MERRA dataset.')
            logging.error('Coordinate: (long, lat) = (' + str(args.longitude) + ',' + str(args.latitude) + ')')
            sys.exit(-3)

    # Download the 50 m wind data for those points. Sometimes this fails because the NASA server is overloaded, so retry
    # up to three times before moving on.
    try:
        u50m[currDate] = dataset.U50M[:, latitudeIndex, longitudeIndex]
    except Exception:
        try:
            u50m[currDate] = dataset.U50M[:, latitudeIndex, longitudeIndex]
            logging.warning('Exception trying to download U50M, retrying...')
        except Exception:
            try:
                u50m[currDate] = dataset.U50M[:, latitudeIndex, longitudeIndex]
                logging.warning('Exception trying to download U50M, retrying...')
            except Exception:
                try:
                    u50m[currDate] = dataset.U50M[:, latitudeIndex, longitudeIndex]
                    logging.warning('Exception trying to download U50M, retrying...')
                except Exception:
                    logging.warning('Download failed for: ' + str(currDate.date()))
                    continue
    try:
        v50m[currDate] = dataset.V50M[:, latitudeIndex, longitudeIndex]
    except Exception:
        try:
            v50m[currDate] = dataset.V50M[:, latitudeIndex, longitudeIndex]
            logging.warning('Exception trying to download V50M, retrying...')
        except Exception:
            try:
                v50m[currDate] = dataset.V50M[:, latitudeIndex, longitudeIndex]
                logging.warning('Exception trying to download V50M, retrying...')
            except Exception:
                try:
                    v50m[currDate] = dataset.V50M[:, latitudeIndex, longitudeIndex]
                    logging.warning('Exception trying to download V50M, retrying...')
                except Exception:
                    logging.warning('Download failed for: ' + str(currDate.date()))
                    continue

    # Make sure that U and V wind arrays are the same size
    assert u50m[currDate].shape == v50m[currDate].shape

    # Debug
    logging.debug('numpy.average(u50m[currDate]) = ' + str(numpy.average(u50m[currDate])))
    logging.debug('numpy.average(v50m[currDate]) = ' + str(numpy.average(v50m[currDate])))

    # Create new WindData objects to insert
    windData = []
    timeCount = 0
    for u, v in zip(u50m[currDate], v50m[currDate]):
        currTime = currDate + timedelta(minutes=30) + timeCount*timedelta(minutes=60)
        windData.append(WindData(currTime, 50,
                        numpy.sqrt(numpy.power(u[0, 0], 2) + numpy.power(v[0, 0], 2)),
                        WindData.calcDirDeg(u[0, 0], v[0, 0])))
        timeCount += 1

    # Insert the date into the WinDB
    windb.insertWindData(curs, conn, 'MERRA ' + str(args.longitude) + ' ' + str(args.latitude),
                         'NASA', windData, longitude=args.longitude, latitude=args.latitude)

    # Go on to the next date
    currDate += timedelta(days=1)
