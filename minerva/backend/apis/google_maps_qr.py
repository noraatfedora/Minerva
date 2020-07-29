import qrcode
from db import orders, users, conn
from sqlalchemy import select

# Takes a list of order IDs, saves image to static/google_maps_qr.png
def make_qr_code(orderIds):
    link = make_url(orderIds)
    img = qrcode.make(link)
    img.save('static/google_maps_qr.png')

def make_url(orderIds):
    link = "https://google.com/maps/dir/"
    # https://www.google.com/maps/dir/2640+134th+Avenue+Northeast,+Bellevue,+WA/The+Overlake+School,+20301+NE+108th+St,+Redmond,+WA+98053/Black+Lodge+Research,+Northeast+65th+Street,+Redmond,+WA/
    slash = '/'
    addresses = []
    for orderId in orderIds:
        orderId = int(orderId)
        order = conn.execute(orders.select().where(orders.c.id==orderId)).fetchone()
        address = conn.execute(select([users.c.address]).where(users.c.id==order.userId)).fetchone()[0].replace(' ', '+')
        addresses.append(address)
    link += slash.join(addresses)
    return link
