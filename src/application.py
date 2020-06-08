import os
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, Flask
)
from db import  conn, users

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY = 'dev',
        #SQLALCHEMY_DATABASE_URI = 'sqlite://instance/requests.sqlite'
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # a simple page that says hello
    @app.route('/')
    @app.route('/home')
    def home():
        return render_template('home.html', title = 'Home')
    
    @app.route('/volunteer')
    def volunteer():
        return render_template('volunteer.html', title = 'Volunteer')

    @app.route('/success')
    def success():
        return render_template('success.html', title = 'Request Submitted')

    @app.route('/ping')
    # This page is called with a cron job so that the database doesn't jam up every 8 hours.
    def ping():
        try:
            conn.execute(users.select())
            return "Success!"
        except:
            return "Fail!"


    import db
    db.init_app(app)
    
    import auth
    app.register_blueprint(auth.bp)

    import dashboard
    app.register_blueprint(dashboard.bp)

    import request_items
    app.register_blueprint(request_items.bp)
    app.add_url_rule('/', endpoint='index')

    import modify_volunteers
    app.register_blueprint(modify_volunteers.bp)

    import view_all_orders
    app.register_blueprint(view_all_orders.bp)

    return app

# Uncomment the below lines if you want debugging tools
app = create_app()
# toolbar.init_app(app)
