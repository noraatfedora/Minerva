import requests
from json import  loads

def matrix(origins, destinations):
    # Example URL:
    #https://maps.googleapis.com/maps/api/distancematrix/json?origins=Boston,MA|Charlestown,MA&destinations=Lexington,MA|Concord,MA&departure_time=now&key=YOUR_API_KEY
    requestString = ("https://maps.googleapis.com/maps/api/distancematrix/json?origins="
        + addAdresses(origins)
        + "&destinations="
        + addAdresses(destinations)
        + "&departure_time=now"
        + "&key="
        + open('GOOGLE_API_KEY', 'r').read())

    return loads(requests.get(requestString).content)

def directions(origin, destination, waypoints):
    requestString = ("https://maps.googleapis.com/maps/api/directions/json?origin="
        + origin
        + "&destination="
        + destination
        + "&waypoints=optimize:true"
        + addAdresses(waypoints)
        + "&key="
        + open('GOOGLE_API_KEY', 'r').read())
    return loads(requests.get(requestString).content)

def addAdresses(addresses):
    toReturn = ''
    for address in addresses:
        # security
        address.replace('&', '')
        address.replace('|', '')
        
        toReturn += address + "|" 

    # Remove the last '|'
    return toReturn[:-1]

