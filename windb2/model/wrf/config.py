#
# Mike Dvorak
# Sail Tactics
# mike@sailtactics.com
#
# Created: 2014-12-31 (as wxtactics-api/generate-tide-tiles/config.py)
# Modified: 2018-08-21
#
"""
Reads in a WRF specific configuration for WinDB2 and utilities.

Configuration files have to be named have to be JSON files that conform to the schema config/windb2-wrf.schema .

Configuration file has to be in the current working directory.
"""
import logging
from jsonschema import validate
import json
import os

class Windb2WrfConfigParser():

    def __init__(self, config_file):
        super().__init__()

        # Logger
        logger = logging.getLogger('windb2')

        # Read the JSON config
        with open(config_file) as fc:
            self.config = json.load(fc)

        # Read the JSON schema
        with open(os.environ['WINDB2_HOME'] + '/config/windb2-wrf.schema') as fs:
            self.schema = json.load(fs)

        # Validate
        try:
            validate(self.config, self.schema)
        except Exception as e:
            logger.error('Invalid WinDB2 config file')
            logger.error(e)