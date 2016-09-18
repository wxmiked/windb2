#!/usr/bin/env python
#
#
# Mike Dvorak
# Sail Tactics
# mike@sailtactics.com
#
# Created: 2014-11-05
# Modified: 2014-12-20
#
#
# Description: Inserts a SUNTANS tide forecast netCDF file into a WindDB at the 0-m height. This script assumes that
# the winds are being inserted into a WRF forecast with the same XLONG and XLAT coordinates.
#
# Returns -1 if there is an IntegrityError, which is triggered by a duplicate key error if the data already exists. 
#

import os
import sys
dir = os.path.dirname(__file__)
sys.path.append(os.path.join(dir, '../'))

import scipy.io.netcdf as nc
import argparse
from windb2 import windb2, insert, util
from windb2.model.suntans import suntans
import logging

# Set up logging for InsertAbstract
logger = logging.getLogger('windb2')
logger.setLevel(logging.WARNING)
logging.basicConfig()

# Get the command line opts
parser = argparse.ArgumentParser()
parser.add_argument("db_host", type=str, help="Database hostname")
parser.add_argument("db_user", type=str, help="Database username")
parser.add_argument("db_name", type=str, help="Database name")
parser.add_argument("ncfile", type=str, help="SUNTANS netCDF file")
parser.add_argument("-r","--replace", help="Replace data if the data for the time exists in the WinDB2", action="store_true")
parser.add_argument("-w", "--where",  type=str, default="true", help="SQL where statement to exclude times")
group = parser.add_mutually_exclusive_group()
group.add_argument("-d", "--domainKey", help="Existing domain key in the WinDB")
group.add_argument("-n", "--new", action="store_true")
args = parser.parse_args()

# Connect to the WinDB
windb2 = windb2.WinDB2(args.db_host, args.db_name, dbUser=args.db_user)
windb2.connect()

# Open the tide netCDF file
ncFile = nc.netcdf_file(args.ncfile, 'r')

# Insert the file, domainKey should be None if it wasn't set, which will create a new domain
suntans.insertNcFile(windb2, ncFile, domainKey=args.domainKey, replaceData=args.replace, sqlWhere=args.where)

