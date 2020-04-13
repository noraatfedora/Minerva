from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, Flask
)
from werkzeug.exceptions import abort
from src.auth import login_required, volunteer_required
from json import loads
from src.db import get_db

bp = Blueprint('dashboard', __name__)

# request seems like it's a reserved word somewhere or something,
# so use request_items instead everywhere.
@bp.route('/dashboard', methods=('GET', 'POST'))
@login_required
@volunteer_required
def dashboard():
    db = get_db()
    itemsList = loads(open("src/items.json", "r").read()).keys()
    print(itemsList)
    users = db.execute("SELECT * FROM USER WHERE role=\"RECEIVER\"")
    return render_template("dashboard.html", users=users, items=itemsList)