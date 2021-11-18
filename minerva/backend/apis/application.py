import os
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, Flask
)
from minerva.backend.apis.db import conn, users
from barcode.writer import ImageWriter
from babel.dates import format_datetime
from datetime import datetime
from  flask_socketio import SocketIO, emit

print("In application.py!")

def format_datetime(value):
    format = "%Y-%m-%d %H:%M:%S.%f"
    dt = datetime.strptime(value, format)
    return dt.strftime("%B %d at %I:%M %p")
def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True, template_folder="../../frontend/templates", static_folder="../../frontend/static")
    app.config.from_mapping(
        SECRET_KEY = 'dev',
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    socketio = SocketIO(app)
    socketio.init_app(app)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # a simple page that says hello
    @app.route('/')
    def home():
        print("in home!")
        if g.user != None:
            defaults = {
                'RECIEVER': '/request_items',
                'VOLUNTEER': '/dashboard',
                'ADMIN': '/all_users'
            }
            return redirect(defaults[g.user.role])
        return render_template('home.html', title = 'Home')
    
    @app.route('/about')
    def about():
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

    print("About to register blueprints...")

    from minerva.backend.apis import db
    db.init_app(app)
    
    from minerva.backend.routes import auth
    app.register_blueprint(auth.bp)

    from minerva.backend.routes import dashboard
    app.register_blueprint(dashboard.bp)

    from minerva.backend.routes import request_items
    app.register_blueprint(request_items.bp)
    app.add_url_rule('/', endpoint='index')

    from minerva.backend.routes import modify_volunteers
    app.register_blueprint(modify_volunteers.bp)

    from minerva.backend.routes import view_all_users
    print("regestering view all users blueprint")
    app.register_blueprint(view_all_users.bp)

    from minerva.backend.routes import routes_view
    app.register_blueprint(routes_view.bp)

    from minerva.backend.routes import edit_user_page
    app.register_blueprint(edit_user_page.bp)

    app.jinja_env.filters['datetime'] = format_datetime

    print("Blueprints registered!")

    @socketio.on('message')
    def handle_message(message):
        print("Received message: ", message)

    return app


# Uncomment the below lines if you want debugging tools
app = create_app()
print("Created app!")
# toolbar.init_app(app)
