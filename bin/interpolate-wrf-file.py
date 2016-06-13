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
import fnmatch
import os
import sys
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
parser.add_argument("ncfile", type=str, help="WRF netCDF file prefix (do NOT use the '*' wildcard)")
args = parser.parse_args()
wrf_config = config.Windb2WrfConfigParser()
wrf_config.read('windb2-wrf.conf')

# Insert all of the files that match the wildcard pattern
for f in sorted(os.listdir('.')):

    if fnmatch.fnmatch(f, args.ncfile + '*[0-9]') and not os.path.exists(f + heightinterpfile.HeightInterpFile.outfile_extension):

        heightinterpfile.HeightInterpFile(wrf_config).interp_file(f)
