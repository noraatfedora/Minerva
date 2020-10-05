import qrcode
from db import users, conn
from sqlalchemy import select

# Takes a list of order IDs, saves image to static/google_maps_qr.png
def make_qr_code(orderIds):
    link = make_url(orderIds)
    img = qrcode.make(link)
    img.save('static/google_maps_qr.png')

def make_url(userList):
    link = "https://google.com/maps/dir/"
    # https://www.google.com/maps/dir/2640+134th+Avenue+Northeast,+Bellevue,+WA/The+Overlake+School,+20301+NE+108th+St,+Redmond,+WA+98053/Black+Lodge+Research,+Northeast+65th+Street,+Redmond,+WA/
    slash = '/'
    addresses = []
    for user in userList:
        addresses.append(prep_address(user['formattedAddress']))
    link += slash.join(addresses)
    return link

# This is a separate function because
# I know at some point we're gonna have
# weird edge cases and this is the best
# way to do it
def prep_address(address):
    return address.replace(" ", "+")