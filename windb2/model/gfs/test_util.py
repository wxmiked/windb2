import unittest
import numpy
from windb2.model.gfs import util

class TestUtil(unittest.TestCase):
    def test_coord_shift(self):
        self.assertEqual(util.center_coords_on_prime_meridian(numpy.array([181])), -179)
        self.assertEqual(util.center_coords_on_prime_meridian(numpy.array([360])), 0)
