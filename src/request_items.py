from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, Flask
)
from werkzeug.exceptions import abort
from src.auth import login_required
from src.db import get_db
from json import loads

print("bippity boop")
itemsList = loads(open("src/items.json", "r").read())
bp = Blueprint('request_items', __name__)

# request seems like it's a reserved word somewhere or something,
# so use request_items instead everywhere.
@bp.route('/request_items', methods=('GET', 'POST'))
@login_required
def request_items():
    print("asdfdsfdsfljkfsdljk")
    if request.method == "POST":
        print("in if statement")
        db = get_db()
        sqlcommand = "UPDATE user"
        for item in itemsList.values():
            name = request.form[item['name']]
            sqlcommand += " SET " + name + "= ?"
        sqlcommand += "WHERE email = ?"
        print(sqlcommand)
        db.execute(
            sqlcommand,
            tuple(itemsList.values()) + (g.user['email'],)
        )
        db.commit()
        return redirect("/home")
    
    return render_template("request_items.html",items = itemsList.values())