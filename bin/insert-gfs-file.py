#!/usr/bin/env python3
#
# Description: Inserts a GRIB1 file into WinDB2.
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
from windb2.model.gfs import insert, config
import logging
import cfgrib
from cfgrib import xarray_store
import xarray

# Get the command line opts
parser = argparse.ArgumentParser()
parser.add_argument("db_host", type=str, help="Database hostname")
parser.add_argument("db_user", type=str, help="Database username")
parser.add_argument("db_name", type=str, help="Database name")
parser.add_argument("gribfile", type=str, help="GRIB file prefix (do NOT use the '*' wildcard)")
parser.add_argument("-o", "--overwrite", help="Replace data if the data for the time exists in the WinDB2",
                    action="store_true")
parser.add_argument("-m", "--mask", help="Name of a 2D PostGIS polygon table in the WinDB2 to be use for a mask.")
parser.add_argument('-p', '--port', type=int, default='5432', help='Port for WinDB2 connection')
parser.add_argument('-z', '--zero_seconds', action='store_true',
                    help='Always set WRF time seconds to zero (stops WRF time creep)')
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("-d", "--domain_key", type=str, help="Existing domain key in the WinDB2")
group.add_argument("-n", "--new", action="store_false", help="Create a new WinDB2 domain")
args = parser.parse_args()

# TODO make sure that -m and -n are only used together (i.e. -m should not be used with -d)

# Connect to the WinDB
windb2 = windb2.WinDB2(args.db_host, args.db_name, dbUser=args.db_user, port=args.port)
windb2.connect()

# Load a WinDB2 config file
windb2_config = config.WinDB2GFSConfigParser('windb2-gfs.json')

# Set up logging
LOGLEVEL = os.environ.get('LOGLEVEL', 'ERROR').upper()
logger = logging.getLogger(__name__)
try:
    logger.setLevel(LOGLEVEL)
except KeyError:
    print('invalid log level: {}, setting to INFO by default'.format(LOGLEVEL), file=sys.stderr)
    logger.setLevel(logging.INFO)
logging.basicConfig()

# Create the inserter from this config
inserter = insert.InsertGFS(windb2, windb2_config)

# Insert the file, domainKey should be None if it wasn't set, which will create a new domain
for var in windb2_config.config['vars']:
    var_config = windb2_config.config['vars'][var]
    if isinstance(var_config['insert'], list):  # will fail if insert does not exist

        # Debug
        logger.debug(cfgrib.open_datasets(args.gribfile))

        # Calculate the level required
        backend_kwargs = {'filter_by_keys': {'typeOfLevel': var_config['cfgribTypeOfLevel']}}
        backend_kwargs['filter_by_keys']['level'] = var_config['insert'][0]
        try:
          # stepType is optional and is needed for PRATE
          backend_kwargs['filter_by_keys']['stepType'] = var_config['cfGribStepType'][0]
        except KeyError:
          pass

        # Open the GRIB2 file using cfgrib
        logger.debug('Trying to open variable: {}'.format(var))
        with xarray.open_dataset(args.gribfile, engine='cfgrib', backend_kwargs=backend_kwargs) as gribfile:
            (times_inserted, domain_key_returned) = inserter.insert_variable(gribfile, var, windb2_config.config['vars'][var]['cfVarName'],
                                                                             domain_key=args.domain_key,
                                                                             replace_data=args.overwrite,
                                                                             mask=args.mask)

    # Set the domain key so that we don't create the same domain twice
    if not args.domain_key:
        args.domain_key = domain_key_returned
