import requests
from os import environ
from json import  loads
from db import users, conn
from sqlalchemy import select, and_

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
    if orderList == []:
        return []
    addresses = []
    for order in orderList:
        user = conn.execute(users.select().where(users.c.id==order.userId)).fetchone()
        addresses.append(user.address)
    print("Origin: " + origin)
    print("Dest: " + destination)
    print("waypoints: " + str(addresses))
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
