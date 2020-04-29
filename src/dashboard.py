from flask import ( Blueprint, flash, g, redirect, render_template,
    request, session, url_for, Flask
)
from werkzeug.exceptions import abort
from auth import login_required, volunteer_required
from json import loads
from db import users, conn
from sqlalchemy import and_, select
from send_conformation import send_recieved_notification

bp = Blueprint('dashboard', __name__)

# request seems like it's a reserved word somewhere or something,
# so use request_items instead everywhere.
@bp.route('/dashboard', methods=('GET', 'POST'))
@login_required
@volunteer_required
def dashboard():
    itemsList = loads(open("items.json", "r").read()).keys()
    filter = False
    zipCode = ""

    if 'zipCode' in request.args:
        filter = True 
        zipCode = request.args['zipCode']
        # save list in our volunteer's column so they don't need to reenter
        conn.execute(users.update().where(users.c.id==g.user['id']).values(assignedZipCodes=zipCode))
    else:
        zipCode = str(conn.execute(select([users.c.assignedZipCodes]).where(users.c.id==g.user['id'])).fetchone()[0])


    completedUsers = getUsers(1, zipCode)
    uncompletedUsers = getUsers(0, zipCode)

    if request.method == "POST":
        userId = next(request.form.keys())
        print(userId)
        query = select([users.c.completed]).where(users.c.id==userId)
        completed = conn.execute(query).fetchone()[0]
        print("completeedddsf: " + str(completed))
        # If you refresh the page and resend data, it'll send 2 conformation emails. This prevents that.
        if (completed == 0):
            email = conn.execute(select([users.c.email]).where(users.c.id==userId)).fetchone()[0]
            send_recieved_notification(email)
            conn.execute(users.update().where(users.c.id==userId).values(completed=1))
            completedUsers = getUsers(1, zipCode)
            uncompletedUsers = getUsers(0, zipCode)
            
            for user in completedUsers:
                print(user)
    return render_template("dashboard.html", completedUsers=completedUsers, uncompletedUsers=uncompletedUsers, items=itemsList, optimap=generate_optimap(completedUsers), zipDefault=zipCode)

def getUsers(completed, zipCode):
    if zipCode != "":
        zipList = zipCode.replace(" ", "").split(",")
        toReturn = []
        for code in zipList:
            toReturn += dictList(conn.execute(users.select().where(and_(users.c.role=="RECIEVER", users.c.completed==completed, users.c.zipCode==code))))
        return toReturn
    else:
        return dictList(conn.execute(users.select().where(and_(users.c.role=="RECIEVER", users.c.completed==completed))))

# A list of dicts, where each dict contains a dict.
def dictList(rows):
    toReturn = []
    for row in rows:
        user = {}
        print("asdf" + str(row))
        for column in conn.execute(users.select()).keys():
            user[str(column)] = str(getattr(row, str(column)))
            print(str(column) + ": " + user[str(column)])
        if user['order'] != "None":
            print("Order: " + user['order'])
            user['itemsDict'] = loads(str(user['order']))
            toReturn.append(user)

    for user in toReturn:
        user['itemsDict'] = loads(user['order'])

    return toReturn


def generate_optimap(completedUsers):
    addresses = []
    print("owo")
    for user in completedUsers:
       addresses.append(user['address']) 
    link = "http://gebweb.net/optimap/index.php?loc0=" + g.user['address'] # Starts at volunteer's address, we might want to change this
    for x in range(0, len(addresses)):
        link += "&loc" + str(x+1) + "=" + addresses[x]
    return link.replace(" ", "%20")
