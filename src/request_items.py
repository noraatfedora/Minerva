from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, Flask
)
from werkzeug.exceptions import abort
from src.auth import login_required
from src.db import get_db
from src.send_conformation import send_request_conformation
from json import loads

itemsList = loads(open("src/items.json", "r").read())
bp = Blueprint('request_items', __name__)

# request seems like it's a reserved word somewhere or something,
# so use request_items instead everywhere.
@bp.route('/request_items', methods=('GET', 'POST'))
@login_required
def request_items():
    if request.method == "POST":
        db = get_db()
        sqlcommand = 'UPDATE user'
        itemsDict = {} # Used for email conformation script
        for item in itemsList.values():
            name = item['name']
            quantity = request.form[name + "-quantity"]
            db.execute("UPDATE user SET " + name + " = ? WHERE id = ?", (quantity, str(g.user['id'])))
            itemsDict[name] = quantity

        send_request_conformation(g.user['email'], itemsDict)
        db.execute("UPDATE user SET completed=0 WHERE ID=?", (str(g.user['id']),))
        db.commit()
        return redirect("/home")
    
    return render_template("request_items.html",items = itemsList.values())