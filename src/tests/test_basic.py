import os
import unittest
from sys import path
path.append(path[0] + "/../")
from tests import set_test_environment_variables
import application

class BasicTests(unittest.TestCase):
    def setUp(self):
        self.app = application.app.test_client()
    def test_main_page(self):
        response = self.app.get('/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def tearDown(self):
        pass

if __name__ == "__main__":
    unittest.main()

