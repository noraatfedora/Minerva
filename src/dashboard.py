from flask import ( Blueprint, flash, g, redirect, render_template,
    request, session, url_for, Flask
)
from werkzeug.exceptions import abort
from auth import login_required, volunteer_required
from json import loads, dumps
from db import users, conn, orders
from sqlalchemy import and_, select
from send_confirmation import send_recieved_notification

bp = Blueprint('dashboard', __name__)

# request seems like it's a reserved word somewhere or something,
# so use request_items instead everywhere.
@bp.route('/dashboard', methods=('GET', 'POST'))
@login_required
@volunteer_required
def dashboard():
    itemsList = loads(open("items.json", "r").read()).keys()

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
            # Remove the order from the volunteer's list
            orderList = loads(str(conn.execute(select([users.c.assignedOrders]).where(users.c.id==g.user.id)).fetchone()[0]))
            orderList.remove(orderId)
            conn.execute(users.update().where(users.c.id==g.user.id).values(assignedOrders=dumps(orderList)))
            ordersDict = getOrders(g.user.id)
    
    print("orders: " + str(orders))
    return render_template("dashboard.html", orders=ordersDict, items=itemsList, optimap=generate_optimap(getAddresses(orders)))

# Returns a dictionary where the keys are the order ID's,
# and the values are dicts with attributes about that order (contents, email, etc.)
# All of these should be uncompleted orders, since an order is removed from a volunteer's
# list when it's completed.
def getOrders(volunteerId):
    # Get the ID's that our volunteer is assigned to
    query = select([users.c.assignedOrders]).where(users.c.id==volunteerId)
    output = conn.execute(query).fetchone()[0]
    print("Output: " + str(output))
    orderIdList = loads(output)

    toReturn = {} # We'll return this later
    for orderId in orderIdList:
        toReturn[orderId] = {}
        order = conn.execute(orders.select().where(orders.c.id==orderId)).fetchone()
        print("Order: " + str(order))
        user = conn.execute(users.select().where(users.c.id==order['userId'])).fetchone()
        # Add all our user's attributes to our order
        userColumns = conn.execute(users.select()).keys()
        userColumns.remove('id')
        for column in userColumns:
            toReturn[orderId][str(column)] = str(getattr(user, str(column)))
        # And all our order's attributes
        for column in conn.execute(orders.select()).keys():        
            toReturn[orderId][str(column)] = str(getattr(order, str(column)))

        #print("Keys: ", str(conn.execute(orders.select()).keys()))
        toReturn[orderId]['itemsDict'] = loads(toReturn[orderId]['contents'])

    print("toReturn: " + str(toReturn)) 
    return toReturn 

def getAddresses(orders):
    #TODO 
    return []

def generate_optimap(addresses):
    link = "http://gebweb.net/optimap/index.php?loc0=" + g.user['address'] # Starts at volunteer's address, we might want to change this
    for x in range(0, len(addresses)):
        link += "&loc" + str(x+1) + "=" + addresses[x]
    return link.replace(" ", "%20")
