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

itemsList = loads(open("items.json", "r").read())
categories = set()
for item in itemsList.values():
    categories.add(item['subcategory'])
bp = Blueprint('request_items', __name__)
strf = "%A, %B %d" # will output dates in the format like "May 31"

# request seems like it's a reserved word somewhere or something,
# so use request_items instead everywhere.
@bp.route('/request_items', methods=('GET', 'POST'))
@login_required
def request_items():
    if request.method == "POST":
        itemsDict = {} # Used for email conformation script
        for item in itemsList.values():
            name = item['name']
            quantity = request.form[name + "-quantity"]
            itemsDict[name] = quantity
        print("Date: " + str(request.form['date']))
        date = datetime.datetime.strptime(request.form['date'] + " 2020", strf + " %Y")
        print("Processed date: " + str(date))
        send_request_confirmation(g.user['email'], itemsDict)

        # Make sure that the user only orders once per week by marking all their
        # old orders as completed 
        conn.execute(orders.update(orders.c.userId==g.user.id).values(completed=1))
        # insert new order into the orders table
        orderId = conn.execute(orders.insert(), contents=dumps(itemsDict), completed=0, bagged=0, userId=g.user.id, foodBankId=g.user.foodBankId, date=date).inserted_primary_key[0]
        return redirect("/success")
    
    return render_template("request_items.html", items = itemsList.values(), categories=categories, dates=availableDates())

def availableDates():
    numDays = 10 # number of available days to display
    toReturn = []
    currentDay = datetime.date.today() + datetime.timedelta(days=1)
    print("Finding available dates...")
    while len(toReturn) < numDays:
        print("loo[p")
        dayOfWeek = currentDay.strftime("%A").lower()
        #days = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
        whereClauses = {"sunday":users.c.sunday, "monday":users.c.monday,
                        "tuesday":users.c.tuesday, "wednesday":users.c.wednesday,
                        "thursday":users.c.wednesday, "friday":users.c.friday,
                        "saturday":users.c.saturday}
        volunteers = conn.execute(users.select(whereclause=and_(whereClauses[dayOfWeek]==True, users.c.foodBankId==g.user.foodBankId, users.c.approved==True))).fetchall()
        print("Volunteers: " + str(volunteers))
        maxOrders = conn.execute(select([users.c.maxOrders]).where(users.c.id==g.user.foodBankId)).fetchone()[0]
        eligibleVolunteers = []
        for volunteer in volunteers:
            ordersList = conn.execute(orders.select(whereclause=(and_(orders.c.volunteerId==volunteer.id, orders.c.completed==0)))).fetchall()
            if len(ordersList) < maxOrders:
                eligibleVolunteers.append(volunteer) 
        if len(eligibleVolunteers) > 0:
            toReturn.append(currentDay.strftime(strf))
        currentDay = currentDay + datetime.timedelta(days=1)

    return toReturn
