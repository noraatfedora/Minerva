# Most of the code here isn't mine. I copy pasted it from https://developers.google.com/optimization/routing/vrp.
# It's under the Apache 2.0 license.
from __future__ import division
from __future__ import print_function
import requests
import json
import urllib.request
from ortools.constraint_solver import pywrapcp, routing_enums_pb2
from os import environ
import set_environment_variables
from db import orders, users, conn
from sqlalchemy import select, and_

def create_distance_matrix(data):
    addresses = data["addresses"]
    API_key = data["API_key"]
    # Distance Matrix API only accepts 100 elements per request, so get rows in multiple requests.
    max_elements = 100
    num_addresses = len(addresses)  # 16 in this example.
    # Maximum number of rows that can be computed per request (6 in this example).
    max_rows = max_elements // num_addresses
    # num_addresses = q * max_rows + r (q = 2 and r = 4 in this example).
    q, r = divmod(num_addresses, max_rows)
    dest_addresses = addresses
    distance_matrix = []
    # Send q requests, returning max_rows rows per request.
    for i in range(q):
        origin_addresses = addresses[i * max_rows: (i + 1) * max_rows]

    # Get the remaining remaining r rows, if necessary.
    if r > 0:
        origin_addresses = addresses[q * max_rows: q * max_rows + r]
        response = send_request(origin_addresses, dest_addresses, API_key)
        distance_matrix += build_distance_matrix(response)
    return distance_matrix


def send_request(origin_addresses, dest_addresses, API_key):
    """ Build and send request for the given origin and destination addresses."""
    def build_address_str(addresses):
        # Build a pipe-separated string of addresses
        address_str = ''
        for i in range(len(addresses) - 1):
            address_str += addresses[i].replace(' ', '+') + '|'
        address_str += addresses[-1]
        return address_str

    request = 'https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial'
    origin_address_str = build_address_str(origin_addresses)
    dest_address_str = build_address_str(dest_addresses)
    request = request + '&origins=' + origin_address_str + '&destinations=' + \
        dest_address_str + '&key=' + API_key
    jsonResult = urllib.request.urlopen(request).read()
    response = json.loads(jsonResult)
    return response



def build_distance_matrix(response):
    distance_matrix = []
    for row in response['rows']:
        row_list = [row['elements'][j]['duration']['value']
                    for j in range(len(row['elements']))]
        distance_matrix.append(row_list)
    return distance_matrix

# Returns a 2D array of addresses
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

def get_order_assignments(orders, num_vehicles, foodBankAddress):
    """Solve the CVRP problem."""
    # Instantiate the data problem.
    data = {}
    data['addresses'] = []
    for order in orders:
        data['addresses'].append(conn.execute(select([users.c.address]).where(users.c.id==order.userId)).fetchone()[0].replace(' ', '+'))
    data['API_key'] = environ['GOOGLE_API']
    data['distance_matrix'] = create_distance_matrix(data)
    data['depot'] = 0
    data['num_vehicles'] = num_vehicles

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

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

    # Solve the problem.
    solution = routing.SolveWithParameters(search_parameters)

    return get_solution(data, manager, routing, solution)

# this is the one
def assignAllOrders(foodBankId):
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
    ordersList = conn.execute(orders.select().where(and_(orders.c.bagged==1, orders.c.completed==0))).fetchall()
    volunteersList = conn.execute(users.select().where(and_(users.c.role=="VOLUNTEER", users.c.approved==True, users.c.foodBankId==foodBankId))).fetchall()
    foodBankAddr = conn.execute(select([users.c.address]).where(users.c.id==foodBankId)).fetchone()[0]
    assignments = get_order_assignments(ordersList, len(volunteersList), foodBankAddr)
    for i in len(assignments):
        volunteer = volunteersList[i]
        for addr in assignments[i]:
            conn.execute(orders.update().values(volunteerId=volunteer.id))

