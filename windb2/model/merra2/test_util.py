import unittest
import numpy
from windb2.model.merra2 import util


class TestUtil(unittest.TestCase):
    def testSurround(self):
        self.assertEqual(util.get_surrounding_merra2_nodes(62.5, 100), 10.42, 2)
        numpy.testing.assert_almost_equal(util.speed([2, 3, 4], [5, 6, 7]), numpy.array([5.385, 6.708, 8.062]), 3)