import requests
from os import environ
from json import  loads
<<<<<<< HEAD
from db import users, orders, conn
from sqlalchemy import select
=======
from db import users, orders
from sqlalchemy import conn
>>>>>>> 157b92d43fa15f283b8c59ddf51ff19f62a44476
import set_environment_variables

def matrix(origins, destinations):
    # Example URL:
    #https://maps.googleapis.com/maps/api/distancematrix/json?origins=Boston,MA|Charlestown,MA&destinations=Lexington,MA|Concord,MA&departure_time=now&key=YOUR_API_KEY
    requestString = ("https://maps.googleapis.com/maps/api/distancematrix/json?origins="
        + addAdresses(origins)
        + "&destinations="
        + addAdresses(destinations)
        + "&departure_time=now"
        + "&key="
        + environ['GOOGLE_API']
    )

    return loads(requests.get(requestString).content)

def directions(origin, destination, waypoints):
    requestString = ("https://maps.googleapis.com/maps/api/directions/json?origin="
        + origin
        + "&destination="
        + destination
        + "&waypoints=optimize:true"
        + addAdresses(waypoints)
        + "&key="
        + environ['GOOGLE_API'])
    return loads(requests.get(requestString).content)

# Returns a sorted list of the order ID's
def getOrdering(origin, destination, orderList):
    addresses = []
    for order in orderList:
        user = conn.execute(users.select().where(users.c.id==order.userId)).fetchone()
        addresses.append(user.address)
    response = directions(origin, destination, addresses)
    waypoint_order = response['routes'][0]['waypoint_order']
    toReturn = []
    for index in waypoint_order:
        toReturn.append(orderList[index].id)
    return toReturn

def addAdresses(addresses):
    toReturn = ''
    for address in addresses:
        # security
        address.replace('&', '')
        address.replace('|', '')
        
        toReturn += "|" + address
    return toReturn
