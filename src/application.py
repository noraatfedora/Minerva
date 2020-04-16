import os
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

    import db
    db.init_app(app)
    
    import auth
    app.register_blueprint(auth.bp)

    import dashboard
    app.register_blueprint(dashboard.bp)
    # request.py has blueprints for both requesting and displaying orders
    # KARTHIK: That's the file where you put your cool google sheets stuff!
    import request_items 
    app.register_blueprint(request_items.bp)
    app.add_url_rule('/', endpoint='index')

    return app

if __name__ == '__main__':
    create_app()

app = create_app()
