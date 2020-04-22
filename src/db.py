import click
import json
from flask import current_app, g, Flask
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData
from flask.cli import with_appcontext
import os

if ('RDS_HOSTNAME' in os.environ):
    user = os.environ['RDS_USERNAME']
    password = os.environ['RDS_PASSWORD']
    host = os.environ['RDS_HOSTNAME']
    port = os.environ['RDS_PORT']

    url = 'mysql+mysqldb://' + user + ':' + password + '@' + host + ':' + port + "/ebdb"
    engine = create_engine(url)
    print("DB URL: " + url)
else:
    engine = create_engine(
        'sqlite:///instance/requests.sqlite?check_same_thread=False')


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
    # Stored as a JSON because g.db doesn't support adding Columns
    Column('order', String(255)),
    Column('completed', Integer)  # either 0 or 1
)
conn = engine.connect()
# TODO: Remove this


def get_db():
    return conn


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()


def init_app(app):
    app.teardown_appcontext(close_db)

    meta.create_all(engine)
