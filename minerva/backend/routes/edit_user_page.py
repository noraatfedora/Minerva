from os import environ
from flask import ( Blueprint, flash, g, redirect, render_template,
    request, session, url_for, Flask, make_response, send_file
)
import geopy
from minerva.backend.routes.auth import login_required, admin_required 
from minerva.backend.apis.db import users, conn, routes

bp = Blueprint('edit_user_page', __name__)

@bp.route('/edit_user/<userId>', methods=['GET', 'POST'])
def edit_users(userId):
    user = conn.execute(users.select().where(users.c.id==userId)).fetchone()
    if request.method == "GET":
        return render_template('edit_user.html', user=user)
    else:
        print(request.form.to_dict())
        address = request.form['address']
        latitude = user['latitude']
        longitude = user['longitude']
        '''
        conn.execute(users.update().where(users.c.id==user.id).values(
                formattedAddress=coords[0],
                latitude=coords[1][0],
                longitude=coords[1][1]
            ))
        '''

        if address != user['formattedAddress']:
            API_KEY = environ['GOOGLE_API']
            googleWrapper = geopy.geocoders.GoogleV3(api_key=API_KEY)
            coords = googleWrapper.geocode(query=request.form['address'], timeout=100)
            address = coords[0]
            latitude = coords[1][0]
            longitude = coords[1][1]

        conn.execute(users.update().where(users.c.id==userId).values(
        formattedAddress = address,
        address2 = request.form['address2'],
        email = request.form['email'],
        cellPhone = request.form['cellPhone'],
        instructions = request.form['instructions'],
        latitude = latitude,
        longitude = longitude))
        return redirect('/all_users#card-' + str(user['id']))