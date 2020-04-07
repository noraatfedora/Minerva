import sqlite3
import click
import json
from flask import current_app, g, Flask
from flask.cli import with_appcontext

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db

def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

def init_db():
    db = get_db()
    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))
    


@click.command('init-db')
@with_appcontext
def init_db_command():
    init_db()
    update_db()
    click.echo('Initialized the database.')

@click.command('update-db')
@with_appcontext
def update_db_command():
    update_db()
    click.echo('Updated the database.')
    
def update_db():
    db = get_db()
    # take the contents of items.json
    itemsRaw = open("src/items.json").read()
    values = json.loads(itemsRaw).values()
    print("Values: " + str(values))
    # Add these items as attiributes to a user
    for item in values:
        name = item['name']
        try:
            print("Name: " + name)
            db.execute("ALTER TABLE user ADD COLUMN " + name + " INTEGER " "DEFAULT 0")
        except:
            print(name + " already exists in the database...")
    db.commit()

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(update_db_command)

