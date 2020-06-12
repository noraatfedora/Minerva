import click
import json
from flask import current_app, g, Flask
from sqlalchemy import create_engine, Table, Column, Date, Integer, String, MetaData, Boolean
from sqlalchemy.orm import session, sessionmaker
from flask.cli import with_appcontext
import sys
import os

Session = sessionmaker(autocommit=True)

if os.environ.get('RDS_CONNECT') is not None:
    url = os.environ.get('RDS_CONNECT')
    engine = create_engine(url, pool_recycle=28700)
    Session.configure(bind=engine)
    sess = Session()
    print("DB URL: " + url)
else:
    url = 'sqlite://' + os.environ['INSTANCE_PATH'] + '/requests.sqlite?check_same_thread=False'
    print('URL: ' + url)
    engine = create_engine(url)
    Session.configure(bind=engine)
    sess = Session()


meta = MetaData()
users = Table(
    'users', meta,
    Column('id', Integer, primary_key=True),
    Column('name', String(60)),
    Column('email', String(60)),
    Column('password', String(255)),
    # Either RECIEVER, VOLUNTEER, or ADMIN
    # yes I know reciever is spelled wrong but it's too late to change that
    Column('role', String(10)),
    Column('cellPhone', String(15)),
    Column('instructions', String(255)),
    Column('homePhone', String(15)),
    Column('address', String(40)),
    Column('zipCode', Integer),
    # for volunteers
    Column('approved', Boolean),
    Column('sunday', Boolean),
    Column('monday', Boolean),
    Column('tuesday', Boolean),
    Column('wednesday', Boolean),
    Column('thursday', Boolean),
    Column('friday', Boolean),
    Column('saturday', Boolean),
    Column('assignedZipCodes', String(255)),

    # Store for food banks, not volunteers
    Column('maxOrders', Integer),

    Column('items', String()),
    # for both users and volunteers
    # this will be determined automatically
    # when the user registers, but the food bank
    # can change which volunteers they control
    Column('foodBankId', Integer) # id of the user of their food bank
)

orders = Table(
    'orders', meta,
    Column('id', Integer, primary_key=True),
    Column('userId', Integer),
    # This is probably redundant, but just in case
    # we need to track who delivered an order after it's 
    # removed from a volunteer's list
    Column('volunteerId', Integer),
    Column('foodBankId', Integer),
    Column('contents', String(255)), # json
    Column('bagged', Integer),
    Column('date', Date),
    Column('completed', Integer)  # either 0 or 1
)

print("Date type: " + str(Date.python_type))
conn = engine.connect()
print("Initializing db!")
try:
    meta.create_all(engine)
except:
    print("Database exists!")

def get_db():
    return conn


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()


def init_app(app):
    app.teardown_appcontext(close_db)

