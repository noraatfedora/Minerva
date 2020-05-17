from flask import ( Blueprint, flash, g, redirect, render_template,
    request, session, url_for, Flask
)
from werkzeug.exceptions import abort
from auth import login_required, admin_required 
from json import loads, dumps
from db import users, conn, orders
from sqlalchemy import and_, select
from send_conformation import send_recieved_notification

bp = Blueprint('view_all_orders', __name__)

@login_required
@admin_required
@bp.route('/allorders', methods=('GET', 'POST'))
def allOrders():
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
            conn.execute(orders.update().where(orders.c.id==orderId).values(bagged=1))
            ordersDict = getOrders(g.user.id)
    
    print("orders: " + str(orders))
    return render_template("view_all_orders.html", orders=ordersDict, items=itemsList)

# Returns a dictionary where the keys are the order ID's,
# and the values are dicts with attributes about that order (contents, email, etc.)
# All of these should be uncompleted orders, since an order is removed from a volunteer's
# list when it's completed.
def getOrders(adminId):
    # Get the ID's that our volunteer is assigned to
    orderIdList = conn.execute(select([orders.c.id]).where(and_(orders.c.foodBankId==g.user.id, orders.c.completed==0))).fetchall()
    toReturn = {} # We'll return this later
    for orderIdProxy in orderIdList:
        orderId = orderIdProxy[0]
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