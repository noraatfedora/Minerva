from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, Flask
)
from werkzeug.exceptions import abort
from src.auth import login_required
from src.db import get_db

bp = Blueprint('request_items', __name__)

# request seems like it's a reserved word somewhere or something,
# so use request_items instead everywhere.
@bp.route('/request_items', methods=('GET', 'POST'))
@login_required
def request_items():
    if request.method == "POST":
        items = request.form['items']
        error = None

        if not items:
            error = "Items are required."
        
        if error is not None:
            flash(error)
        else:
            db = get_db()
            
            db.execute(
                'UPDATE user' # change the params for users so that
                'SET items = ?' # they have the given items
                'WHERE email = ?', # but only for our logged in user.
                # email is set to be unique, so each email has to correspond
                # to exactly 1 user.
                (items, g.user.email)
            )
            return redirect("/index")
    
    return render_template("request_items.html")
