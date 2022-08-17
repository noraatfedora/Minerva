from flask import ( Blueprint, flash, g, redirect, render_template,
    request, session, url_for, Flask, make_response
)
from werkzeug.exceptions import abort
from minerva.backend.routes.auth import login_required, volunteer_required
from json import loads, dumps
from minerva.backend.apis.db import users, conn, routes
from sqlalchemy import and_, select
from minerva.backend.apis.email import send_recieved_notification
from datetime import date, datetime, timedelta
from os import environ
from minerva.backend.apis import google_maps_qr
import pdfkit

bp = Blueprint('dashboard', __name__)
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
