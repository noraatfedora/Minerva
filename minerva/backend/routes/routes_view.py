from flask import ( Blueprint, flash, g, redirect, render_template,
    request, session, url_for, Flask, make_response, send_file
)
from werkzeug.exceptions import abort
from minerva.backend.routes.auth import login_required, admin_required 
from json import loads, dumps
from collections import OrderedDict
import pdfkit
from PyPDF2 import PdfFileMerger
from minerva.backend.apis.db import users, conn, routes
from sqlalchemy import and_, select
from os import environ
from minerva.backend.apis import assign
import io, datetime
from minerva.backend.apis import google_maps_qr
from datetime import datetime
import statistics
from minerva.backend.apis.email import send_recieved_notification, send_bagged_notification
bp = Blueprint('routes', __name__)

@login_required
@admin_required
@bp.route('/routes', methods=('GET', 'POST'))
def manageRoutes():
    #itemsList = conn.execute(items.select(items.c.foodBankId==g.user.foodBankId)).fetchall()
    print("Type: " + str(type(routes)))
    print("Attributes: " + str(dir(routes)))
    if request.method == "POST":
        print("Values: " + str(request.values.to_dict()))
    if request.method == "POST" and 'num_vehicles' in request.values.to_dict().keys():
        print(request.values.to_dict())
        separateCities = 'separate_cities' in request.values.keys()
        return loadingScreen(num_vehicles=int(request.values.get('num_vehicles')),
            global_span_cost=int(request.values.get('global_span_cost')),
            stop_conversion=int(request.values.get('stop_conversion')),
            solution_limit=int(request.values.get('solution_limit')),
            separate_cities=separateCities)
        '''
        if request.values['separateCities'] == 'None':
            print("Not separating cities")
            assign.createAllRoutes(foodBankId=g.user.id, num_vehicles=int(request.values.get('num-vehicles')),
                globalSpanCostCoefficient=int(request.values.get('global_span_cost')),
                stopConversion=int(request.values.get('stop_conversion')), solutionLimit=int(request.values.get('solution-limit')))
        else:
            print("Seperating cities")
            assign.createAllRoutesSeparatedCities(foodBankId=g.user.id, num_vehicles=int(request.values.get('num-vehicles')),
                globalSpanCostCoefficient=int(request.values.get('global_span_cost')),
                stopConversion=int(request.values.get('stop_conversion')), solutionLimit=int(request.values.get('solution-limit')))
        '''
    elif request.method == "POST" and 'move-user' in request.values.to_dict().keys():
        userId = int(request.values.to_dict()['move-user'])
        toRoute = int(request.values.to_dict()['to-route'])
        fromRoute = int(request.values.to_dict()['from-route'])
        print("Moving user " + str(userId) + " to route " + str(toRoute))
        assign.assignUserToRoute(toRoute, userId, fromRoute)
    elif request.method=="POST" and 'move-route' in request.values.to_dict().keys():
        toRoute = int(request.values.to_dict()['to-route'])
        fromRoute = int(request.values.to_dict()['move-route'])
        print("Moving route " + str(fromRoute) + " to " + str(toRoute))
        clients = loads(conn.execute(select([routes.c.content]).where(routes.c.id==fromRoute)).fetchone()[0])
        # remove food bank
        clients.remove(clients[0])
        clients.remove(clients[len(clients)-1])
        for client in clients:
            print("Removing client " + str(client))
            assign.assignUserToRoute(toRoute, client, fromRoute)
    elif request.method=="POST" and 'split-route' in request.values.to_dict().keys():
        routeId = int(request.values.to_dict()['split-route'])
        splitRoute(routeId)

    routeList = getRoutes()
    stats = getStats(routeList)

    return render_template("routes_view.html", routes=routeList, stats=stats)

@bp.route('/loading', methods=(['GET', 'POST']))
def loadingScreen(num_vehicles=100, global_span_cost=4000, stop_conversion=1000, solution_limit=10000, separate_cities=False):
    return render_template("loading.html", num_vehicles=num_vehicles, global_span_cost=global_span_cost, stop_conversion=stop_conversion, solution_limit=solution_limit, separate_cities=separate_cities, foodBankId=g.user.id, host=request.host)

@bp.route('/generate_new_routes')
def generate_new_routes():
    print("ASDFLIJSDJKLDSFJDSFKLJ")
    num_vehicles = int(request.values.get('num_vehicles'))
    global_span_cost = int(request.values.get('global_span_cost'))
    stop_conversion = int(request.values.get('stop_conversion'))
    solution_limit = int(request.values.get('solution_limit'))
    separate_cities = bool(request.values.get('separate_cities'))
    foodBankId = request.values.get('foodBankId')
    if separate_cities:
        assign.createAllRoutesSeparatedCities(g.user.id,
            num_vehicles=num_vehicles,
            stopConversion=stop_conversion,
            globalSpanCostCoefficient=global_span_cost,
            solutionLimit=solution_limit)
    else:
        assign.createAllRoutes(g.user.id,
            num_vehicles=num_vehicles,
            stopConversion=stop_conversion,
            globalSpanCostCoefficient=global_span_cost,
            solutionLimit=solution_limit)
    return redirect('/routes')

@bp.route('/loading_status/<int:foodBankId>', methods=(['GET', 'POST']))
def loading_status(foodBankId):
    status = conn.execute(select([users.c.doneCalculating]).where(users.c.id==foodBankId)).fetchone()[0]
    return str(status)


@bp.route('/route_link/<query>')
def google_maps_redirect(query):
    splitQuery = query.split('-')
    userIdList=splitQuery[0].split('+')
    api_key = splitQuery[1]
    foodBank = conn.execute(users.select().where(users.c.apiKey==api_key)).fetchall()
    if foodBank == None:
        return "Sorry, that URL contains an invalid API key."
    userList = []
    for id in userIdList:
        userList.append(conn.execute(users.select().where(users.c.id==id)).fetchone())
    return redirect(google_maps_qr.make_url(userList))

def getStats(routeList):
    if len(routeList) == 0:
        return {}
    stats = {}
    clientNumberList = []
    distanceList = []

    for route in routeList:
        clientNumberList.append(len(route['userList']))
        distanceList.append(float(route['length']))
    
    stats['numRoutes'] = len(routeList)
    stats['meanClients'] = round(statistics.mean(clientNumberList), 2)
    stats['stdevClients'] = round(statistics.pstdev(clientNumberList), 2)
    stats['maxClients'] = max(clientNumberList)
    stats['minClients'] = min(clientNumberList)
    stats['meanDist'] = round(statistics.mean(distanceList), 2)
    stats['stdevDist'] = round(statistics.pstdev(clientNumberList), 2)
    stats['sumDist'] = sum(clientNumberList)
    stats['maxDist'] = max(distanceList)
    stats['minDist'] = min(distanceList)
    
    return stats

def getRoutes():
    row2dict = lambda r: {c.name: str(getattr(r, c.name)) for c in routes.columns}
    rp = conn.execute(routes.select().where(routes.c.foodBankId==g.user.id)).fetchall()
    if len(rp) == 0:
        return []
    scoreAverage = 0
    toReturn = []
    for route_rp in rp:
        routeDict = row2dict(route_rp)
        routeDict['userList'] = getUsers(route_rp.id)
        routeDict['google_maps'] = google_maps_qr.make_url(routeDict['userList'])
        routeDict['parsedContent'] = loads(route_rp.content)
        score = assign.getRouteCost(routeDict['parsedContent'], datetime.now())
        scoreAverage += score
        routeDict['score'] = score
        routeDict['osm'] = google_maps_qr.osm_url(routeDict['userList'])
        toReturn.append(routeDict)
    scoreAverage = scoreAverage / len(rp)

    for routeDict in toReturn:
        if scoreAverage == 0:
            scoreAverage = 1
        routeDict['weightedScore'] = round(10 * routeDict['score'] / scoreAverage, 2)
    return toReturn

# Returns a list of users based off the given route ID
def getUsers(routeId):
    print("Route ID:" + str(routeId))
    row2dict = lambda r: {c.name: str(getattr(r, c.name)) for c in users.columns}
    # Get the ID's that our volunteer is assigned to
    route_rp = conn.execute(routes.select().where(routes.c.id==routeId)).fetchone()
    content = loads(route_rp.content)
    toReturn = []
    for userId in content:
        #if userId != g.user.foodBankId: # Stupid to put the food bank on the user's list of orders
        user_rp = conn.execute(users.select().where(users.c.id==userId)).fetchone()
        if user_rp == None:
            continue
        userObj = row2dict(user_rp)
        if user_rp['lastDelivered']:
            userObj['doneToday'] = user_rp['lastDelivered'].date() == datetime.today().date()
        else:
            userObj['doneToday'] = False
        toReturn.append(userObj)

    return toReturn

@login_required
@admin_required
@bp.route('/driver_printout/<int:routeId>')
def driver_printout(routeId):
    print("getting driver printout")
    route = {}
    route['usersList'] = getUsers(routeId)
    
    # Generate QR codes for each user
    for user in route['usersList']:
        qr_data = google_maps_qr.make_user_qr(user['formattedAddress'])
        user['qr_data'] = qr_data

    route['qr'] = google_maps_qr.make_qr_code(route['usersList'], g.user.apiKey)
    route['headerText'] = "Route " + str(routeId)
    route['length'] = conn.execute(select([routes.c.length]).where(routes.c.id==routeId)).fetchone()[0] / 1000.0

    html = render_template("driver_printout.html", routes=[route])

    options = {
        'orientation': 'Landscape',
        'margin-top': '0',
        'margin-bottom': '0'
    }
    pdf = pdfkit.from_string(html, False, options=options)

    response = make_response(pdf)
    response.headers['Content-type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline;'

    #return html
    return response

@login_required
@admin_required
@bp.route('/driver_printout/all')
def master_driver_printout():
    print("ID" + str(g.user.id))
    routesList = conn.execute(routes.select().where(routes.c.foodBankId==g.user.id)).fetchall()
    routeDictList = []
    count = 0
    for route in routesList:
        routeDict = {}
        routeDict['usersList'] = getUsers(route.id)
        for user in routeDict['usersList']:
            qr_data = google_maps_qr.make_user_qr(user['formattedAddress'])
            user['qr_data'] = qr_data
        routeDict['qr'] = google_maps_qr.make_qr_code(routeDict['usersList'], g.user.apiKey)
        routeDict['headerText'] = "Route " + str(count) #+ "(ID: " + str(route['id']) + ")"
        routeDict['length'] = route['length'] / 1000
        count += 1
        routeDictList.append(routeDict)

    options = {
        'header-right': '[page]/[toPage]',
        'orientation': 'Landscape',
        'margin-top': '0',
        'margin-bottom': '0'
    }
    html = render_template("driver_printout.html", routes=routeDictList)
    pdf = pdfkit.from_string(html, False, options=options)
    response = make_response(pdf )
    response.headers['Content-type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline;'

    return response

def splitRoute(routeId):
    oldRoute = loads(conn.execute(select([routes.c.content]).where(routes.c.id==routeId)).fetchone()[0])
    print("Old route: " + str(oldRoute))
    newRouteRight = getUsersFromIdList([g.user.id] + oldRoute[int(len(oldRoute)/2):])
    newRouteLeft = getUsersFromIdList(oldRoute[:int(len(oldRoute)/2)] + [g.user.id])
    leftDistance = calculateLength(newRouteLeft)
    rightDistance = calculateLength(newRouteRight)
    if leftDistance > rightDistance:
        while leftDistance > rightDistance and len(newRouteLeft) > 2:
            newRouteRight.insert(1, newRouteLeft[len(newRouteLeft) - 2])
            newRouteLeft.remove(newRouteLeft[len(newRouteLeft) - 2])
            leftDistance = calculateLength(newRouteLeft)
            rightDistance = calculateLength(newRouteRight)
    else:
        while rightDistance > leftDistance and len(newRouteRight) > 2:
            newRouteLeft.insert(len(newRouteLeft)-2, newRouteRight[1])
            newRouteRight.remove(newRouteRight[1])
            leftDistance = calculateLength(newRouteLeft)
            rightDistance = calculateLength(newRouteRight)
    leftContents = getIdList(newRouteLeft)
    rightContents = getIdList(newRouteRight)
    print("Left: " + str(leftContents)) 
    print("Right: " + str(rightContents)) 
    print("Left distance: " + str(leftDistance))
    print("Right distance: " + str(rightDistance))

    conn.execute(routes.insert().values(content=dumps(leftContents), length=leftDistance, foodBankId=g.user.id))
    conn.execute(routes.insert().values(content=dumps(rightContents), length=rightDistance, foodBankId=g.user.id))
    conn.execute(routes.delete().where(routes.c.id==routeId))

def getUsersFromIdList(contents):
    toReturn = []
    for id in contents:
        user = conn.execute(users.select().where(users.c.id==id)).fetchone()
        toReturn.append(user)
    return toReturn

def calculateLength(route): # requres list of user objects, like from getUsersFromIdList()
    distance = 0
    for i in range(0, len(route) - 1):
        userFrom = route[i]
        userTo = route[i+1]
        distance += assign.measure(userFrom.latitude, userFrom.longitude, userTo.latitude, userTo.longitude)
    return distance

def getIdList(route): # also takes user objects
    toReturn = []
    for user in route:
        toReturn.append(user.id)
    return toReturn
