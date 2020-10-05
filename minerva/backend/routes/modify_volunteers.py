from flask import ( Blueprint, flash, g, redirect, render_template,
    request, session, url_for, Flask)
from werkzeug.exceptions import abort
from minerva.backend.routes.auth import login_required, volunteer_required
from json import loads
from datetime import datetime
from minerva.backend.apis.db import users, conn
from sqlalchemy import and_, select
from os import environ
from order_assignment import unassign
from minerva.backend.apis.email import send_volunteer_acceptance_notification

bp = Blueprint('modify', __name__)

# request seems like it's a reserved word somewhere or something,
# so use request_items instead everywhere.
@bp.route('/modify', methods=('GET', 'POST'))
@login_required
@volunteer_required
def dashboard():
    # itemsList = loads(conn.execute(users.select(users.c.id==g.user.foodBankId)).fetchone()['items'])

    # Get all the volunteers that are assigned to our food bank
    volunteers = conn.execute(users.select().where(and_(users.c.foodBankId == g.user.id, users.c.role=="VOLUNTEER", users.c.approved==True)))
    unassigned = conn.execute(users.select().where(and_(users.c.foodBankId == g.user.id, users.c.role=="VOLUNTEER", users.c.approved==False)))
    if request.method == "GET" and "assign" in request.args.keys():
        conn.execute(users.update(users.c.name==request.args['assign']).values(approved=True))
        volunteerEmail = conn.execute(select([users.c.email]).where(users.c.name==request.args['assign'])).fetchone()[0]
        send_volunteer_acceptance_notification(volunteerEmail, g.user.name)
        return redirect("/modify")
    if request.method == "POST":
        try:
            key = next(request.form.keys())
        except:
            key = ""
        print("Key: " + key)
        if "unassign" in key:
            orderId = key[len('unassign-'):]
            unassign(int(orderId))
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
    return render_template("modify_volunteers.html", volunteers=getVolunteerInfoList(g.user.id), unassigned=unassigned)

# Returns a list of users based off the volunteer's ordering column
def getUsers(volunteer):
    row2dict = lambda r: {c.name: str(getattr(r, c.name)) for c in users.columns}
    # Get the ID's that our volunteer is assigned to
    ordering = loads(volunteer['ordering'])
    toReturn = []
    for userId in ordering:
        if userId != volunteer['foodBankId']: # Stupid to put the food bank on the user's list of orders
            user_rp = conn.execute(users.select().where(users.c.id==userId)).fetchone()
            userObj = row2dict(user_rp)
            userObj['doneToday'] = user_rp['lastDelivered'].date() == datetime.today().date()
            toReturn.append(userObj)

    print("Users: " + str(toReturn))
    return toReturn



def getVolunteerInfoList(foodBankId):
    row2dict = lambda r: {c.name: str(getattr(r, c.name)) for c in users.columns}
    volunteerList = conn.execute(users.select().where(and_(users.c.role=="VOLUNTEER", users.c.foodBankId==foodBankId)))
    toReturn = []
    for volunteer_rp in volunteerList:
        volunteerDict = row2dict(volunteer_rp)
        volunteerDict['userList'] = getUsers(volunteerDict)
        toReturn.append(volunteerDict)
    return toReturn