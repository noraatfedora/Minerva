from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, Flask
)
from werkzeug.exceptions import abort
from auth import login_required
from db import users, conn
from send_conformation import send_request_conformation
from json import loads, dumps

itemsList = loads(open("items.json", "r").read())
bp = Blueprint('request_items', __name__)

# request seems like it's a reserved word somewhere or something,
# so use request_items instead everywhere.
@bp.route('/request_items', methods=('GET', 'POST'))
@login_required
def request_items():
    if request.method == "POST":
        itemsDict = {} # Used for email conformation script
        for item in itemsList.values():
            name = item['name']
            quantity = request.form[name + "-quantity"]
            itemsDict[name] = quantity

        send_request_conformation(g.user['email'], itemsDict)
        conn.execute(users.update().where(users.c.id==g.user['id'])
            .values(order=dumps(itemsDict), completed=0))
        return redirect("/success")
    
    return render_template("request_items.html",items = itemsList.values())
