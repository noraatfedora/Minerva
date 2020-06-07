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

    def test_register_client(self):
        response = self.app.post(
            '/register',
            data=dict(email='johndoe@mailinator.com',
                password='asdf',
                confirm='asdf',
                address='1234 address st',
                zipCode='98034',
                instructions='',
                cellPhone='1234567890',
                homePhone=''),
            follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)

    def tearDown(self):
        pass

if __name__ == "__main__":
    unittest.main()

