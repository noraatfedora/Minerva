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
import pandas as pd
import geopy
from json import loads, dumps
from minerva.backend.apis.db import users, conn, routes
from sqlalchemy import select, and_


def create_data(num_vehicles, gscce, stopConversion):

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
    data['globalSpanCostCoefficient'] = gscce
    data['stopConversion'] = stopConversion

    data['depot'] = 0
    data['users'].insert(0, g.user)

    data['vehicle_capacities'] = []
    maximumStops = len(data['users'])/data['num_vehicles'] + 3
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
            print("Name: " + str(user['name']))
            print("Original address: " + str(user['address']))
            print("Coords: " + str(coords))
            conn.execute(users.update().where(users.c.id==user.id).values(
                formattedAddress=coords[0],
                latitude=coords[1][0],
                longitude=coords[1][1]
            ))

def measure(lat1, lon1, lat2, lon2):
    lat1 = float(lat1)
    lat2 = float(lat2)
    lon1 = float(lon1)
    lon2 = float(lon2)
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
def getNextRoute(volunteerId, foodBankId):
    oldId = conn.execute(select([routes.c.id]).where(routes.c.volunteerId== volunteerId)).fetchone()
    routeList = conn.execute(routes.select().where(and_(routes.c.foodBankId==foodBankId, routes.c.volunteerId==-1))).fetchall()
    now = datetime.now()
    # wow tuples how pythonic
    maxRoute = (-1, -1) # ID, cost
    for route in routeList:
        cost = getRouteCost(json.loads(route.content), now)
        #print("Cost: " + str(cost))
        #print("Route: " + str(route))
        if cost > maxRoute[1]:
            maxRoute = (route.id, cost)
    print("updating to route " + str(maxRoute[0]))
    conn.execute(routes.update().where(routes.c.id==maxRoute[0]).values(volunteerId=volunteerId))
    if oldId != None:
        conn.execute(routes.update().where(routes.c.id==oldId[0]).values(volunteerId=-1))
    return maxRoute[0]

# route is a list of user ID's, time is a datetime object (pass it datetime.now)
def getRouteCost(route, time):
    cost = 0
    for userId in route:
        if userId == g.user.id or userId == g.user.foodBankId:
            continue
        lastDelivered = conn.execute(select([users.c.lastDelivered]).where(users.c.id==userId)).fetchone()
        #print(lastDelivered)
        # Uncomment this line to fix the cold start problem
        #conn.execute(users.update().where(users.c.id==userId).values(lastDelivered=time))
        if lastDelivered == None or lastDelivered[0] == None:
            lastDelivered = time
        else:
            lastDelivered = lastDelivered[0]
        delta = (lastDelivered - time)
        #print("Total seconds: " + str(delta.total_seconds()))
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
            #print("From " + str(fromUser.name) + " to " + str(toUser.name))
            distance = measure(
                fromUser.latitude, fromUser.longitude, toUser.latitude, toUser.longitude)
            row_list.append(distance)
            if distance > 50000:
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
        combined = [[], 0]
        index = routing.Start(vehicle_id)
        route_distance = 0
        while not routing.IsEnd(index):
            combined[0].append(data['users'][manager.IndexToNode(index)])
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            route_distance += routing.GetArcCostForVehicle(
                previous_index, index, vehicle_id) - data['stopConversion']
        combined[0].append(data['users'][manager.IndexToNode(index)])
        combined[1] = route_distance
        toReturn.append(combined)
    return toReturn


def get_order_assignments(num_vehicles, data, stopConversion, globalSpanCostCoefficient, defaultRoutes=None, warpSpeed=False):

    """Solve the CVRP problem."""

    # Instantiate the data problem.

    #sdfdsfljk = spreadsheet[spreadsheet['Address 1'] != start_address]

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

        return data['distance_matrix'][from_node][to_node] + data['stopConversion']



    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)


    # Define cost of each arc.

    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)



    # Add Distance constraint.

    dimension_name = 'Distance'

    routing.AddDimension(

        transit_callback_index,

        0,  # no slack

        45000,  # vehicle maximum travel distance

        True,  # start cumul to zero

        dimension_name)

    distance_dimension = routing.GetDimensionOrDie(dimension_name)

    # Default should be around 4000
    distance_dimension.SetGlobalSpanCostCoefficient(data['globalSpanCostCoefficient'])

    #distance_dimension.SetSpanCostCoefficientForAllVehicles(10000)
    #distance_dimension.SetCumulVarSoftLowerBound(transit_callback_index, 10000, 100000000)
    #distance_dimension.SetCumulVarSoftUpperBound(transit_callback_index, 20000, 100000000)

    '''
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,
        data['vehicle_capacities'],
        True,
        'Capacity'
    )
    '''


    # Setting first solution heuristic.

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()

    if warpSpeed:
        search_parameters.solution_limit = 1
        print("Warp speed go brrr")

    search_parameters.first_solution_strategy = (

        routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION)


    # Solve the problem.
    initial_solution = routing.ReadAssignmentFromRoutes(defaultRoutes, True)
    if initial_solution != None:
        print("Initial solution:" + str(initial_solution))
        print(type(initial_solution))
        solution = routing.SolveWithParameters(initial_solution, search_parameters)
    else:
        solution = routing.SolveWithParameters(search_parameters)

    return get_solution(data, manager, routing, solution)

def createAllRoutes(foodBankId, num_vehicles=100, stopConversion=1000, globalSpanCostCoefficient=4000, warpSpeed=False):
    print("Number of vehicles: " + str(num_vehicles))
    #routeList = [[2, 114, 264, 454, 327, 405, 137, 144, 474, 333, 229, 456, 321, 128, 216, 59, 178, 2], [2, 207, 19, 407, 147, 256, 159, 162, 208, 226, 233, 426, 65, 97, 244, 261, 205, 2], [2, 2], [2, 67, 54, 379, 290, 484, 53, 422, 113, 259, 357, 373, 72, 268, 439, 32, 491, 2], [2, 2], [2, 319, 110, 429, 461, 265, 496, 112, 196, 306, 184, 223, 73, 432, 352, 427, 2], [2, 170, 483, 466, 478, 402, 120, 366, 325, 14, 160, 41, 221, 359, 250, 451, 117, 2], [2, 2], [2, 2], [2, 413, 75, 328, 384, 86, 236, 382, 386, 311, 145, 436, 192, 279, 218, 371, 294, 2], [2, 2], [2, 476, 198, 18, 376, 37, 421, 377, 324, 182, 142, 455, 314, 135, 133, 181, 166, 2], [2, 392, 358, 83, 475, 187, 11, 431, 46, 287, 109, 237, 430, 16, 411, 497, 2], [2, 353, 156, 68, 81, 344, 343, 85, 445, 390, 313, 447, 401, 469, 355, 155, 275, 2], [2, 416, 43, 202, 100, 249, 316, 354, 485, 305, 462, 22, 394, 477, 89, 60, 138, 2], [2, 406, 200, 481, 317, 124, 271, 492, 235, 482, 273, 246, 212, 161, 152, 98, 301, 2], [2, 408, 149, 365, 220, 225, 136, 468, 228, 154, 26, 87, 312, 172, 381, 277, 410, 2], [2, 24, 336, 397, 42, 121, 267, 38, 52, 39, 307, 163, 254, 260, 171, 320, 393, 2], [2, 443, 219, 460, 280, 12, 148, 418, 95, 241, 472, 21, 435, 335, 168, 23, 104, 2], [2, 91, 186, 134, 173, 276, 295, 299, 349, 378, 310, 82, 115, 334, 340, 158, 193, 2], [2, 63, 346, 467, 369, 195, 243, 58, 404, 329, 197, 270, 464, 288, 2], [2, 213, 169, 175, 350, 361, 217, 179, 118, 27, 201, 274, 131, 177, 165, 126, 36, 2], [2, 92, 209, 248, 238, 490, 440, 428, 423, 420, 412, 370, 341, 283, 50, 130, 356, 2], [2, 106, 141, 266, 47, 206, 232, 143, 389, 459, 13, 380, 94, 293, 318, 326, 194, 2], [2, 227, 479, 330, 29, 364, 296, 342, 372, 69, 214, 257, 398, 102, 96, 286, 486, 2], [2, 2], [2, 493, 132, 444, 80, 111, 77, 425, 190, 323, 167, 203, 119, 176, 40, 400, 140, 2], [2, 239, 363, 230, 450, 442, 298, 247, 494, 231, 189, 446, 234, 285, 64, 488, 269, 2], [2, 183, 84, 463, 368, 292, 93, 116, 403, 304, 272, 51, 453, 174, 433, 419, 2], [2, 2], [2, 281, 284, 291, 108, 282, 78, 458, 331, 424, 332, 57, 415, 17, 452, 473, 258, 2], [2, 180, 123, 337, 263, 127, 204, 125, 99, 252, 79, 414, 278, 211, 30, 387, 367, 2], [2, 351, 224, 395, 480, 300, 48, 15, 157, 90, 103, 245, 347, 471, 215, 66, 251, 2], [2, 146, 441, 242, 345, 139, 45, 240, 437, 495, 385, 315, 338, 107, 457, 35, 188, 2], [2, 44, 49, 210, 191, 129, 465, 302, 489, 28, 374, 308, 222, 88, 2], [2, 62, 399, 417, 438, 61, 74, 164, 262, 255, 34, 388, 150, 375, 322, 348, 55, 2], [2, 105, 185, 56, 76, 309, 449, 122, 434, 487, 391, 448, 362, 71, 396, 383, 253, 2], [2, 101, 199, 409, 339, 151, 31, 303, 70, 153, 297, 25, 360, 470, 20, 33, 289, 2], [2, 2], [2, 2]]
    print(environ['INSTANCE_PATH'])
    data = create_data(num_vehicles, globalSpanCostCoefficient, stopConversion)
    usersList = conn.execute(users.select().where(
        users.c.role=="RECIEVER"
    )).fetchall()
    missingClientsRaw = conn.execute(select([users.c.id]).where(users.c.foodBankId==g.user.id and users.c.role=="RECIEVER")).fetchall()
    missingClients = []
    for client in missingClientsRaw:
        missingClients.append(client[0])
    print(missingClients)
    currentRoutesRaw = conn.execute(routes.select().where(routes.c.foodBankId==g.user.id)).fetchall()
    currentRoutes = []
    for route in currentRoutesRaw:
        routeContent = loads(route.content)
        badStuffRemoved = []
        for userId in routeContent:
            if userId in missingClients:
                badStuffRemoved.append(userId)
        currentRoutes.append(badStuffRemoved)
    #currentRoutes.append(missingClients)
    #TODO: Figure out if stuff was necessary


    # Add anyone missing

    print("Calculating routes...")
    print("Current routes: " + str(currentRoutes))
    assignments = get_order_assignments(num_vehicles, data, stopConversion, globalSpanCostCoefficient, currentRoutes, warpSpeed)
    routeList = []
    for i in range(len(assignments)):
        userIdList = []  # sorted list to store as column with volunteer
        for user in assignments[i][0]:
            userIdList.append(user['id'])
        routeList.append(userIdList)
    conn.execute(routes.delete().where(routes.c.foodBankId==foodBankId))
    for routeNum in range(len(routeList)):
        route = routeList[routeNum]
        length = assignments[routeNum][1]
        print("Route: " + str(route))
        if len(route) == 2:
            continue
        conn.execute(routes.insert().values(foodBankId=foodBankId, length=length, content=json.dumps(route), volunteerId=-1))
    routesToSpreadsheet(foodBankId)

def routesToSpreadsheet(foodBankId):
    routesList = conn.execute(routes.select().where(routes.c.foodBankId==foodBankId))
    pdList = []
    for route in routesList:
        df = pd.DataFrame(getUsers(route.id, addOriginal=True))
        pdList.append(df)

    fileName = environ['INSTANCE_PATH'] + 'routes.xlsx'
    writer = pd.ExcelWriter(fileName)

    for index in range(0, len(pdList)):
        pdList[index].to_excel(writer, sheet_name="Route " + str(index))

    writer.save()

    return fileName


# Returns a list of users based off the given route ID
def getUsers(routeId, addOriginal=False, columns = [users.c.name, users.c.email,
        users.c.cellPhone, users.c.instructions,
        users.c.address,
        users.c.formattedAddress,
        users.c.address2,
        users.c.householdSize]):
    print("Route ID:" + str(routeId))
    prettyNames = {'formattedAddress': 'Full Address',
                    'address2': 'Apt',
                    'address': 'Original Ajddress',
                    'name': 'Name',
                    'email':'Email',
                    'cellPhone': 'Phone',
                    'instructions': 'Notes',
                    'householdSize': 'Household Size',
                    'id': 'id',
                    'latitude': 'latitude',
                    'longitude': 'longitude'}
    row2dict = lambda r: {prettyNames[c.name]: betterStr(getattr(r, c.name)) for c in columns}
    # Get the ID's that our volunteer is assigned to
    route_rp = conn.execute(routes.select().where(routes.c.id==routeId)).fetchone()
    content = loads(route_rp.content)
    toReturn = []
    for userId in content:
        if userId != g.user.id: # Stupid to put the food bank on the user's list of orders
            user_rp = conn.execute(users.select().where(users.c.id==userId)).fetchone()
            userObj = row2dict(user_rp)
            toReturn.append(userObj)

    print("Users: " + str(toReturn))
    return toReturn
def betterStr(value):
    if value == None:
        return ''
    else:
        return str(value)
    
def assignUserToRoute(toRoute, userId, fromRoute):
    # Remove from original route first
    idArr = json.loads(conn.execute(select([routes.c.content]).where(routes.c.id==fromRoute)).fetchone()[0])
    idArr.remove(userId)
    conn.execute(routes.update().where(routes.c.id==fromRoute).values(content=json.dumps(idArr)))
    routeContent = getUsers(toRoute, columns=[users.c.id, users.c.latitude, users.c.longitude])
    userToInsert = conn.execute(users.select().where(users.c.id==userId)).fetchone()
    minIndex = 0
    minDistance = 999999
    for i in range(0, len(routeContent)-1):
        userFrom = routeContent[i]
        print("At user " + str(userFrom))
        userTo = routeContent[i+1]
        distanceLeft = measure(userFrom['latitude'], userFrom['longitude'], userToInsert['latitude'], userToInsert['longitude'])
        distanceRight = measure(userToInsert['latitude'], userToInsert['longitude'], userTo['latitude'], userTo['longitude'])
        distance = distanceLeft + distanceRight
        print("Distance at index " + str(i) + ": " + str(distance))
        if distance < minDistance:
            minIndex = i
            minDistance = distance
    print("Inserting to index " + str(minIndex) + " with distance " + str(minDistance))
    idArr = json.loads(conn.execute(select([routes.c.content]).where(routes.c.id==toRoute)).fetchone()[0])
    idArr.insert(minIndex+1, userId)
    conn.execute(routes.update().where(routes.c.id==toRoute).values(content=json.dumps(idArr)))

