__author__ = 'dvorak'

import unittest
import numpy


class TestHorizontalInterpMethods(unittest.TestCase):
    def setUp(self):
        self.test_input_x_array = [[0, 1, 2], [0, 1, 2]]
        self.test_input_y_array = [[0, 1, 2], [0, 1, 2]]
        self.test_input_array = numpy.array([[0, 1, 0], [1, 0, 1]], numpy.float)

        self.test_output_x_array = [[0.5, 1.5], [0.5, 1.5]]
        self.test_output_y_array = [[0.5, 1.5], [0.5, 1.5]]
        self.test_output_array = numpy.array([0.5, 0.5], [0.5, 0.5], numpy.float)

    def test_interp(self):
        self.assertEqual(interph(self.test_input_array), self.test_output_array)

    if __name__ == '__main__':
        unittest.main()
