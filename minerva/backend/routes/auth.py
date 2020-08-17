import functools
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash
from minerva.backend.apis.db import users, conn, items, family_members
from sqlalchemy import select, update
from json import loads, dumps
from os import environ
from sys import path
from minerva.backend.apis.email import send_new_volunteer_request_notification

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
        user = conn.execute(users.select().where(
            users.c.email == email)).fetchone()
        if user is None:
            error = 'Incorrect email address.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('index'))
        flash(error)

    return render_template('auth/login.html', title="Log In")


dietaryRestrictions = ["Lactose Intolerant",
                       "Vegetarian", "Peanut Allergy", "Gluten Free"]


def fetch_delete(key, dictionary):
    value = dictionary[key]
    dictionary.pop(key, None)
    return value


@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == "POST":
        with open("minerva/backend/apis/database/supported_zip_codes", 'r') as f:
            supportedZipCodes = f.read()

        form = request.form.to_dict()

        name = fetch_delete('name', form)
        birthday = fetch_delete('birthday', form)
        email = fetch_delete('email', form)
        password = fetch_delete('password', form)
        confirm = fetch_delete('confirm', form)
        address = fetch_delete('address', form)
        zipCode = fetch_delete('zipCode', form)
        cellPhone = fetch_delete('cell', form)
        homePhone = fetch_delete('homePhone', form)
        instructions = fetch_delete('instructions', form)
        restrictions = []

        for restriction in dietaryRestrictions:
            if restriction in request.form:
                restrictions.append(restriction)
        error = ""

        if zipCode[0:5] not in supportedZipCodes:
            error = "Sorry, but your zip code is not supported at this time. Please contact your local food banks."
        elif conn.execute(users.select().where(users.c.email == email)).fetchone() is not None:
            error += '\nUser {} is already registered.'.format(email)

        if error == "":
            password_hash = generate_password_hash(password)

            conn.execute(users.insert(), name=name, birthday=birthday, email=email, password=password_hash, address=address,
                                  role="RECIEVER", instructions=instructions, cellPhone=cellPhone, homePhone=homePhone,
                                  zipCode=zipCode, completed=0, foodBankId=getFoodBank(address), restrictions=dumps(restrictions))

            user_id = conn.execute(users.select().where(users.c.email == email)).fetchone().id

            for key in list(form):
                if ('name' not in key and 'race' not in key):
                    form.pop(key, None)

            # Get list of keys
            keys = [*form]

            for i in range(0, len(keys), 2):
                conn.execute(family_members.insert(), user=user_id, name=form[keys[i]], race=form[keys[i + 1]])

            return redirect(url_for('auth.login'))
        else:
            return render_template('auth/register.html', title='Register', dietaryRestrictions=dietaryRestrictions, error=error)
    return render_template('auth/register.html', title='Register', dietaryRestrictions=dietaryRestrictions, error="")


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = conn.execute(users.select().where(
            users.c.id == user_id)).fetchone()


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
    if request.method == 'POST':
        if g.user.role == "ADMIN":
            newItemsList = []
        for attribute in request.form:
            if attribute[:len('name')] == 'name':
                newItemsList.append(request.form[attribute])
            else:
                given = request.form[attribute]
                if (given != '') and attribute != 'submit':
                    print("Given: " + str(given))
                    query = users.update().where(users.c.id == g.user['id'])
                    values = {
                        'email': query.values(email=given),
                        'address': query.values(address=given),
                        'cellPhone': query.values(cellPhone=given),
                        'instructions': query.values(instructions=given),
                        'homePhone': query.values(homePhone=given),
                        'requestPageDescription': query.values(requestPageDescription=given)
                    }[attribute]
                    print("Values: " + str(values))
                    conn.execute(values)

        # Remove all of our items, so that we can just cleanly replace it
        conn.execute(items.delete().where(items.c.foodBankId == g.user.id))
        # Insert new elements into table
        for itemName in newItemsList:
            conn.execute(items.insert().values(
                name=itemName, foodBankId=g.user.id))

        return redirect('/youraccount')
    if g.user.role == "ADMIN":
        rawItemsList = conn.execute(select([items.c.name]).where(
            items.c.foodBankId == g.user.id)).fetchall()
        itemsList = []
        for item in rawItemsList:
            itemsList.append(item[0])
        print("Items list: " + str(itemsList))
        return render_template("auth/changeinfo.html", user=g.user, items=itemsList)
    return render_template("auth/changeinfo.html", user=g.user)


@bp.route('/volunteerregister', methods=('GET', 'POST'))
def volunteerregister():
    foodBanks = conn.execute(
        select([users.c.name], whereclause=users.c.role == "ADMIN")).fetchall()
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
        volunteerRole = request.form['volunteerRole']

        # kinda proud of how clean this line is ngl
        foodBankId, foodBankEmail = tuple(conn.execute(
            select([users.c.id, users.c.email]).where(users.c.name == foodBank)).fetchone())
        dayValues = {}
        error = ""
        # TODO: find error stuff
        if error == "":
            password_hash = generate_password_hash(password)
            conn.execute(users.insert(), email=email, name=name, password=password_hash, address=address,
                         role="VOLUNTEER", cellPhone=cellPhone, homePhone=homePhone,
                         zipCode=zipCode, completed=0, approved=False, foodBankId=foodBankId, volunteerRole=volunteerRole)

            send_new_volunteer_request_notification(foodBankEmail, name)
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
            return render_template('auth/volunteer-register.html', title='Register', data=data)
    data = {'email': '', 'address': '', 'firstName': '',
            'lastName': '', 'homePhone': '', 'zipCode': ''}
    return render_template('auth/volunteer-register.html', title='Register', data=data, foodBanks=foodBanks)


@bp.route('/changepass', methods=['GET', 'POST'])
@login_required
def change_pass():
    if request.method == 'POST':
        old = request.form['old']
        new = request.form['new']
        confirm = request.form['confirm']
        if check_password_hash(g.user['password'], old):
            if new == confirm:
                conn.execute(users.update().where(users.c.id == g.user['id']).values(
                    password=generate_password_hash(new)))
                return redirect('/youraccount')
            else:
                flash("Passwords do not match.")
        else:
            flash("Your current password is incorrect.")
    return render_template("auth/changepass.html")


def getFoodBank(address):
    return conn.execute(select([users.c.id]).where(users.c.role == 'ADMIN')).fetchone()[0]
