import functools
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash
from db import users, conn
from sqlalchemy import select, update 
from json import loads
from os import environ
from sys import path

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=('GET', 'POST'))
def login():
    redirect_url = request.args.get('redirect_url')
    if redirect_url is None:
        redirect_url = 'index'
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        error = None
        user = conn.execute(users.select().where(users.c.email==email)).fetchone()
        if user is None:
            error = 'Incorrect email address.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'
        
        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('index'))
        print(error)
        flash(error)
    
    return render_template('auth/login.html', title = "Log In")

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == "POST":
        with open(environ['INSTANCE_PATH'] + 'supported_zip_codes', 'r') as f:
            supportedZipCodes = f.read()
        email = request.form['email']
        password = request.form['password']
        confirm = request.form['confirm']
        address = request.form['address']
        zipCode = request.form['zipCode']
        instructions = request.form['instructions']
        cellPhone = request.form['cell']
        homePhone = request.form['homePhone']
        error = "" 
        
        if zipCode[0:5] not in supportedZipCodes:
            error += "Sorry, but your zip code is not supported at this time. Please contact your local food banks."
        elif conn.execute(users.select().where(users.c.email==email)).fetchone() is not None:
            error = 'User {} is already registered.'.format(email)
        
        if error == "":
            print("poopdsfy poop!")
            password_hash = generate_password_hash(password)
            conn.execute(users.insert(), email=email, password=password_hash, address=address, 
            role="RECIEVER", instructions=instructions, cellPhone=cellPhone, homePhone=homePhone,
            zipCode=zipCode, completed=0, foodBankId=getFoodBank(address))
            return redirect(url_for('auth.login'))
        else:
            flash(error)
            data = {
                    'email': email,
                    'address': address,
                    'cellPhone': cellPhone,
                    'homePhone': homePhone,
                    'zipCode': zipCode,
                    'instructions': instructions
                    }
            return render_template('auth/register.html', title='Register', data=data)
    data = {'email': '', 'address': '', 'homePhone': '', 'zipCode': '', 'instructions': ''}
    return render_template('auth/register.html', title = 'Register', data=data)

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = conn.execute(users.select().where(users.c.id==user_id)).fetchone()

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        
        return view(**kwargs)

    return wrapped_view

def volunteer_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        role = g.user['role'].lower()
        if role != "volunteer" and role != "admin":
            print("Invalid authentication!")
            print(role)
            return redirect('/')

        return view(**kwargs)

    return wrapped_view

def admin_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        role = g.user['role'].lower()
        if role != "admin":
            print("Invalid authentication!")
            print(role)
            return redirect('/')
    return wrapped_view

@bp.route('/youraccount')
@login_required
def your_account():
    attributes = {
        'email': 'email',
        'address': 'home address',
        'cellPhone': "cell phone",
        'instructions': 'special delivery instructions',
        'homePhone': "home phone"
    }

    return render_template("youraccount.html", attributes=attributes, user=g.user)

@bp.route('/changeinfo', methods=['GET', 'POST'])
@login_required
def change_info():
    # For security, we double check that the column we're inserting is in this list.
    attributesList = {
        'email', 'address', 'cellPhone', 'instructions', 'homePhone', "zipCode"
    }
    if request.method=='POST':
        for attribute in request.form:
            given = request.form[attribute]
            if given != '' and attribute != 'submit' and attribute in attributesList:
                print("about to generate query")
                query = users.update().where(users.c.id==g.user['id'])
                values = {
                    'email': query.values(email=given),
                    'address': query.values(address=given),
                    'cellPhone': query.values(cellPhone=given),
                    'instructions': query.values(instructions=given),
                    'homePhone': query.values(homePhone=given)
                }[attribute]
                conn.execute(values)
        return redirect('/youraccount')
    return render_template("auth/changeinfo.html", user=g.user)


@bp.route('/volunteerregister', methods=('GET', 'POST'))
def volunteerregister():
    days = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]
    foodBanks = conn.execute(select([users.c.name], whereclause=users.c.role=="ADMIN")).fetchall()
    if request.method == "POST":
        print("Data: " + str(request.form))
        email = request.form['email']
        name = request.form['name']
        password = request.form['password']
        confirm = request.form['confirm']
        address = request.form['address']
        zipCode = request.form['zipCode']
        cellPhone = request.form['cell']
        homePhone = request.form['homePhone']
        foodBank = request.form['organization']
        foodBankId = conn.execute(select([users.c.id]).where(users.c.name==foodBank)).fetchone()[0]
        dayValues = {}
        for day in days:
            if day in request.form.keys():
                dayValues[day] = True
            else:
                dayValues[day] = False
        error = ""
        print("dayValues: " + str(dayValues))
        if error == "":
            print("poopdsfy poop!")
            password_hash = generate_password_hash(password)
            conn.execute(users.insert(), email=email, name=name, password=password_hash, address=address, 
            role="VOLUNTEER", cellPhone=cellPhone, homePhone=homePhone,
            zipCode=zipCode, completed=0, approved=False, foodBankId=foodBankId,
            sunday=dayValues["Sunday"], monday=dayValues["Monday"], tuesday=dayValues["Tuesday"],
            wednesday=dayValues["Wednesday"], thursday=dayValues["Thursday"], friday=dayValues["Friday"], saturday=dayValues["Saturday"])
            return redirect(url_for('auth.login'))
        else:
            flash(error)
            data = {
                    'email': email,
                    'address': address,
                    'name': name,
                    'cellPhone': cellPhone,
                    'homePhone': homePhone,
                    'zipCode': zipCode,
                    }
            return render_template('auth/volunteer-register.html', title='Register', data=data, days=days)
    data = {'email': '', 'address': '', 'firstName': '', 'lastName': '','homePhone': '', 'zipCode': ''}
    return render_template('auth/volunteer-register.html', title = 'Register', data=data, days=days, foodBanks=foodBanks)

@bp.route('/changepass', methods=['GET', 'POST'])
@login_required
def change_pass():
    if request.method=='POST':
        old = request.form['old']
        new = request.form['new']
        confirm = request.form['confirm']
        if check_password_hash(g.user['password'], old):
            if new == confirm:
                conn.execute(users.update().where(users.c.id==g.user['id']).values(password=generate_password_hash(new)))
                return redirect('/youraccount')
            else:
                flash("Passwords do not match.")
        else:
            flash("Your current password is incorrect.")
    return render_template("auth/changepass.html")

def getFoodBank(address):
    return conn.execute(select([users.c.id]).where(users.c.role=='ADMIN')).fetchone()[0]
