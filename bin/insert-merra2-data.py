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
import os
import sys

dir = os.path.dirname(__file__)
sys.path.append(os.path.join(dir, '../'))

import logging
import argparse
from windb2 import windb2
from windb2.struct import geovariable, insert
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

# Open the WinDB2
windb2conn = windb2.WinDB2(args.dbHost, args.dbName, args.dbUser)
windb2conn.connect()

# For each variable...
for var in args.vars.split(','):

    # Break up the variable name
    var_re = re.match(r'([a-z]+)([0-9]*)([a-z]*)[,]*', var)

    # For each long
    longcount = 0
    longarr = ncfile.variables['lon']
    for long in longarr:

        # For each lat
        latcount = 0
        latarr = ncfile.variables['lat']
        for lat in latarr:

            # For each time in the variable
            tcount = 0
            varstoinsert = []
            for t in timearr:

                # Clean up the seconds because every other time has a residual
                t = t.replace(microsecond=0)

                # Figure out the height
                if var_re.group(2) is not None:
                    height = var_re.group(2)
                else:
                    height = -9999

                v = geovariable.GeoVariable(var, t, height,
                                            ncfile.variables[var_re.group(0)][tcount, latcount, longcount])
                varstoinsert.append(v)

                # Increment t
                tcount += 1

        # Insert the data
        insert.insertGeoVariable(windb2conn, "MERRA2", "NASA", varstoinsert, long, lat)

        # Increment lat
        latcount += 1

    # Increment long
    longcount += 1


