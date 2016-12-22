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
from windb2.model.merra2 import util
from windb2.struct import geovariable, insert
from netCDF4 import Dataset, num2date
import re
from datetime import datetime, timedelta


# Logging
logging.basicConfig(level=logging.WARNING)

# Parse the arguments
parser = argparse.ArgumentParser()
parser.add_argument('dbHost', type=str, help='Hostname of WinDB')
parser.add_argument('dbUser', type=str, help='User of WinDB')
parser.add_argument('dbName', type=str, help='Database name of WinDB')
parser.add_argument('vars', type=str, help="CSV list of MERRA2 variable names e.g. 'u50m,v50m' or 'windenergy' to get t10m,u10m,v10m,t2m,u2m,v2m,u50m,v50m,ps,disph")
parser.add_argument('long', type=float, help='Longitude to download surrounding nodes for')
parser.add_argument('lat', type=float, help='Latitude to download surrounding nodes for')
parser.add_argument('ncFile', type=str, help='MERRA2 netCDF file')
parser.add_argument('-d', '--download', action="store_true", help='Download all available times for the surrounding nodes')
parser.add_argument('-i', '--insert', action="store_true", help='Inserts all files files for surrounding nodes')
args = parser.parse_args()

# See if we are using a predefined set of vars
if args.vars == 'windenergy':
    args.vars = 't10m,u10m,v10m,t2m,u2m,v2m,u50m,v50m,ps,disph'

# Open the WinDB2
windb2conn = windb2.WinDB2(args.dbHost, args.dbName, args.dbUser)
windb2conn.connect()

# Download all of the MERRA2 netCDF file from the begginning of time
if args.download:

    # Get the coordinate range of the surrounding coords
    # If the coodinate happens to be a MERRA node, only one node will be downloaded
    longRange, latRange = util.get_surrounding_merra2_nodes(args.long, args.lat)

    # Download all of the MERRA2 data
    util.download_all_merra2(windb2conn, args.long, args.lat, args.vars, dryRun=True)

# Insert the MERRA2 netCDF file
if args.insert:

    # Insert the files
    # TODO add file globbing
    util.insert_merra2_file(windb2conn, args.ncFile, args.vars)