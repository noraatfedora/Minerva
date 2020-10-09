from flask import ( Blueprint, flash, g, redirect, render_template,
    request, session, url_for, Flask, make_response
)
from werkzeug.exceptions import abort
from minerva.backend.routes.auth import login_required, admin_required 
from json import loads, dumps
from collections import OrderedDict
from db import users, conn, routes
from sqlalchemy import and_, select
from os import environ
import assign, io, datetime, order_assignment
import google_maps_qr
from datetime import datetime
from minerva.backend.apis.email import send_recieved_notification, send_bagged_notification
bp = Blueprint('routes', __name__)

@login_required
@admin_required
@bp.route('/routes', methods=('GET', 'POST'))
def allOrders():
    #itemsList = conn.execute(items.select(items.c.foodBankId==g.user.foodBankId)).fetchall()
    routeList = getRoutes()
    if request.method == "GET" and "assignall" in request.args.keys():
        assign.createAllRoutes(foodBankId=g.user.id)
        return redirect('/allorders')
    volunteers = getVolunteers()
    #checkedInVolunteers = conn.execute(users.select().where(users.c.checkedIn==str(today))).fetchall()
    return render_template("routes_view.html", routes=routeList)

@login_required
@admin_required
@bp.route('/shipping_labels', methods=('GET', 'POST'))
def generate_shipping_labels():
    volunteers = getVolunteers()
    ordersDict = getOrders(g.user.id)
    itemsList = loads(conn.execute(users.select(users.c.id==g.user.foodBankId)).fetchone()['items'])
    html = render_template("shipping-labels.html", orders=ordersDict, volunteers=volunteers, barcode_to_base64=barcode_to_base64, qrcode_to_base64=qrcode_to_base64)
    # Uncomment this line for debugging
    #return html
    pdf = pdfkit.from_string(html, False)
    response = make_response(pdf)
    response.headers['Content-type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline;'
    return response

def getVolunteers():
    proxy = conn.execute(users.select(and_(users.c.role=="VOLUNTEER", users.c.approved==True, users.c.volunteerRole=="DRIVER"))).fetchall()
    dictList = []
    for volunteer in proxy:
        volunteerDict = {}
        columns = conn.execute(users.select()).keys()
        for column in columns:
            volunteerDict[column] = getattr(volunteer, column)
        volunteerDict['numOrders'] = len(conn.execute(orders.select(and_(orders.c.volunteerId==volunteer.id, orders.c.completed==0))).fetchall())
        dictList.append(volunteerDict)
    return dictList

def getRoutes():
    row2dict = lambda r: {c.name: str(getattr(r, c.name)) for c in routes.columns}
    rp = conn.execute(routes.select().where(routes.c.foodBankId==g.user.id)).fetchall()
    toReturn = []
    for route_rp in rp:
        routeDict = row2dict(route_rp)
        routeDict['userList'] = getUsers(route_rp.id)
        routeDict['google_maps'] = google_maps_qr.make_url(routeDict['userList'])
        routeDict['parsedContent'] = loads(route_rp.content)
        toReturn.append(routeDict)

    return toReturn

# Returns a list of users based off the given route ID
def getUsers(routeId):
    print("Route ID:" + str(routeId))
    row2dict = lambda r: {c.name: str(getattr(r, c.name)) for c in users.columns}
    # Get the ID's that our volunteer is assigned to
    route_rp = conn.execute(routes.select().where(routes.c.id==routeId)).fetchone()
    content = loads(route_rp.content)
    toReturn = []
    for userId in content:
        if userId != g.user.foodBankId: # Stupid to put the food bank on the user's list of orders
            user_rp = conn.execute(users.select().where(users.c.id==userId)).fetchone()
            userObj = row2dict(user_rp)
            userObj['doneToday'] = user_rp['lastDelivered'].date() == datetime.today().date()
            toReturn.append(userObj)

    return toReturn