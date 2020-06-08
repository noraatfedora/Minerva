import os
import unittest
from sys import path
path.append(path[0] + "/../")
from tests import set_test_environment_variables
import application
import request_items
from json import loads
from werkzeug.security import generate_password_hash
from os import environ
from db import users, conn, orders

class BasicTests(unittest.TestCase):
    def setUp(self):
        self.app = application.app.test_client()
        if len(conn.execute(users.select(users.c.role=="ADMIN")).fetchall()) == 0:
            # Manually create a new food bank
            # If you create a user, it requires
            # a food bank id, so the first user
            # must be a manually created food bank.
            food_bank_pass=generate_password_hash("password")
            conn.execute(users.insert(),
                id=1,
                email="foodbankexample@mailinator.com",
                name="Example food bank",
                address="1323 S Yakima Ave, Tacoma, WA 98405",
                role="ADMIN",
                zipCode=98405
            )

    def test_main_page(self):
        response = self.app.get('/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def check_response_code(self, page, data):
        response = self.app.post(
            page, data=data, follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)

    def test_register_client(self):
        self.check_response_code(
            page='/register',
            data=dict(
                email='johndoe@mailinator.com',
                password='password',
                confirm='password',
                address='1234 address st',
                zipCode='98034',
                instructions='',
                cell='1234567890',
                homePhone='')
        )

    def test_register_volunteer(self):
        self.check_response_code(
            page='/volunteerregister',
            data=dict(
                email='volunteerexample@mailinator.com',
                password='password',
                name="Test Volunteer",
                confirm='password',
                address='volunteer address wheeee',
                zipCode='98034',
                cell = '0987654321',
                homePhone = '',
                Sunday='Sunday',
                Monday='',
                Tuesday='Tuesday',
                Wednesday='',
                Thursday='',
                Friday='',
                Saturday=''
            )
        )

    def test_login(self):
        self.test_register_client()
        self.check_response_code(
            page='/login',
            data=dict(
                email='johndoe@mailinator.com',
                password='password')
        )

    def test_request(self):
        with application.app.app_context():
            self.check_response_code(
                page='/login',
                data=dict(
                    email='johndoe@mailinator.com',
                    password='asdf')
            )
            availableDates = request_items.availableDates()
            with open(environ['INSTANCE_PATH'] + "items.json", "r") as f:
                itemsList = loads(f.read())
            firstItem = next(iter(itemsList.keys()))
            data = {
               'date': next(iter(availableDates))
            }
            for item in itemsList.keys():
                data[item + "-quantity"] = 0
            data[firstItem + "-quantity"] = 2
            self.check_response_code(
                page='/request_items',
                data=data
            )

    def tearDown(self):
        pass

if __name__ == "__main__":
    unittest.main()

