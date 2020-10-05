from flask import ( Blueprint, flash, g, redirect, render_template,
    request, session, url_for, Flask, make_response
)
from werkzeug.exceptions import abort
from minerva.backend.routes.auth import login_required, admin_required 
from json import loads, dumps
from collections import OrderedDict
from db import users, conn, items
from sqlalchemy import and_, select
from os import environ
from barcode import Code128
from barcode.writer import ImageWriter
import assign, io, pdfkit, base64, qrcode, datetime, order_assignment
from minerva.backend.apis.email import send_recieved_notification, send_bagged_notification
bp = Blueprint('view_all_orders', __name__)

@login_required
@admin_required
@bp.route('/allorders', methods=('GET', 'POST'))
def allOrders():
    #itemsList = conn.execute(items.select(items.c.foodBankId==g.user.foodBankId)).fetchall()
    userList = conn.execute(users.select().where(users.c.foodBankId == g.user.id)).fetchall()
    if request.method == "GET" and "assignall" in request.args.keys():
        assign.createAllRoutes(foodBankId=g.user.id)
        return redirect('/allorders')
    if request.method == "GET" and "volunteer" in request.args.keys():
        volunteerId = int(request.args.get("volunteer"))
        orderId = int(request.args.get("order"))
        order_assignment.assign(orderId=orderId, volunteerId=volunteerId)
        return redirect("/allorders")
    if request.method == "POST":
        key = next(request.form.keys())
        print("Key: " + str(key))
        if "delete" in key: #TODO
            userId = int(key[len('bag-'):])
            userList = conn.execute(users.select().where(users.c.foodBankId == g.user.id)).fetchall()
    volunteers = getVolunteers()
    today = datetime.date.today()
    #checkedInVolunteers = conn.execute(users.select().where(users.c.checkedIn==str(today))).fetchall()
    return render_template("view_all_orders.html", users=userList, volunteers=volunteers)

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