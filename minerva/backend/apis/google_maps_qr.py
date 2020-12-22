import qrcode
from minerva.backend.apis.db import users, conn
from sqlalchemy import select
from flask import url_for
from io import BytesIO
import base64

# Takes a list of order IDs, returns base64 data
def make_qr_code(userList, routeId):
    link = make_url(userList)
    buffered = BytesIO()
    img = qrcode.make(link)
    img.save(buffered, format="PNG")
    data = base64.b64encode(buffered.getvalue())
    return str(data)[2:len(data)-2]
def make_user_qr(addr):
    link = make_single_url(addr)
    buffered = BytesIO()
    img = qrcode.make(link)
    img.save(buffered, format="PNG")
    data = base64.b64encode(buffered.getvalue())
    return str(data)[2:len(data)-2]

def make_url(userList):
    link = "https://google.com/maps/dir/"
    # https://www.google.com/maps/dir/2640+134th+Avenue+Northeast,+Bellevue,+WA/The+Overlake+School,+20301+NE+108th+St,+Redmond,+WA+98053/Black+Lodge+Research,+Northeast+65th+Street,+Redmond,+WA/
    slash = '/'
    addresses = []
    for user in userList:
        if 'formattedAddress' in user.keys():
            addr = user['formattedAddress']
        else:
            addr = user['Full Address'] # if this is in spreadsheet form or something
        addresses.append(prep_address(addr))
    link += slash.join(addresses)
    return link

def make_single_url(address):
    return "https://google.com/maps/place/" + prep_address(address)

def osm_url(userList):
    link = "https://map.project-osrm.org/?z=12&center="
    separator = '&loc='
    coordsList = []
    for user in userList:
        coordsList.append(user['latitude'] + '%2C' + user['longitude'])
    link += separator.join(coordsList)
    footer = "&hl=en&alt=0&srv=0"
    return link + footer

# This is a separate function because
# I know at some point we're gonna have
# weird edge cases and this is the best
# way to do it
def prep_address(address):
    return address.replace(" ", "+")