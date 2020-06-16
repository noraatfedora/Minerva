from sqlalchemy import select, and_
from db import conn, users, orders
from google_api import getOrdering
from json import dumps
from send_confirmation import send_bagged_notification

def assign(orderId, volunteerId):
    print("volunteer id: " + str(volunteerId))
    volunteer = conn.execute(users.select().where(users.c.id==volunteerId)).fetchone()
    foodBank = conn.execute(users.select().where(users.c.id==volunteer.foodBankId)).fetchone()
    conn.execute(orders.update().where(orders.c.id==orderId).values(volunteerId=volunteerId))
    assignedOrders = conn.execute(orders.select().where(and_(orders.c.volunteerId==volunteerId, orders.c.completed==0, orders.c.bagged==1))).fetchall()
    print("Assigned orders: " + str(assignedOrders))
    ordering = getOrdering(origin=foodBank.address, destination=volunteer.address, orderList=assignedOrders)
    conn.execute(users.update().where(users.c.id==volunteer.id).values(ordering=dumps(ordering)))

    # If it's already been bagged we send the email notification
    order = conn.execute(orders.select().where(orders.c.id==orderId)).fetchone()
    client = conn.execute(users.select().where(users.c.id==order.userId)).fetchone()
    if order.bagged == 1:
        send_bagged_notification(reciever_email=volunteer.email, orderId=orderId, address=client.address)

def unassign(orderId):
    order = conn.execute(orders.select().where(orders.c.id==orderId)).fetchone()
    print("Order: " + str(order))
    volunteer = conn.execute(users.select().where(users.c.id==order.volunteerId)).fetchone()
    print("volunteer: " + str(volunteer))
    if not volunteer == None:
        foodBank = conn.execute(users.select().where(users.c.id==volunteer.foodBankId)).fetchone()
        conn.execute(orders.update().where(orders.c.id==orderId).values(volunteerId=None))
        orderList = conn.execute(orders.select().where(orders.c.volunteerId==volunteer.id)).fetchall()
        ordering = getOrdering(origin=foodBank.address, destination=volunteer.address, orderList=orderList)

def bag(orderId):
    order = conn.execute(orders.select().where(orders.c.id==orderId)).fetchone()
    if (not order.bagged == 1):
        client = conn.execute(users.select().where(users.c.id==order.userId)).fetchone()
        volunteer = conn.execute(users.select().where(users.c.id==order.volunteerId)).fetchone()
        send_bagged_notification(reciever_email=volunteer.email, orderId=orderId, address=client.address)