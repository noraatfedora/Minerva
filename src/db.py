import click
import json
from flask import current_app, g, Flask
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData
from sqlalchemy.orm import session, sessionmaker
from flask.cli import with_appcontext
import os

Session = sessionmaker(autocommit=True)

if os.environ.get('RDS_CONNECT') is not None:
    url = os.environ.get('RDS_CONNECT')
    engine = create_engine(url)
    Session.configure(bind=engine)
    sess = Session()
    print("DB URL: " + url)
else:
    engine = create_engine(
        'sqlite:///instance/requests.sqlite?check_same_thread=False')
    Session.configure(bind=engine)
    sess = Session()


meta = MetaData()
users = Table(
    'users', meta,
    Column('id', Integer, primary_key=True),
    Column('email', String(60)),
    Column('password', String(255)),
    Column('role', String(10)),
    Column('cellPhone', String(15)),
    Column('instructions', String(255)),
    Column('homePhone', String(15)),
    Column('address', String(40)),
    Column('zipCode', Integer),
    # for volunteers
    Column('assignedZipCodes', String(255)),
    # Stored as a JSON because g.db doesn't support adding Columns
    Column('order', String(255)),
    Column('completed', Integer)  # either 0 or 1
)
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

