import os
from . import db, auth
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, Flask
)

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'requests.sqlite'),
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

    # Home page
    @app.route('/')
    def index():
        return render_template("index.html")

    # Request food page, redirects to sign in page if you're not signed in
    @app.route('/request')
    def request():
        if g.user is None:
            return redirect(url_for("auth.login", redirect_url="request"))
        else:
            return render_template("request.html")

    db.init_app(app)

    app.register_blueprint(auth.bp)
    
    return app
    