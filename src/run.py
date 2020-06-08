from os import environ
import set_environment_variables
from subprocess import call
from sys import path

environ['FLASK_APP'] = 'application.py'
environ['FLASK_ENV'] = 'development'
environ['FLASK_DEBUG'] = '1'
environ['INSTANCE_PATH'] = '/' + path[0] + '/../instance/'
call(['flask', 'run'])
