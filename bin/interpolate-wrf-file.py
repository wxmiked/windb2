#!/usr/bin/env python3
#
#
# Mike Dvorak
# Sail Tactics
# mike@sailtactics.com
#
# Created: 2014-11-05
# Modified: 2016-06-13
#
#
# Description: Inserts a arbitrary WRF netCDF file into a WindDB at the specified height.
#
# Returns -1 if there is an IntegrityError, which is triggered by a duplicate key error if the data already exists. 
#
import configparser
import fnmatch
import os
import os.path
import sys
import re
dir = os.path.dirname(__file__)
sys.path.append(os.path.join(dir, '../'))

import argparse
from windb2.model.wrf import heightinterpfile
from windb2.model.wrf.copyvar import copyvar
from windb2.model.wrf import config
import logging

# Get the command line opts
parser = argparse.ArgumentParser()
parser.add_argument("ncfile", type=str, help="WRF netCDF filename to interpolate")
parser.add_argument("-c", "--copy", help="Copy WRF variables to the interp file",
                    action="store_true")
parser.add_argument("-o", "--overwrite", help="Overwrite an existing interp file",
                    action="store_true")
args = parser.parse_args()
windb2_config = config.Windb2WrfConfigParser('windb2-wrf.json').config

# Set up logging
logger = logging.getLogger('windb2')
try:
    logger.setLevel(windb2_config['loglevel'])
except KeyError:
    logger.setLevel(logging.INFO)
logging.basicConfig()

# Extension
interp_extension = '-height-interp.nc'

# Get rid of escaped colon characters that are often added in Unix shells
ncfile_cleansed = re.sub(r'[\\]', '', args.ncfile)

# Check to see if the file already exists and abort if 'overwrite' is not enabled
if not args.overwrite and os.path.exists(ncfile_cleansed + interp_extension):
    logger.error('Interp file already exists and the overwrite option is not enabled: {}'.format(ncfile_cleansed + interp_extension))
    sys.exit(-3)
elif args.overwrite and os.path.exists(ncfile_cleansed + interp_extension):
    logger.info('Overwriting existing interp file: {}'.format(ncfile_cleansed + interp_extension))

# Interpolate this file and leave the file open if we're copying WRF vars
close_file = True if args.copy else False
heightinterpfile.HeightInterpFile(windb2_config).interp_file(ncfile_cleansed, close_file=close_file)

# Copy of WRF vars
if args.copy:
    # Get the WRF vars to copy
    wrf_vars = []
    for key, val in windb2_config['vars'].items():
        try:
            val['copy'] # Generates an exception if not there
            wrf_vars.append(key)
        except KeyError as e:
            True

    # Exit if nothing to do
    if len(wrf_vars) == 0:
        exit(0)

    # Copy the vars
    copyvar(wrf_vars, ncfile_cleansed, ncfile_cleansed + interp_extension)
