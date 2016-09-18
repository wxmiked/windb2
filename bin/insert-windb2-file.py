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
import re
import configparser

dir = os.path.dirname(__file__)
sys.path.append(os.path.join(dir, '../'))

from netCDF4 import Dataset
import argparse
from windb2 import windb2
from windb2.model.wrf import insert, heightinterpfile, config
import logging

# Set up logging level
logger = logging.getLogger('windb2')
logger.setLevel(logging.WARNING)
logging.basicConfig()

# Get the command line opts
parser = argparse.ArgumentParser()
parser.add_argument("db_host", type=str, help="Database hostname")
parser.add_argument("db_user", type=str, help="Database username")
parser.add_argument("db_name", type=str, help="Database name")
parser.add_argument("ncfile", type=str, help="WRF netCDF file prefix (do NOT use the '*' wildcard)")
parser.add_argument("-o", "--overwrite", help="Replace data if the data for the time exists in the WinDB2",
                    action="store_true")
parser.add_argument("-m", "--mask", help="Name of a 2D PostGIS polygon table in the WinDB2 to be use for a mask.")
parser.add_argument('-p', '--port', type=int, default='5432', help='Port for WinDB2 connection')
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("-d", "--domain_key", type=str, help="Existing domain key in the WinDB")
group.add_argument("-n", "--new", action="store_false")
args = parser.parse_args()

# Connect to the WinDB
windb2 = windb2.WinDB2(args.db_host, args.db_name, dbUser=args.db_user, port=args.port)
windb2.connect()

# Load a WinDB2 config file
windb2_config = config.Windb2WrfConfigParser()
windb2_config.read('windb2-wrf.conf')

# Create the inserter from this config
inserter = insert.InsertWRF(windb2, windb2_config)

# Get rid of escaped colon characters that are often added in Unix shells
ncfile_cleansed = re.sub(r'[\\]', '', args.ncfile)

# Open the WRF netCDF file
ncfile = Dataset(ncfile_cleansed, 'r')

# Insert the file, domainKey should be None if it wasn't set, which will create a new domain
try:
    inserter.insert_variable(ncfile, 'WIND', 'wind', domain_key=args.domain_key, replace_data=args.overwrite,
                             mask=args.mask)
except configparser.NoSectionError:
    msg = 'Missing windb2-wrf.conf file. Please add a valid config file.'
    print(msg)
    logger.error(msg)
    sys.exit(-1)
