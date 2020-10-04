# Most of the code here isn't mine. I copy pasted it from https://developers.google.com/optimization/routing/vrp.
# It's under the Apache 2.0 license.
from __future__ import division
from __future__ import print_function
import json
import urllib.request
from ortools.constraint_solver import pywrapcp, routing_enums_pb2
from os import environ
from datetime import date, datetime, timedelta
import math
from flask import g
import geopy
from db import users, conn
from sqlalchemy import select, and_


def create_data(num_vehicles):

    '''
    with open("minerva/data.json", "r") as jsonFile:
        return json.load(jsonFile)
    '''

    data = {}

    data['API_key'] = environ['GOOGLE_API']
    print("Google api key: " + str(data['API_key']))
    data['users'] = conn.execute(
        users.select().where(users.c.role=="RECIEVER")).fetchall()

    data['num_vehicles'] = num_vehicles
    data['depot'] = 0
    data['users'].insert(0, g.user)

    data['vehicle_capacities'] = []
    maximumStops = len(data['users'])/data['num_vehicles'] + 5
    print("Maximum stops: " + str(maximumStops))
    #maximumStops = 500
    for vehicleNum in range(data['num_vehicles']):
        data['vehicle_capacities'].append(maximumStops)

    setCoords(data['API_key'])
    data['distance_matrix'] = create_distance_matrix(data)

    return data
# Haversine formula, gets distance in meeters between coords

def setCoords(API_key):
    print("Setting coordinates...")
    googleWrapper = geopy.geocoders.GoogleV3(api_key=API_key)
    userList = conn.execute(users.select()).fetchall()
    for user in userList:
        if not (user.latitude and user.longitude and user.formattedAddress):
            fullAddr = str(user['address']) + ", " + str(user['zipCode'])
            print("Fulladdr: " + fullAddr)
            coords = googleWrapper.geocode(query=fullAddr, timeout=100)
            if coords == None: # One of the zip codes in the spreadsheet is wrong
                coords = googleWrapper.geocode(query=user['address'] + " WA", timeout=100)
            print("Coords: " + str(coords))
            conn.execute(users.update().where(users.c.id==user.id).values(
                formattedAddress=coords[0],
                latitude=coords[1][0],
                longitude=coords[1][1]
            ))

def measure(lat1, lon1, lat2, lon2):
    # no idea how this works but stackoverflow does
    R = 6378.137  # radius of earth in KM
    dLat = lat2 * math.pi / 180 - lat1 * math.pi / 180
    dLon = lon2 * math.pi / 180 - lon1 * math.pi / 180
    a = math.sin(dLat/2) * math.sin(dLat/2) + \
        math.cos(lat1 * math.pi / 180) * math.cos(lat2 * math.pi / 180) * \
        math.sin(dLon/2) * math.sin(dLon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = R * c
    return d * 1000


def demand_callback(from_index):
    return 1

# returns array of user ID's
def getNextRoute(foodBankId):
    routeJson = conn.execute(
        select([users.c.routes]).where(users.c.id==foodBankId)
    ).fetchone()[0]
    routeList = json.loads(routeJson)
    print("List: " + str(routeList[0]))
    now = datetime.now()
    # wow tuples how pythonic
    maxRoute = ([], 0)
    for route in routeList:
        cost = getRouteCost(route, now)
        #print("Route: " + str(route))
        if cost > maxRoute[1]:
            maxRoute = (route, cost)
    return maxRoute[0]

# route is a list of user ID's, time is a datetime object (pass it datetime.now)
def getRouteCost(route, time):
    cost = 0
    for userId in route:
        lastDelivered = conn.execute(select([users.c.lastDelivered]).where(users.c.id==userId)).fetchone()
        print(lastDelivered)
        # Uncomment this line to fix the cold start problem
        #conn.execute(users.update().where(users.c.id==userId).values(lastDelivered=time))
        if lastDelivered == None or lastDelivered[0] == None:
            lastDelivered = time
        else:
            lastDelivered = lastDelivered[0]
        delta = (lastDelivered - time)
        print("Total seconds: " + str(delta.total_seconds()))
        cost += delta.total_seconds() ** 2
    return cost


def create_distance_matrix(data):
    distance_matrix = []
    print("Creating distance matrix...")
    for fromUser in data['users']:
        #print("From user: " + str(fromUser))
        #row_list = [row['elements'][j]['distance']['value'] for j in range(len(row['elements']))]
        row_list = []
        for toUser in data['users']:
            distance = measure(
                fromUser.latitude, fromUser.longitude, toUser.latitude, toUser.longitude)
            row_list.append(distance)
            if distance > 100000:
                print("Distance of " + str(distance) + " between " + fromUser.formattedAddress + " and " + toUser.formattedAddress)
        distance_matrix.append(row_list)
    print(len(distance_matrix))
    print(len(distance_matrix[0]))
    return distance_matrix

def get_solution(data, manager, routing, solution):
    """Prints solution on console."""
    print("Getting solution...")
    max_route_distance = 0
    toReturn = []
    for vehicle_id in range(data['num_vehicles']):
        toAppend = []
        index = routing.Start(vehicle_id)
        route_distance = 0
        while not routing.IsEnd(index):
            toAppend.append(data['users'][manager.IndexToNode(index)])
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            route_distance += routing.GetArcCostForVehicle(
                previous_index, index, vehicle_id)
        toAppend.append(data['users'][manager.IndexToNode(index)])
        toReturn.append(toAppend)
    return toReturn


def get_order_assignments(num_vehicles, data):

    """Solve the CVRP problem."""

    # Instantiate the data problem.

    #sdfdsfljk = spreadsheet[spreadsheet['Address 1'] != start_address]

    data = create_data(num_vehicles=40)

    #add_coords_to_df(spreadsheet, data)


    # Create the routing index manager.

    manager = pywrapcp.RoutingIndexManager(len(data['distance_matrix']), data['num_vehicles'], data['depot'])



    # Create Routing Model.

    routing = pywrapcp.RoutingModel(manager)





    # Create and register a transit callback.

    def distance_callback(from_index, to_index):

        """Returns the distance between the two nodes."""

        # Convert from routing variable Index to distance matrix NodeIndex.

        from_node = manager.IndexToNode(from_index)

        to_node = manager.IndexToNode(to_index)

        return data['distance_matrix'][from_node][to_node]



    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)


    # Define cost of each arc.

    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)



    # Add Distance constraint.

    dimension_name = 'Distance'

    routing.AddDimension(

        transit_callback_index,

        0,  # no slack

        90000,  # vehicle maximum travel distance

        True,  # start cumul to zero

        dimension_name)

    distance_dimension = routing.GetDimensionOrDie(dimension_name)

    distance_dimension.SetGlobalSpanCostCoefficient(100)

    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,
        data['vehicle_capacities'],
        True,
        'Capacity'
    )



    # Setting first solution heuristic.

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()

    search_parameters.first_solution_strategy = (

        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)



    # Solve the problem.

    solution = routing.SolveWithParameters(search_parameters)

    return get_solution(data, manager, routing, solution)

def createAllRoutes(foodBankId, num_vehicles=40):
    data = create_data(num_vehicles)
    usersList = conn.execute(users.select().where(
        users.c.role=="RECIEVER"
    )).fetchall()
    print("Calculating routes...")
    assignments = get_order_assignments(num_vehicles, data)
    route = []
    for i in range(len(assignments)):
        userIdList = []  # sorted list to store as column with volunteer
        for user in assignments[i]:
            userIdList.append(user['id'])
        route.append(userIdList)
    routeJson = json.dumps(route)
    conn.execute(users.update().where(users.c.id==g.user.id).values(routes=routeJson))



# assignAllOrders(2)
