from flask import ( Blueprint, flash, g, redirect, render_template,
    request, session, url_for, Flask
)
from werkzeug.exceptions import abort
from auth import login_required, volunteer_required
from json import loads
from db import users, conn, orders
from sqlalchemy import and_, select
from send_confirmation import send_recieved_notification

bp = Blueprint('modify', __name__)

# request seems like it's a reserved word somewhere or something,
# so use request_items instead everywhere.
@bp.route('/modify', methods=('GET', 'POST'))
@login_required
@volunteer_required
def dashboard():
    itemsList = loads(open("items.json", "r").read()).keys()


    # Get all the volunteers that are assigned to our food bank
    volunteers = conn.execute(users.select().where(and_(users.c.foodBankId == g.user.id, users.c.role=="VOLUNTEER")))

    if request.method == "POST":
        '''
        userId = next(request.form.keys())
        print(userId)
        query = select([users.c.completed]).where(users.c.id==userId)
        completed = conn.execute(query).fetchone()[0]
        # If you refresh the page and resend data, it'll send 2 conformation emails. This prevents that.
        if (completed == 0):
            email = conn.execute(select([users.c.email]).where(users.c.id==userId)).fetchone()[0]
            send_recieved_notification(email)
            conn.execute(users.update().where(users.c.id==userId).values(completed=1))
            completedUsers = getUsers(1, zipCode)
            uncompletedUsers = getUsers(0, zipCode)
            
            for user in completedUsers:
                print(user)
        '''
    return render_template("modify_volunteers.html", users=dictList(volunteers))

# Basically this method takes all our volunteers
# and converts them into nice little dicts so that
# jinja2 can access all their data.
# This is a list of dicts of lists of dicts of dicts.
# VolunteerLIst --> volunteer --> assignedOrders --> order --> contents
def dictList(rows):
    toReturn = []
    for row in rows:
        volunteer = {}
        for column in conn.execute(users.select()).keys():
            volunteer[str(column)] = str(getattr(row, str(column)))
            print(str(column) + ": " + volunteer[str(column)])
        
        assignedOrders = conn.execute(orders.select(orders.c.volunteerId==volunteer['id'])).fetchall()
        assignedOrdersDictList = []
        for order in assignedOrders:
            orderDict = {}
            orderColumns = conn.execute(orders.select()).keys()
            for column in orderColumns:
                orderDict[column] = str(getattr(order, str(column)))

            userColumns = conn.execute(users.select()).keys()
            user = conn.execute(users.select(users.c.id==order['id'])).fetchone()
            for column in userColumns:
                if column not in orderColumns:
                    orderDict[column] = str(getattr(user, str(column)))
                else:
                    print("skipping " + column)
            orderDict['contents'] = loads(orderDict['contents'])

            assignedOrdersDictList.append(orderDict)
        volunteer['orders'] = assignedOrdersDictList
        toReturn.append(volunteer)

    return toReturn
