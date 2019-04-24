import unittest
from windb2 import windb2

class TestHeightInterpMethods(unittest.TestCase):

    def setUp(self):
        self.db = windb2.WinDB2('localhost', 'windb2-test-1', dbUser='postgres')
        self.db.connect()

    def test_table_exists(self):
        self.assertFalse(self.db.table_exists('non_existent_table'))
        self.assertTrue(self.db.table_exists('domain'))

    if __name__ == '__main__':
        unittest.main()
