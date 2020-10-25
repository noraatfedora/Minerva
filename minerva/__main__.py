from dotenv import load_dotenv
load_dotenv()

from os import environ
from subprocess import call
from sys import path

environ['FLASK_APP'] = 'minerva/backend/apis/application.py'
environ['FLASK_ENV'] = 'development'
environ['FLASK_DEBUG'] = '1'

print("Path:" + str(path))
call(['flask', 'run'])
