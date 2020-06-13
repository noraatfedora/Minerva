from flask import ( Blueprint, flash, g, redirect, render_template,
    request, session, url_for, Flask
)
from werkzeug.exceptions import abort
from auth import login_required, volunteer_required
from json import loads, dumps
from db import users, conn, orders
from sqlalchemy import and_, select
from send_confirmation import send_recieved_notification
from datetime import date
from os import environ
import google_maps_qr

bp = Blueprint('dashboard', __name__)

# request seems like it's a reserved word somewhere or something,
# so use request_items instead everywhere.
@bp.route('/dashboard', methods=('GET', 'POST'))
@login_required
@volunteer_required
def dashboard():
    itemsList = loads(conn.execute(users.select(users.c.id==g.user.foodBankId)).fetchone()['items'])

    ordersDict = getOrders(g.user.id)
    if request.method == "GET" and "checkin" in request.args.keys():
        conn.execute(users.update().where(users.c.id==g.user.id).values(checkedIn=str(date.today())))
        return redirect('/dashboard')
    if request.method == "POST":
        firstKey = next(request.form.keys())
        orderId = int(firstKey)
        query = select([orders.c.completed]).where(orders.c.id==orderId)
        completed = conn.execute(query).fetchone()[0]
        print("completeedddsf: " + str(completed))
        # If you refresh the page and resend data, it'll send 2 conformation emails. This if statement prevents that.
        if (completed == 0):
            email = ordersDict[orderId]['email']
            send_recieved_notification(email)
            conn.execute(orders.update().where(orders.c.id==orderId).values(completed=1))
            ordersDict = getOrders(g.user.id)

    print("orders: " + str(orders))
    return render_template("dashboard.html", orders=ordersDict, items=itemsList, google_maps = google_maps_qr.make_url(loads(g.user.ordering)))

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
    itemsList = loads(open(environ['INSTANCE_PATH'] + "items.json", "r").read()).keys()

    ordersDict = getOrders(g.user.id)

    if request.method == "POST":
        orderId = int(next(request.form.keys()))
        query = select([orders.c.completed]).where(orders.c.id==orderId)
        completed = conn.execute(query).fetchone()[0]
        print("completeedddsf: " + str(completed))
        # If you refresh the page and resend data, it'll send 2 conformation emails. This if statement prevents that.
        if (completed == 0):
            email = ordersDict[orderId]['email']
            send_recieved_notification(email)
            conn.execute(orders.update().where(orders.c.id==orderId).values(completed=1))
            ordersDict = getOrders(g.user.id)
    
    print("orders: " + str(orders))
    return render_template("driver_printout.html", orders=ordersDict, items=itemsList, volunteer=g.user)

# Returns a dictionary where the keys are the order ID's,
# and the values are dicts with attributes about that order (contents, email, etc.)
# All of these should be uncompleted orders, since an order is removed from a volunteer's
# list when it's completed.
def getOrders(volunteerId):
    # Get the ID's that our volunteer is assigned to
    orderList = conn.execute(orders.select(and_(orders.c.volunteerId==g.user.id, orders.c.completed==0, orders.c.bagged==1))).fetchall()

    toReturn = {} # We'll return this later
    for order in orderList:
        toReturn[order.id] = {}
        user = conn.execute(users.select().where(users.c.id==order['userId'])).fetchone()
        # Add all our user's attributes to our order
        userColumns = conn.execute(users.select()).keys()
        userColumns.remove('id')
        for column in userColumns:
            toReturn[order.id][str(column)] = str(getattr(user, str(column)))
        # And all our order's attributes
        for column in conn.execute(orders.select()).keys():        
            toReturn[order.id][str(column)] = str(getattr(order, str(column)))

        toReturn[order.id]['itemsDict'] = loads(toReturn[order.id]['contents'])

    return toReturn

def getAddresses(orders):
    #TODO 
    return []
