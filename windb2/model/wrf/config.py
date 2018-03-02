#
# Mike Dvorak
# Sail Tactics
# mike@sailtactics.com
#
# Created: 2014-12-31 (as wxtactics-api/generate-tide-tiles/config.py)
# Modified: 2015-08-31
#
"""
Reads in a WRF specific configuration for WinDB2 and utilities.

Configuration files have to be names "windb2.conf" or ".windb2.conf".

Configuration files has to be in the current working directory.
"""
import configparser
import logging

class Windb2WrfConfigParser(configparser.SafeConfigParser):

    """Default heights, specified here for unit testing purposes"""
    interp_heights = '5.0,10.0,50.0,90.0'
    windb2_heights = '10.0'
    interp_vars = 'U'
    wrf_vars = 'PSFC,'

    def __init__(self):
        super().__init__()

    @staticmethod
    def writeNewConfigFile(config_filename):
        config_parser = configparser.ConfigParser()

        # Interpolation section
        config_parser.add_section('INTERP')
        config_parser.set('INTERP', 'heights', Windb2WrfConfigParser.interp_heights)
        config_parser.set('INTERP', 'vars', Windb2WrfConfigParser.interp_vars)

        # WinDB2 section
        config_parser.add_section('WINDB2')
        config_parser.set('WINDB2', 'heights', Windb2WrfConfigParser.windb2_heights)
        config_parser.set('WINDB2', 'dbhost', 'UNSET')
        config_parser.set('WINDB2', 'dbname', 'UNSET')
        config_parser.set('WINDB2', 'dbuser', 'UNSET')

        # Interpolation section
        config_parser.add_section('WRF')
        config_parser.set('WRF', 'vars', Windb2WrfConfigParser.interp_vars)

        # Logging section
        config_parser.add_section('LOGGING')
        config_parser.set('LOGGING', 'interp', 'INFO')
        config_parser.set('LOGGING', 'windb2', 'INFO')

        # Write the new config file
        with open(config_filename, 'w') as config_new:
            config_parser.write(config_new)


    def get_float_list(self, section, var):
        """Returns a list of floats that are separated by a comma"""
        list_str = self.get(section, var).split(',')
        try:
            return [float(item) for item in list_str]
        except ValueError:
            return [float(item) for item in list_str[:-1]]  # A number and a comma returns a ['10',''] so ignore the last element


    def get_str_list(self, section, var):
        """Returns a list of strings that are separated by a comma"""
        list_str = self.get(section, var).split(',')
        return [str(item) for item in list_str]

    def contains_interp_var(self, var):
        """Returns true if the variable (case insensitive) was in the config file."""
        if var in self.get_str_list('INTERP', 'vars'):
            return True
        else:
            return False