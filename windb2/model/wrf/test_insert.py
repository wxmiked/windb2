import unittest
import numpy.testing
from windb2.model.wrf.insert import InsertWRF


class TestHeightInterpMethods(unittest.TestCase):

  def test_lcc_coords(self):

      x_arr, y_arr = InsertWRF.create_coord_arrays(4, 4, 5000, 5000)
      numpy.testing.assert_almost_equal(x_arr, numpy.array([-10000, -5000, 0, 5000]))

if __name__ == '__main__':
    unittest.main()
