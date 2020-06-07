from os import environ
# Use all the normal environment variables
exec(open('set_environment_variables.py').read())
# And then change the sqlite path to point to the testing database.
environ['INSTANCE_PATH'] = '/instance/'