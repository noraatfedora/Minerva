from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, Flask
)
from werkzeug.exceptions import abort
from src.auth import login_required
from src.db import get_db

itemsList = [
    {
        'name': 'ramen',
        'category': 'food',
        'max': '20'
    },
    {
        'name': 'toothpaste',
        'category': 'hygiene',
        'max': '5'
    }

]


bp = Blueprint('request_items', __name__)

# request seems like it's a reserved word somewhere or something,
# so use request_items instead everywhere.
@bp.route('/request_items', methods=('GET', 'POST'))
@login_required
def request_items():
    if request.method == "POST":
        items = request.form['items']
        error = None
        print("Items: " + items)
        if not items:
            error = "Items are required."
        
        if error is not None:
            flash(error)
        else:
            db = get_db()
            sqlcommand = """UPDATE user SET items = ? WHERE email = ?"""
            print(sqlcommand)
            db.execute(
                sqlcommand,
                (items, g.user['email'])
            )
            db.commit()
            return redirect("/index")
    
    return render_template("request_items.html",items = itemsList)
