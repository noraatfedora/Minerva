from flask import ( Blueprint, flash, g, redirect, render_template,
    request, session, url_for, Flask, make_response
)
from werkzeug.exceptions import abort
from minerva.backend.routes.auth import login_required, volunteer_required
from json import loads, dumps
from minerva.backend.apis.db import users, conn, routes
from minerva.backend.apis.assign import getNextRoute
from sqlalchemy import and_, select
from minerva.backend.apis.email import send_recieved_notification
from datetime import date, datetime, timedelta
from os import environ
from minerva.backend.apis import google_maps_qr
import pdfkit

bp = Blueprint('dashboard', __name__)

# request seems like it's a reserved word somewhere or something,
# so use request_items instead everywhere.
@bp.route('/dashboard', methods=('GET', 'POST'))
@login_required
@volunteer_required
def dashboard():
    # Uncomment this line for testing. This gives everyone mailinator emails,
    # so that you don't accidentally send them conformiation emails while testing.
    #makeAllEmailsMailinator()


    if request.method == "GET" and "claimRoute" in request.args.keys():
        print("Getting next route...")
        route = getNextRoute(g.user.id, g.user.foodBankId)
        print("route: " + str(route))
        #conn.execute(users.update().where(users.c.id==g.user.id).values(ordering=dumps(route)))
        return redirect('/dashboard')
    if request.method == "POST":
        firstKey = next(request.form.keys())
        userId = int(firstKey)
        conn.execute(
            users.update().where(
                users.c.id==userId
            ).values(lastDelivered=datetime.now())
        )
        # If you refresh the page and resend data, it'll send 2 confirmation emails. This if statement prevents that.
        email = conn.execute(
            select([users.c.email]).where(
                users.c.id==userId
            )
        ).fetchone()[0]
        send_recieved_notification(email)

    routeId = conn.execute(select([routes.c.id]).where(routes.c.volunteerId==g.user.id)).fetchone()
    if routeId == None:
        return render_template("dashboard.html", users=[], google_maps = "")
    else:
        routeId = routeId[0]
    userList = getUsers(routeId)
    checkedIn = g.user.checkedIn == str(date.today())
    return render_template("dashboard.html", users=userList, approved=g.user.approved, google_maps = google_maps_qr.make_url(userList))

def makeAllEmailsMailinator():
    userList = conn.execute(users.select()).fetchall()
    for user in userList:
        if not user['email'] == None and not '@mailinator.com' in user['email']:
            newEmail = user['name'].replace(' ', '') + "@mailinator.com"
            conn.execute(users.update().where(users.c.id==user.id).values(email=newEmail))


@login_required
@volunteer_required
@bp.route('/auto_complete', methods=(['GET']))
def qr_mark_as_complete():
    if "orderId" in request.args.keys():
        orderId = int(request.args['orderId'])
        order = conn.execute(orders.select().where(orders.c.id==orderId)).fetchone()
        if order.completed == 0:
            email = conn.execute(select([users.c.email]).where(users.c.id==order.userId)).fetchone()[0]
            send_recieved_notification(email)
            conn.execute(orders.update().where(orders.c.id==orderId).values(completed=1))
    return "Order " + str(orderId) + " has been marked as complete."

@bp.route('/driver_printout', methods=('GET', 'POST'))
def driver_printout():
    routeId = conn.execute(routes.select().where(routes.c.volunteerId==g.user.id)).fetchone()
    if routeId == None:
        return redirect('/dashboard')
    else:
        routeId = routeId[0]
    usersList = getUsers(routeId)

    html = render_template("driver_printout.html", users=usersList, volunteer=g.user)

    pdf = pdfkit.from_string(html, False)

    response = make_response(pdf)
    response.headers['Content-type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline;'

    #return html
    return response

# Returns a list of users based off the given route ID
def getUsers(routeId):
    print("Route ID:" + str(routeId))
    row2dict = lambda r: {c.name: str(getattr(r, c.name)) for c in users.columns}
    # Get the ID's that our volunteer is assigned to
    route_rp = conn.execute(routes.select().where(routes.c.id==routeId)).fetchone()
    content = loads(route_rp.content)
    toReturn = []
    allDone = True
    for userId in content:
        if userId != g.user.foodBankId: # Stupid to put the food bank on the user's list of orders
            user_rp = conn.execute(users.select().where(users.c.id==userId)).fetchone()
            if user_rp == None:
                continue
            userObj = row2dict(user_rp)
            userObj['doneToday'] = user_rp['lastDelivered'].date() == datetime.today().date()
            if not userObj['doneToday']:
                allDone = False
            toReturn.append(userObj)
            userObj['googleMapsUrl'] = google_maps_qr.make_single_url(userObj['formattedAddress'])

    print("Users: " + str(toReturn))
    if allDone:
        conn.execute(routes.update().where(routes.c.id==routeId).values(volunteerId=-1))
    return toReturn


def getAddresses(orders):
    #TODO
    return []
