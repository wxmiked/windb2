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
import sys
import re
dir = os.path.dirname(__file__)
sys.path.append(os.path.join(dir, '../'))

import argparse
from windb2.model.wrf import heightinterpfile
from windb2.model.wrf import config
import logging

# Set up logging for InsertAbstract
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logging.basicConfig()

# Get the command line opts
parser = argparse.ArgumentParser()
parser.add_argument("ncfile", type=str, help="WRF netCDF filename to interpolate")
args = parser.parse_args()
wrf_config = config.Windb2WrfConfigParser()
wrf_config.read('windb2-wrf.conf')

# Get rid of escaped colon characters that are often added in Unix shells
ncfile_cleansed = re.sub(r'[\\]', '', args.ncfile)

# Interpolate this file
try:
    heightinterpfile.HeightInterpFile(wrf_config).interp_file(ncfile_cleansed)
except configparser.NoSectionError:
    msg = 'Missing windb2-wrf.conf file. Please add a valid config file.'
    print(msg)
    logger.error(msg)
    sys.exit(-1)
