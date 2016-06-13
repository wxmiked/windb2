import unittest
from windb2.model.wrf.heightinterp import calculate_height


class TestHeightInterpMethods(unittest.TestCase):

  def test_bottom(self):
      self.assertEqual(calculate_height(1), 0)

  def test_invalid(self):
      self.assertRaises(ValueError, calculate_height, -1)
      self.assertRaises(ValueError, calculate_height, 2)
      self.assertRaises(ValueError, calculate_height, 'a')
      self.assertRaises(ValueError, calculate_height, None)

  # Check against 1976 US Standard Atmosphere
  # Generated example eta levels using: http://www.digitaldutch.com/atmoscalc/index.htm
  def test_standard_atmosphere(self):
      self.assertAlmostEqual(calculate_height(0.540, topPressure=0),
                             5e3, delta=1e2)
      self.assertAlmostEqual(calculate_height(0.264, topPressure=0),
                             1e4, delta=1e3)
      self.assertAlmostEqual(calculate_height(0.989, topPressure=0),
                             100, delta=10)

if __name__ == '__main__':
    unittest.main()
