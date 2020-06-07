from os import environ
import set_environment_variables
from subprocess import call
environ['FLASK_APP'] = 'application.py'
environ['FLASK_ENV'] = 'development'
environ['FLASK_DEBUG'] = '1'
call(['flask', 'run'])
