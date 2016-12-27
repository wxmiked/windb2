import unittest
import numpy
from windb2.model.merra2 import util
from windb2 import windb2


class TestUtil(unittest.TestCase):

    def setUp(self):
        self.db = windb2.WinDB2('localhost', 'windb2-test-4', dbUser='postgres')
        self.db.connect()

    def testSurround(self):
        self.assertEqual(util.get_surrounding_merra2_nodes(62.73, 38.21), ('62.5,63.125', '38.0,38.5'))
        self.assertEqual(util.get_surrounding_merra2_nodes(63.125, 38.0), ('63.125', '38.0'))

    def testDownload(self):
        util.download_all_merra2(self.db, 90.625, -45.5, 'u50m,v50m', dryrun=True)

    def testIndexConvert(self):
        self.assertEqual(util._convert_long_to_index(-179.375, -90), (0, 0))
        self.assertEqual(util._convert_long_to_index(180, 90), (575, 360))
        numpy.testing.assert_array_equal(util._convert_long_to_index([-100.625, -100], [32.5, 33.0]),
                                         [[126, 127], [245, 246]])