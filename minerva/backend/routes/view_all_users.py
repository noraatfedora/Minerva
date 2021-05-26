from flask import ( Blueprint, flash, g, redirect, render_template,
    request, session, url_for, Flask, make_response, send_file
)
from werkzeug.exceptions import abort
from minerva.backend.routes.auth import login_required, admin_required
import usaddress
from json import loads, dumps
from collections import OrderedDict
from minerva.backend.apis import google_maps_qr
from minerva.backend.apis.assign import getUsers
from minerva.backend.apis.db import users, conn, items, routes
from sqlalchemy import and_, select, desc
import pandas as pd
from os import environ
from barcode import Code128
from openpyxl import load_workbook, styles
from barcode.writer import ImageWriter
from minerva.backend.apis import assign, order_assignment
import io, pdfkit, base64, qrcode, datetime
from fuzzywuzzy import fuzz
from minerva.backend.apis.email import send_recieved_notification, send_bagged_notification
bp = Blueprint('view_all_users', __name__)

class Duplicate:
    # Generates a color for these cards
    # by setting the hue to a hash of the user ID's
    def generate_hue(self):
        return hash(sum(self.userIds)) % 255

    # Score here should be the max score
    # out of any combo in the list
    def __init__(self, userIds, score):
        self.userIds = userIds
        self.score = score
        self.hue = self.generate_hue()
    
    def __eq__(self, other):
        return self.userIds == other.userIds
    
    def __hash__(self):
        return sum(self.userIds) 
    
    def __str__(self):
        return ("Duplicate with score " + str(self.score) + " containing " + str(self.userIds))

@login_required
@admin_required
@bp.route('/all_users', methods=('GET', 'POST'))
def all_users():
    #itemsList = conn.execute(items.select(items.c.foodBankId==g.user.foodBankId)).fetchall()
    userList = getUserList()
    showingDuplicates = False
    print(create_master_spreadsheet())
    if request.method == "POST" and 'num-vehicles' in request.values.to_dict().keys():
        print(request.values.to_dict())
        if 'redirect' in request.values.to_dict().keys():
            return loadingScreen(num_vehicles=request.values.get('num-vehicles'))
        else:
            assign.createAllRoutes(foodBankId=g.user.id, num_vehicles=int(request.values.get('num-vehicles')))
            return redirect('/all_orders')
    if request.method == "GET" and "volunteer" in request.args.keys():
        volunteerId = int(request.args.get("volunteer"))
        orderId = int(request.args.get("order"))
        order_assignment.assign(orderId=orderId, volunteerId=volunteerId)
        return redirect("/all_users")
    elif 'find-duplicates' in request.args.keys():
        # TODO: this is a really really shitty algorithm
        # and can definitley be sped up (but I only need to
        # run it once a week so it should be OK)
        setDuplicates = set() # set of sets of user ID's
        for firstUser in userList:
            userIdSet = {firstUser.id}
            scoreMax = 0
            for secondUser in userList:
                score = fuzz.ratio(firstUser.name, secondUser.name)
                print("Ratio: " + str(score))
                # TODO: make this use things other than name
                if score > 80:
                    userIdSet.add(secondUser.id)
                    scoreMax = max(score, scoreMax)
            if len(userIdSet) > 1:
                setDuplicates.add(Duplicate(userIdSet, scoreMax))
        # print("Set duplicates:" + str(next(iter(setDuplicates))))
        userList = []
        for duplicate in setDuplicates:
            for userId in duplicate.userIds:
                row = (conn.execute(users.select().where(users.c.id==userId)).fetchone())
                d = dict(row.items())
                d['hue'] = duplicate.hue
                userList.append(d)
        showingDuplicates = True

    if request.method == "POST":
        key = next(request.form.keys())
        print("Key: " + str(key))
        if "delete" in key:
            userId = int(key[len('delete-'):])
            conn.execute(users.delete().where(users.c.id==userId))
        if "enable" in key:
            userId = int(key[len('enable-'):])
            conn.execute(users.update().where(users.c.id==userId).values(disabled=False))
        if "download-master-spreadsheet" in key:
            return create_master_spreadsheet()
        if "disable" in key:
            userId = int(key[len('disable-'):])
            conn.execute(users.update().where(users.c.id==userId).values(disabled=True))
            routesList = conn.execute(routes.select().where(routes.c.foodBankId==g.user.foodBankId)).fetchall()
            for route in routesList:
                content = loads(route.content)
                if userId in content:
                    print("UserID in content!")
                    content.remove(userId)
                    conn.execute(routes.update().where(routes.c.id==route.id).values(content=dumps(content)))
                    break
        userList = getUserList()

    volunteers = getVolunteers()
    today = datetime.date.today()
    activeUsersCount = 0
    disabledUsersCount = 0
    for user in userList:
        if user['disabled']:
            disabledUsersCount += 1
        else:
            activeUsersCount += 1

    return render_template("view_all_orders.html", users=userList, showingDuplicates=showingDuplicates, volunteers=volunteers, activeUsersCount=activeUsersCount, disabledUsersCount=disabledUsersCount)

def getUserList():
    return conn.execute(users.select().order_by(desc(users.c.disabled)).where(and_(users.c.foodBankId == g.user.id, users.c.role == "RECIEVER"))).fetchall()

@bp.route('/loading', methods=(['GET', 'POST']))
def loadingScreen(num_vehicles=40):
    return render_template("loading.html", num_vehicles=40)

@login_required
@admin_required
@bp.route('/routes-spreadsheet/', methods=('GET', 'POST'))
def send_spreadsheet():
    print("Sending spreadsheet...")
    google_maps = request.args.get('map') == 'true'
    routesList = conn.execute(routes.select(routes.c.foodBankId==g.user.id)).fetchall()
    outputColumns = ['Number', 'First Name', "Last Name", "Address", "Apt", "City", "State", "Zip", "Phone", "Notes"]
    if google_maps:
        outputColumns.append("Google Maps")
    pdList = []
    routeCount = 0
    for route in routesList:
        usersList = getUsers(route.id, addOriginal=True, includeDepot=True, columns=[users.c.id, users.c.name, users.c.email, users.c.formattedAddress, users.c.address2, users.c.cellPhone, users.c.instructions])
        for user in usersList:
            userCount = 1
            try:
                parsed = usaddress.tag(user['Full Address'])[0]
                user['City'] = parsed['PlaceName']
                user['State'] = 'WA'
                user['Zip'] = parsed['ZipCode']
                addressFormat = ['AddressNumber', 'StreetNamePreDirectional', 'StreetName', 'StreetNamePostType']
                address = ""
                for attribute in addressFormat:
                    if attribute not in parsed.keys():
                        continue
                    if address == "":
                        address = parsed[attribute]
                    else:
                        address = address + " " + parsed[attribute]
            except:
                address = user['Full Address']
            user['Address'] = address
                
            names = user['Name'].split(" ", maxsplit=1)
            user['First Name'] = names[0]
            user['Last Name'] = names[1]
            if user['Last Name'] == "nan":
                user['Last Name'] = ''
            if 'Google Maps' in outputColumns:
                user['Google Maps'] = google_maps_qr.make_single_url(user['Full Address'])
            user['Number'] = userCount
        google_maps_link = google_maps_qr.make_url(usersList) 
        # remove food bank
        usersList.remove(usersList[0])
        usersList.remove(usersList[len(usersList)-1])
        row_num = 15
        create_blank_rows(row_num - len(usersList), usersList, outputColumns)
        if google_maps:
            footerContent = [['', 'Google maps link:', google_maps_link], ['', 'Assigned to: ', ''], ['', 'Date:', ''], ['', 'Route ' + str(routeCount)]]
        else:
            footerContent = [['', 'Assigned to: ', ''], ['', 'Date:', ''], ['', 'Route ' + str(routeCount)]]
        routeCount += 1
        create_footer_rows(footerContent, usersList, outputColumns)
        df = pd.DataFrame(usersList)
        pdList.append(df)
    fileName = environ['INSTANCE_PATH'] + 'routes.xlsx'
    writer = pd.ExcelWriter(fileName, engine="openpyxl")
    for index in range(0, len(pdList)):
        pdList[index].to_excel(writer, sheet_name="Route " + str(index), index=False, columns=outputColumns)
    writer.save()
    
    # set formatting
    workbook = load_workbook(fileName)
    writer = pd.ExcelWriter(fileName, engine="openpyxl")
    writer.book = workbook
    for ws in workbook.worksheets:
        print(ws.title)
        for col in ws.iter_cols():
            maxWidth = ''
            for cell in col:
                cell.font = styles.Font(name='Times New Roman', size=10)
                if len(str(cell.value)) > len(maxWidth) and cell.value is not None and 'oogle.com' not in cell.value:
                    maxWidth = str(cell.value)
            ws.column_dimensions[col[0].column_letter].width = len(maxWidth)
    writer.save()
    return send_file(fileName, as_attachment=True)

@login_required
@admin_required
@bp.route('/routes-overview/', methods=('GET', 'POST'))
def send_overview():
    
    routesList = conn.execute(routes.select(routes.c.foodBankId==g.user.id)).fetchall()
    dictList = []
    count = 0
    for route in routesList:
        dictList.append({
            'Route Number': count,
            'Length': len(loads(route.content)),
            'Date': ' '
        })
        count += 1
    fileName = environ['INSTANCE_PATH'] + 'routes-overview.xlsx'
    df = pd.DataFrame(dictList)
    df.to_excel(fileName, index=False, header=True)
    return send_file(fileName, as_attachment=True)

def create_blank_rows(num_rows, currentList, outputColumns):
    for y in range(0, num_rows):
        toAppend = {}
        for x in outputColumns:
            toAppend[x] = ''
        currentList.append(toAppend)
        
# Content is a 2D list
def create_footer_rows(content, currentList, outputColumns):
    for rowList in content:
        rowDict = {}
        for x in range(0, len(rowList)):
            rowDict[outputColumns[x]] = rowList[x]
        for x in range(len(rowList), len(outputColumns)):
            rowDict[outputColumns[x]] = '' 
        currentList.append(rowDict)


@login_required
@admin_required
@bp.route('/master-spreadsheet', methods=('GET', 'POST'))
def create_master_spreadsheet():
    columns = ['name', 'email', 'formattedAddress', 'address2', 'cellPhone', 'instructions']
    prettyNames = {'formattedAddress': 'Full Address',
                    'address2': 'Apt',
                    'name': 'Name',
                    'email':'Email',
                    'cellPhone': 'Phone',
                    'instructions': 'Notes'}
    enabledRpList = conn.execute(users.select(and_(users.c.role=="RECIEVER", users.c.foodBankId==g.user.id, users.c.disabled==False))).fetchall()
    enabled = generateUserDataFrame(enabledRpList)
    disabledRpList = conn.execute(users.select(and_(users.c.role=="RECIEVER", users.c.foodBankId==g.user.id, users.c.disabled==True)).order_by(users.c.disabledDate)).fetchall()
    disabled = generateUserDataFrame(disabledRpList)
    outputColumns = ['First Name', "Last Name", "Email", "Address", "Apt", "City", "Zip", "Phone", "Notes"]
    writer = pd.ExcelWriter(environ['INSTANCE_PATH'] + 'client-master-list.xlsx')
    enabled.to_excel(writer, sheet_name="Master list", columns=outputColumns, startrow=0, index=False, na_rep="")
    disabled.to_excel(writer, sheet_name="Disabled clients", columns=outputColumns, startrow=0, index=False, na_rep="")
    writer.save()
    return send_file(environ['INSTANCE_PATH'] + 'client-master-list.xlsx', as_attachment=True)

def generateUserDataFrame(userRpList):
    columns = ['name', 'email', 'formattedAddress', 'address2', 'cellPhone', 'instructions']
    prettyNames = {'formattedAddress': 'Full Address',
                    'address2': 'Apt',
                    'name': 'Name',
                    'email':'Email',
                    'cellPhone': 'Phone',
                    'instructions': 'Notes'}
    row2dict = lambda r: {prettyNames[c]: betterStr(getattr(r, c)) for c in columns}
    userDictList = []
    disabled = userRpList[0].disabled
    disabledDate = userRpList[0].disabledDate
    firstDate = True
    for user in userRpList:
        if (user.disabledDate != disabledDate or firstDate) and disabled:
            disabledDate = user.disabledDate
            blankRow = {'First Name': '', 'Last Name': '', 'Email': '', 'Address': '', 'Apt': '', 'City': '', 'Zip': '', 'Phone': '', 'Notes': ''}
            if type(disabledDate) == str: # Type changes depending on if you're using mysql or sqlite apparently
                removalRow = {'First Name': 'Removal', 'Last Name': disabledDate, 'Email': '', 'Address': '', 'Apt': '', 'City': '', 'Zip': '', 'Phone': '', 'Notes': ''}
            else:
                removalRow = {'First Name': 'Removal', 'Last Name': disabledDate.strftime('%m-%d-%y'), 'Email': '', 'Address': '', 'Apt': '', 'City': '', 'Zip': '', 'Phone': '', 'Notes': ''}

            if not firstDate:
                userDictList.append(blankRow)
            userDictList.append(removalRow)
            firstDate = False
        userDict = row2dict(user)
        try:
            parsed = usaddress.tag(userDict['Full Address'])[0]
            userDict['City'] = parsed['PlaceName']
            userDict['Zip'] = parsed['ZipCode']
            addressFormat = ['AddressNumber', 'StreetNamePreDirectional', 'StreetName', 'StreetNamePostDirectional', 'StreetNamePostModifier', 'StreetNamePostType']
            address = ""
            for attribute in addressFormat:
                if attribute not in parsed.keys():
                    continue
                if address == "":
                    address = parsed[attribute]
                else:
                    address = address + " " + parsed[attribute]
        except:
            address = userDict['Full Address']
        userDict['Address'] = address
        names = userDict['Name'].split(" ", maxsplit=1)
        userDict['First Name'] = names[0]
        userDict['Last Name'] = names[1]
        if userDict['Last Name'] == "nan":
            userDict['Last Name'] = ''
        userDictList.append(userDict)
    df = pd.DataFrame(userDictList)

    return df

def betterStr(value):
    if value == None:
        return ''
    else:
        return str(value)

@login_required
@admin_required
@bp.route('/shipping_labels', methods=('GET', 'POST'))
def generate_shipping_labels():
    volunteers = getVolunteers()
    ordersDict = getOrders(g.user.id)
    itemsList = loads(conn.execute(users.select(users.c.id==g.user.foodBankId)).fetchone()['items'])
    html = render_template("shipping-labels.html", orders=ordersDict, volunteers=volunteers, barcode_to_base64=barcode_to_base64, qrcode_to_base64=qrcode_to_base64)
    # Uncomment this line for debugging
    #return html
    pdf = pdfkit.from_string(html, False)
    response = make_response(pdf)
    response.headers['Content-type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline;'
    return response

def getVolunteers():
    proxy = conn.execute(users.select(and_(users.c.role=="VOLUNTEER", users.c.approved==True, users.c.volunteerRole=="DRIVER"))).fetchall()
    dictList = []
    for volunteer in proxy:
        volunteerDict = {}
        columns = conn.execute(users.select()).keys()
        for column in columns:
            volunteerDict[column] = getattr(volunteer, column)
        volunteerDict['numOrders'] = len(conn.execute(orders.select(and_(orders.c.volunteerId==volunteer.id, orders.c.completed==0))).fetchall())
        dictList.append(volunteerDict)
    return dictList

def barcode_to_base64(orderId):
    imgByteArray = io.BytesIO()
    Code128(str(orderId) + "\n", writer=ImageWriter()).write(imgByteArray)
    return base64.b64encode(imgByteArray.getvalue()).decode()

def qrcode_to_base64(orderId):
    urlString = request.base_url[:-len('shipping_labels')] + 'auto_complete?orderId=' + str(orderId)
    imgByteArray = io.BytesIO()
    code = qrcode.make(urlString)
    code.save(imgByteArray, format="PNG")
    return base64.b64encode(imgByteArray.getvalue()).decode()
