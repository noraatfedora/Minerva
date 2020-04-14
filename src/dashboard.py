from flask import ( Blueprint, flash, g, redirect, render_template,
    request, session, url_for, Flask
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
    users = db.execute("SELECT * FROM USER WHERE role=\"RECEIVER\"") 
    if request.method == "POST":
        userId = next(request.form.keys())
        db.execute("UPDATE USER SET completed=1 WHERE ID=" + userId)
        db.commit()
        users = db.execute("SELECT * FROM USER WHERE role=\"RECEIVER\"") 
    generate_optimap()
    return render_template("dashboard.html", users=users, items=itemsList, optimap=generate_optimap())

def generate_optimap():
    db = get_db()
    users = db.execute("SELECT * FROM USER WHERE role=\"RECEIVER\" AND completed=0") 
    addresses = []
    for user in users:
       addresses.append(user['address']) 
    link = "http://gebweb.net/optimap/index.php?loc0=2640 134th ave ne Bellevue, WA 98005"
    for x in range(0, len(addresses)):
        link += "&loc" + str(x+1) + "=" + addresses[x]
    return link.replace(" ", "%20")