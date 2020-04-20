import click
import json
from flask import current_app, g, Flask
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData
from flask.cli import with_appcontext

engine = create_engine('sqlite:///instance/requests.sqlite?check_same_thread=False')
meta = MetaData()
users = Table(
    'users', meta,
    Column('id', Integer, primary_key = True),
    Column('email', String),
    Column('password', String),
    Column('role', String),
    Column('cellPhone', String),
    Column('instructions', String),
    Column('homePhone', String),
    Column('address', String),
    Column('items', String), # Stored as a JSON because g.db doesn't support adding Columns
    Column('completed', Integer) # either 0 or 1
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
