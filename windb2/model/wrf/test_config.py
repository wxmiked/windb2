import unittest
from windb2.model.wrf import config
import os

class TestConfigMethods(unittest.TestCase):

    temp_config = None

    def testExisting(self):
        # Just make sure this doesn't throw a schema exception
        config.Windb2WrfConfigParser(os.environ['WINDB2_HOME'] + '/config/windb2-wrf.json')

if __name__ == '__main__':
    unittest.main()
