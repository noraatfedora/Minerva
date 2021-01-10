from flask import ( Blueprint, flash, g, redirect, render_template,
    request, session, url_for, Flask, make_response, send_file
)
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
        conn.execute(users.update().where(users.c.id==userId).values( formattedAddress = request.form['address'],
        address2 = request.form['address2'],
        email = request.form['email'],
        cellPhone = request.form['cellPhone'], instructions = request.form['instructions']))
        return redirect('/all_users#card-' + str(user['id']))