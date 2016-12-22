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
parser.add_argument('vars', type=str, help="CSV list of MERRA2 variable names e.g. 'u50m,v50m'")
parser.add_argument('long', type=float, help='Longitude to download surrounding MERRA2 nodes for')
parser.add_argument('lat', type=float, help='Latitude to download surrounding MERRA2 nodes for')
parser.add_argument('ncFile', type=str, help='MERRA2 netCDF file')
args = parser.parse_args()

# Open the WinDB2
windb2conn = windb2.WinDB2(args.dbHost, args.dbName, args.dbUser)
windb2conn.connect()

# Insert the MERRA2 netCDF file
util.insert_merra2_file(windb2conn, args.ncFile, args.vars)