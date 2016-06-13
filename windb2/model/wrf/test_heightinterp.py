import unittest
from windb2.model.wrf import heightinterp
from windb2 import util
import numpy


class TestHeightInterpMethods(unittest.TestCase):
    def testBottom(self):
        self.assertEqual(heightinterp.calculate_height(numpy.array([1.0])), 0)

    def testInvalid(self):
        self.assertRaises(ValueError, heightinterp.calculate_height, numpy.array([-1.0]))
        self.assertRaises(ValueError, heightinterp.calculate_height, numpy.array([2.0]))
        self.assertRaises(ValueError, heightinterp.calculate_height, 'a')
        self.assertRaises(TypeError, heightinterp.calculate_height, numpy.array([[0.4], [0.4]]))
        self.assertRaises(ValueError, heightinterp.calculate_height, None)

    # Check against 1976 US Standard Atmosphere
    # Generated example eta levels using: http://www.digitaldutch.com/atmoscalc/index.htm
    def testStandardAtmosphere(self):
        self.assertAlmostEqual(heightinterp.calculate_height(numpy.array([0.264]), topPressure=0),
                               1e4, delta=1e3)
        self.assertAlmostEqual(heightinterp.calculate_height(numpy.array([0.540]), topPressure=0),
                               5e3, delta=1e2)
        self.assertAlmostEqual(heightinterp.calculate_height(numpy.array([0.989]), topPressure=0),
                               100, delta=10)

    def testLogLawInterp(self):
        # Match log wind speed profile from this site: http://wind-data.ch/tools/profile.php?lng=en
        speed = numpy.array([5.00, 6.19, 7.11, 7.60])
        z = numpy.array([10, 30, 70, 110])
        z_interp = numpy.array([20, 40, 60, 90])
        z_max = 150
        numpy.testing.assert_almost_equal(heightinterp.log_law_interp(speed, z, z_interp, z_max=z_max),
                                          numpy.array([5.75, 6.51, 6.95, 7.39]), decimal=2)

    def testLogLawBadInputs(self):
        # Bogus (negative value) wind speed
        self.assertRaises(ValueError, heightinterp.log_law_interp, numpy.array([-1]), numpy.array([10]),
                          numpy.array([5]))

        # Bogus (negative value) for the z_interp height
        self.assertRaises(ValueError, heightinterp.log_law_interp, numpy.array([5]), numpy.array([-1]),
                          numpy.array([5]))

        # Should return ValueError for heights about 130 m unless z_max is explicitly defined
        self.assertRaises(ValueError, heightinterp.log_law_interp, numpy.array([5]), numpy.array([5]),
                          numpy.array([150]))

    def testUVInterp(self):
        # Match log wind speed profile from this site: http://wind-data.ch/tools/profile.php?lng=en
        numpy.testing.assert_almost_equal(heightinterp.uv_column_interp(numpy.array([util.u_flow(5.75, 45),
                                                                              util.u_flow(6.19, 45),
                                                                              util.u_flow(6.51, 45),
                                                                              util.u_flow(6.75, 45),
                                                                              util.u_flow(6.95, 45),
                                                                              util.u_flow(7.11, 45),
                                                                              util.u_flow(7.39, 45)]),
                                                                 numpy.array([util.v_flow(5.75, 45),
                                                                              util.v_flow(6.19, 45),
                                                                              util.v_flow(6.51, 45),
                                                                              util.v_flow(6.75, 45),
                                                                              util.v_flow(6.95, 45),
                                                                              util.v_flow(7.11, 45),
                                                                              util.v_flow(7.39, 45)]),
                                                                 numpy.array([20, 30,
                                                                              40, 50, 60,
                                                                              70, 90]), numpy.array([0.0001, 10])),
                                          [[0, util.u_flow(5, 45)], [0, util.v_flow(5, 45)]],
                                          decimal=2)

if __name__ == '__main__':
    unittest.main()
