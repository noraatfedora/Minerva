from flask import ( Blueprint, flash, g, redirect, render_template,
    request, session, url_for, Flask, make_response
)
from werkzeug.exceptions import abort
from auth import login_required, admin_required 
from json import loads, dumps
from collections import OrderedDict
from db import users, conn, orders
from sqlalchemy import and_, select
from os import environ
from barcode import Code128
from barcode.writer import ImageWriter
import assign, io, pdfkit, base64, qrcode, datetime, order_assignment
from send_confirmation import send_recieved_notification, send_bagged_notification
bp = Blueprint('view_all_orders', __name__)

@login_required
@admin_required
@bp.route('/allorders', methods=('GET', 'POST'))
def allOrders():
    itemsList = loads(conn.execute(users.select(users.c.id==g.user.foodBankId)).fetchone()['items'])
    ordersDict = getOrders(g.user.id)
    if request.method == "GET" and "assignall" in request.args.keys():
        assign.assignAllOrders(g.user.id)
        return redirect('/allorders')
    if request.method == "GET" and "volunteer" in request.args.keys():
        volunteerId = int(request.args.get("volunteer"))
        orderId = int(request.args.get("order"))
        order_assignment.assign(orderId=orderId, volunteerId=volunteerId)
        return redirect("/allorders")
    if request.method == "POST":
        key = next(request.form.keys())
        print("Key: " + str(key))
        if "unassign" in key:
            orderId = int(key[len('unassign-'):])
            order_assignment.unassign(orderId)
            ordersDict = getOrders(g.user.id)
        elif "bag" in key:
            orderId = int(key[len('bag-'):])
            order_assignment.bag(orderId)
            ordersDict = getOrders(g.user.id)
        elif "barcode" in key:
            baggedIds = request.form[key].split('\r\n')
            for order in baggedIds:
                order_assignment.bag(order)
    volunteers = getVolunteers()
    today = datetime.date.today()
    checkedInVolunteers = conn.execute(users.select().where(users.c.checkedIn==str(today))).fetchall()
    return render_template("view_all_orders.html", orders=ordersDict, volunteers=volunteers, checkedIn=checkedInVolunteers)

@login_required
@admin_required
@bp.route('/shipping_labels', methods=('GET', 'POST'))
def generate_shipping_labels():
    volunteers = getVolunteers()
    ordersDict = getOrders(g.user.id)
    itemsList = loads(conn.execute(users.select(users.c.id==g.user.foodBankId)).fetchone()['items'])
    html = render_template("shipping-labels.html", orders=ordersDict, volunteers=volunteers)
    # Uncomment this line for debugging
    #return html
    pdf = pdfkit.from_string(html, False)
    response = make_response(pdf)
    response.headers['Content-type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline;'
    return response

# Returns a dictionary where the keys are the order ID's,
# and the values are dicts with attributes about that order (contents, email, etc.)
# All of these should be uncompleted orders, since an order is removed from a volunteer's
# list when it's completed.
def getOrders(adminId):
    # Get the ID's that our volunteer is assigned to
    orderIdList = conn.execute(select([orders.c.id]).where(and_(orders.c.foodBankId==g.user.id, orders.c.completed==0)).order_by(orders.c.date)).fetchall()
    toReturn = OrderedDict() # Sorted by date
    for orderIdProxy in orderIdList:
        orderId = orderIdProxy[0]
        toReturn[orderId] = {}
        order = conn.execute(orders.select().where(orders.c.id==orderId)).fetchone()
        user = conn.execute(users.select().where(users.c.id==order['userId'])).fetchone()
        # Add all our user's attributes to our order
        userColumns = conn.execute(users.select()).keys()
        userColumns.remove('id')
        for column in userColumns:
            toReturn[orderId][str(column)] = str(getattr(user, str(column)))
        # And all our order's attributes
        for column in conn.execute(orders.select()).keys():        
            toReturn[orderId][str(column)] = str(getattr(order, str(column)))
        toReturn[orderId]['itemsDict'] = loads(toReturn[orderId]['contents'])
        volunteerName = conn.execute(select([users.c.name], users.c.id==order.volunteerId)).fetchone()
        if not volunteerName is None:
            toReturn[orderId]['volunteerName'] = volunteerName[0]
            
    return toReturn 

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

def barcode_to_base64(orderId):
    imgByteArray = io.BytesIO()
    Code128(str(orderId) + "\n", writer=ImageWriter()).write(imgByteArray)
    return base64.b64encode(imgByteArray.getvalue()).decode()

def qrcode_to_base64(orderId):
    urlString = request.base_url[:-len('shipping_labels')] + 'auto_complete?orderId=' + str(orderId)
    imgByteArray = io.BytesIO()
    code = qrcode.make(urlString)
    code.save(imgByteArray, format="PNG")
    return base64.b64encode(imgByteArray.getvalue()).decode()