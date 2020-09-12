# Most of the code here isn't mine. I copy pasted it from https://developers.google.com/optimization/routing/vrp.
# It's under the Apache 2.0 license.
from __future__ import division
from __future__ import print_function
import json
import urllib.request
from ortools.constraint_solver import pywrapcp, routing_enums_pb2
from os import environ
from datetime import date
import math
from db import orders, users, conn
from sqlalchemy import select, and_


def create_data(num_vehicles):
    data = {}

    data['API_key'] = environ['GOOGLE_API']
    data['addresses'] = conn.execute(
        select([users.c.formattedAddress])).fetchAll()

    data['num_vehicles'] = num_vehicles
    data['depot'] = 0
    data['addresses'].insert(0, g.user.formattedAddress)

    data['vehicle_capacities'] = []
    maximumStops = len(data['addresses'])/data['num_vehicles'] + 2
    for vehicleNum in range(data['num_vehicles']):
        data['vehicle_capacities'].append(maximumStops)

    return data
# Haversine formula, gets distance in meeters between coords


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


def create_distance_matrix(data):
    distance_matrix = []
    userList = conn.execute(users.select()).fetchall()
    for fromUser in userList:
        #row_list = [row['elements'][j]['distance']['value'] for j in range(len(row['elements']))]
        row_list = []
        for toUser in userList:
            row_list.append(measure(
                fromUser.latitude, fromUser.longitude, toUser.latitude, toUser.longitude))

        distance_matrix.append(row_list)

    return distance_matrix

def get_solution(data, manager, routing, solution):
    """Prints solution on console."""
    max_route_distance = 0
    toReturn = []
    for vehicle_id in range(data['num_vehicles']):
        toAppend = []
        index = routing.Start(vehicle_id)
        route_distance = 0
        while not routing.IsEnd(index):
            toAppend.append(data['addresses'][manager.IndexToNode(index)])
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            route_distance += routing.GetArcCostForVehicle(
                previous_index, index, vehicle_id)
        toAppend.append(data['addresses'][manager.IndexToNode(index)])
        toReturn.append(toAppend)
    return toReturn


def get_order_assignments(num_vehicles):
    """Solve the CVRP problem."""
    # Instantiate the data problem.
    data = create_data(num_vehicles)

    # Create the routing index manager.
    manager = pywrapcp.RoutingIndexManager(len(data['distance_matrix']),
                                           data['num_vehicles'], data['depot'])

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
    demand_callback_index = routing.RegisterTransitCallback(demand_callback)

    # Define cost of each arc.
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Add Distance constraint.
    dimension_name = 'Distance'
    routing.AddDimension(
        transit_callback_index,
        0,  # no slack
        7000,  # vehicle maximum travel distance
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

def createAllRoutes(foodBankId=g.user.id, num_vehicles=40):
    '''
    addresses = ['3610+Hacks+Cross+Rd+Memphis+TN', # depot
                     '1921 Elvis+Presley Blvd Memphis TN',
                     '149+Union+Avenue+Memphis+TN',
                     '1034+Audubon+Drive+Memphis+TN',
                     '1532+Madison+Ave+Memphis+TN',
                     '706+Union+Ave+Memphis+TN',
                     '3641+Central+Ave+Memphis+TN',
                     '926+E+McLemore+Ave+Memphis+TN',
                     '4339+Park+Ave+Memphis+TN',
                     '600+Goodwyn+St+Memphis+TN',
                     '2000+North+Pkwy+Memphis+TN',
                     '262+Danny+Thomas+Pl+Memphis+TN',
                     '125+N+Front+St+Memphis+TN',
                     '5959+Park+Ave+Memphis+TN',
                     '814+Scott+St+Memphis+TN',
                     '1005+Tillman+St+Memphis+TN'
                    ]
    '''
    usersList = conn.execute(users.select().where(
        users.c.role=="RECIEVER"
    )).fetchall()
    volunteersList = conn.execute(users.select().where(and_(users.c.role == "VOLUNTEER", users.c.approved ==
                                                            True, users.c.foodBankId == foodBankId, users.c.checkedIn == date.today()))).fetchall()
    assignments = get_order_assignments(num_vehicles)
    route = []
    for i in range(len(assignments)):
        volunteer = volunteersList[i]
        orderIdList = []  # sorted list to store as column with volunteer
        for addr in assignments[i]:
            addr = addr.replace('+', ' ')
            userId = conn.execute(select([users.c.id]).where(
                users.c.address == addr)).fetchone()[0]
            orderId = conn.execute(select([orders.c.id]).where(and_(
                orders.c.userId == userId, orders.c.completed == 0, orders.c.bagged == 1))).fetchone()[0]
            print("Order id:" + str(orderId))
            conn.execute(orders.update().where(
                orders.c.id == orderId).values(volunteerId=volunteer.id))
            orderIdList.append(orderId)
        print("Order id list: " + str(orderIdList))
        route.append(orderIdList)
    print("Volunteers: " + str(volunteersList))
    routeJson = json.dumps(route)
    conn.execute(users.update().where(users.c.id==g.user.id).values(routes=routeJson))



# assignAllOrders(2)
