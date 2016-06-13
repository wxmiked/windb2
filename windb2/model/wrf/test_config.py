import unittest
from windb2.model.wrf import heightinterpfile
from windb2.model.wrf import config
import tempfile
import os

class TestConfigMethods(unittest.TestCase):

    temp_config = None

    def createTempTestDir(self):
        # Create temporary directory and change to it
        self.tempdir_parent = tempfile.TemporaryDirectory()
        os.chdir(self.tempdir_parent.name)

        # Write a new config file in the temp dir
        config.Windb2WrfConfigParser.writeNewConfigFile('windb2-wrf.conf')

    def testExisting(self):
        print('CWD=', os.getcwd())
        testing_config = config.Windb2WrfConfigParser()
        testing_config.read('test/windb2-wrf.conf')
        self.assertEqual([str(item) for item in testing_config.get_float_list('INTERP', 'heights')],
                         ['5.0', '10.0', '20.0', '60.0', '150.0'])
        self.assertEqual([str(item) for item in testing_config.get_float_list('WINDB2', 'heights')],
                         ['10.0', '60.0'])

    def testHeightArrays(self):
        self.createTempTestDir()
        temp_config = config.Windb2WrfConfigParser()
        temp_config.read('windb2-wrf.conf')
        self.assertEqual([str(item) for item in temp_config.get_float_list('INTERP', 'heights')],
                         config.Windb2WrfConfigParser.interp_heights.split(','))
        self.assertEqual([str(item) for item in temp_config.get_float_list('WINDB2', 'heights')],
                         config.Windb2WrfConfigParser.windb2_heights.split(','))

    def testInterpVarArray(self):
        self.createTempTestDir()
        temp_config = config.Windb2WrfConfigParser()
        temp_config.read('windb2-wrf.conf')
        self.assertEqual([str(item) for item in temp_config.get_str_list('INTERP', 'vars')],
                         config.Windb2WrfConfigParser.interp_vars.split(','))

    def testContainsInterpVar(self):
        temp_config = config.Windb2WrfConfigParser()
        temp_config.read('test/windb2-wrf.conf')
        self.assertTrue(temp_config.contains_interp_var('UV'))
        self.assertFalse(temp_config.contains_interp_var('cannot find'))

if __name__ == '__main__':
    unittest.main()
