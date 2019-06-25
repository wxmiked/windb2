"""
Reads in a WRF specific configuration for WinDB2 and utilities.

Configuration files have to be named have to be JSON files that conform to the schema config/windb2-gfs.schema .

Configuration file has to be in the current working directory.
"""
import logging
from jsonschema import validate
import json
import os

class WinDB2GFSConfigParser():

    def __init__(self, config_file):
        super().__init__()

        # Logger
        LOGLEVEL = os.environ.get('LOGLEVEL', 'ERROR').upper()
        logger = logging.getLogger('windb2')
        logger.setLevel(LOGLEVEL)

        # Read the JSON config
        with open(config_file) as fc:
            self.config = json.load(fc)

        # Read the JSON schema
        with open(os.environ['WINDB2_HOME'] + '/config/windb2-gfs.schema') as fs:
            self.schema = json.load(fs)

        # Validate
        try:
            validate(self.config, self.schema)
        except Exception as e:
            logger.error('Invalid WinDB2 config file')
            logger.error(e)
