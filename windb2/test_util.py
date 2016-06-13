import unittest
import numpy
import util


class TestUtil(unittest.TestCase):
    def testSpeed(self):
        self.assertAlmostEqual(util.speed(8.3, 6.3), 10.42, 2)
        numpy.testing.assert_almost_equal(util.speed([2, 3, 4], [5, 6, 7]), numpy.array([5.385, 6.708, 8.062]), 3)

    def testDirection(self):

        # Single scalars
        self.assertAlmostEqual(util.u_flow(4.24, 45), 3, 2)
        self.assertAlmostEqual(util.u_met(4.24, 45), -3, 2)
        self.assertAlmostEqual(util.v_flow(4.24, 45), 3, 2)
        self.assertAlmostEqual(util.v_met(4.24, 45), -3, 2)


        # Numpy arrays
        numpy.testing.assert_almost_equal(util.speed([2, 3, 4], [5, 6, 7]), numpy.array([5.385, 6.708, 8.062]), 3)
        numpy.testing.assert_almost_equal(util.u_flow([3, 3, 2], [0, 90, 60]), [0, 3, numpy.sqrt(3)], decimal=2)
        numpy.testing.assert_almost_equal(util.u_met([3, 3, 2], [0, 90, 60]), [0, -3, -numpy.sqrt(3)], decimal=2)
        numpy.testing.assert_almost_equal(util.v_flow([3, 3, 2], [0, 90, 60]), [3, 0, 1], decimal=2)
        numpy.testing.assert_almost_equal(util.v_met([3, 3, 2], [0, 90, 60]), [-3, 0, -1], decimal=2)

        # Test broadcasting one direction to multiple speeds
        numpy.testing.assert_almost_equal(util.u_flow([2, 2, 2], [60]), [numpy.sqrt(3), numpy.sqrt(3), numpy.sqrt(3)],
                                          decimal=2)
        numpy.testing.assert_almost_equal(util.v_flow([2, 2, 2], [60]), [1, 1, 1], decimal=2)

    def testCalcDirDegrees(self):

        # First quadrant
        self.assertEqual(util.calc_dir_deg(3, 3), 45)

        # Second quadrant
        self.assertEqual(util.calc_dir_deg(3, -3), 135)

        # Third quadrant
        self.assertEqual(util.calc_dir_deg(-3, -3), 225)

        # Fourth quadrant
        self.assertEqual(util.calc_dir_deg(-3, 3), 315)
