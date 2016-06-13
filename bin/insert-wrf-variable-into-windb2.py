#!/usr/bin/env python3
#
#
# Mike Dvorak
# Sail Tactics
# mike@sailtactics.com
#
# Created: 2014-11-05
# Modified: 2015-04-17
#
#
# Description: Inserts a arbitrary WRF netCDF file into a WindDB at the specified height.
#
# Returns -1 if there is an IntegrityError, which is triggered by a duplicate key error if the data already exists. 
#

import os
import sys
dir = os.path.dirname(__file__)
sys.path.append(os.path.join(dir, '../'))

from netCDF4 import Dataset
import argparse
from windb2 import windb2
from windb2.model.wrf import insert
import logging

# Set up logging for InsertAbstract
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logging.basicConfig()

# Get the command line opts
parser = argparse.ArgumentParser()
parser.add_argument("db_host", type=str, help="Database hostname")
parser.add_argument("db_user", type=str, help="Database username")
parser.add_argument("db_name", type=str, help="Database name")
parser.add_argument("nc_file", type=str, help="WRF netCDF file")
parser.add_argument("-o","--overwrite", help="Replace data if the data for the time exists in the WinDB2", action="store_true")
parser.add_argument("-m", "--mask", help="Name of a 2D PostGIS polygon table in the WinDB2 to be use for a mask.")
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("-d", "--domain_key", type=str, help="Existing domain key in the WinDB")
group.add_argument("-n", "--new", action="store_true")
args = parser.parse_args()

# Connect to the WinDB
windb2 = windb2.WinDB2(args.db_host, args.db_name, dbUser=args.db_user)
windb2.connect()

# Create the inserter from this config
inserter = insert.InsertWRF(windb2)

# Open the tide netCDF file
nc_file = Dataset(args.nc_file, 'r', format="NETCDF3_CLASSIC")

# Insert the file, domainKey should be None if it wasn't set, which will create a new domain
# TODO the variable to insert should be read from the windb2.conf file
timesInserted, u10_domain_key = inserter.insert_variable(nc_file, 'U10', 'u10', domain_key=args.domain_key,
                                                                replace_data=args.overwrite, file_type='wrf', mask=args.mask)
timesInserted, v10_domain_key = inserter.insert_wrf_nc_variable(nc_file, 'V10', 'v10', domain_key=u10_domain_key,
                                                                replace_data=args.overwrite, file_type='wrf', mask=args.mask)
