from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, Flask
)
from werkzeug.exceptions import abort
from auth import login_required
from db import users, conn, orders
from send_confirmation import send_request_confirmation
from json import loads, dumps
import datetime
from sqlalchemy import select, and_
from os import environ
from sys import path

bp = Blueprint('request_items', __name__)
strf = "%A, %B %d" # will output dates in the format like "May 31"

# request seems like it's a reserved word somewhere or something,
# so use request_items instead everywhere.
@bp.route('/request_items', methods=('GET', 'POST'))
@login_required
def request_items():
    itemsList = loads(conn.execute(users.select(users.c.id==g.user.foodBankId)).fetchone()['items'])
    if request.method == "POST":
        itemsDict = {} # Used for email confirmation script
        for item in itemsList:
            name = item['name']
            quantity = request.form[name]
            itemsDict[name] = quantity


        # date = datetime.datetime.strptime(request.form['date'], "%Y-%m-%d")
        # date.strftime("%A, %B %e")

        send_request_confirmation(g.user['email'], itemsDict, "date strftime would go here")

        # Make sure that the user only orders once per week by marking all their
        # old orders as completed
        conn.execute(orders.update(orders.c.userId==g.user.id).values(completed=1))
        # insert new order into the orders table
        orderId = conn.execute(orders.insert(), contents=dumps(itemsDict), completed=0, bagged=0, userId=g.user.id, foodBankId=g.user.foodBankId, date="").inserted_primary_key[0]
        return redirect("/success")
    categories = []
    return render_template("request_items.html", items=itemsList, categories=categories, dates="availableDates() would go here")

def availableDates():
    numDays = 10 # number of available days to display
    toReturn = []
    currentDay = datetime.date.today() + datetime.timedelta(days=1)
    whereClauses = {"sunday":users.c.sunday, "monday":users.c.monday,
                "tuesday":users.c.tuesday, "wednesday":users.c.wednesday,
                "thursday":users.c.thursday, "friday":users.c.friday,
                "saturday":users.c.saturday}
    while len(toReturn) < numDays:
        dayOfWeek = currentDay.strftime("%A").lower()
        volunteers = conn.execute(users.select(whereclause=and_(whereClauses[dayOfWeek]==True, users.c.foodBankId==g.user.foodBankId, users.c.approved==True))).fetchall()
        maxOrders = conn.execute(select([users.c.maxOrders]).where(users.c.id==g.user.foodBankId)).fetchone()[0]
        eligibleVolunteers = []
        for volunteer in volunteers:
            ordersList = conn.execute(orders.select(whereclause=(and_(orders.c.volunteerId==volunteer.id, orders.c.completed==0)))).fetchall()
            if len(ordersList) < maxOrders:
                eligibleVolunteers.append(volunteer)
        if len(eligibleVolunteers) > 0:
            toReturn.append(currentDay)
        currentDay = currentDay + datetime.timedelta(days=1)

    return toReturn
