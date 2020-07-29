from os import environ, remove
from sys import path
# Use all the normal environment variables
path.append(path[0] + '/../')

# And then change the sqlite path to point to the testing database.
environ['INSTANCE_PATH'] = '//home/jared/Minerva/src/tests/instance/'
try:
    remove(environ['INSTANCE_PATH'] + "/requests.sqlite")
except:
    pass