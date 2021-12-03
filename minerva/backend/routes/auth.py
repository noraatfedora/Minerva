import functools
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash
from minerva.backend.apis.db import users, conn, items, family_members
from datetime import datetime, date
from sqlalchemy import select, update, and_
from json import loads, dumps
import xlrd
from os import environ
from minerva.backend.apis.assign import setCoords
from sys import path
from minerva.backend.apis.email import send_new_volunteer_request_notification
import pandas as pd

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
    value = None
    if key in dictionary:
        value = dictionary[key]
    dictionary.pop(key, None)
    return value


@bp.route('/upload_data', methods=('GET', 'POST'))
def upload_data():
    message = ''
    if request.method == "GET":
        return render_template('upload_data.html', title='All Users', message=message)

    if 'name' in request.form:
        form = request.form.to_dict()

        name = fetch_delete('name', form)
        birthday = datetime.strptime(
            fetch_delete('birthday', form), "%Y-%m-%d")
        email = fetch_delete('email', form)
        password = fetch_delete('password', form)
        confirm = fetch_delete('confirm', form)
        address = fetch_delete('address', form)
        zipCode = fetch_delete('zipCode', form)
        cellPhone = fetch_delete('cell', form)
        homePhone = fetch_delete('homePhone', form)
        instructions = fetch_delete('instructions', form)
        restrictions = []

        error = ""

        if (not email == "") and (not email == "info@themadfseattle.org") and conn.execute(users.select().where(users.c.email == email)).fetchone() is not None:
            error += '\nUser {} is already registered.'.format(email)

        if error == "":
            conn.execute(users.insert(), name=name, birthday=birthday, email=email, address=address,
                         role="RECIEVER", instructions=instructions, cellPhone=cellPhone, homePhone=homePhone,
                         zipCode=zipCode, completed=0, foodBankId=getFoodBank(address), lastDelivered=datetime.now(), restrictions=dumps(restrictions))

            user_id = conn.execute(users.select().where(
                users.c.email == email)).fetchone().id

            for key in list(form):
                if ('name' not in key and 'race' not in key):
                    form.pop(key, None)

            # Get list of keys
            keys = [*form]

            for i in range(0, len(keys), 2):
                conn.execute(family_members.insert(), user=user_id,
                             name=form[keys[i]], race=form[keys[i + 1]])
        setCoords(environ['GOOGLE_API'])

    else:
        import traceback
        message = "Successfully uploaded the spreadsheet!"
        # try:
        file = request.files.get('users')
        filename = file.filename
        splitname = filename.split(".")
        fileType = splitname[len(splitname) - 1]
        print(request.form)
        delete = 'delete-checkbox' in request.form.keys()
        header = int(request.form['header'])
        disabledUsers = 'disabled-checkbox' in request.form.keys()
        print("Form: " + str(request.form))
        if request.form['spreadsheet-type'] == 'master-spreadsheet':
            importMasterList(request, filename, fileType,
                delete, header, disabledUsers)
        elif request.form['spreadsheet-type'] == 'routes-spreadsheet':
            importRoutesList(request, filename, fileType, delete, header)
        elif request.form['spreadsheet-type'] == 'family-member-data':
            importFamilyMemberData(
                request, filename, fileType, delete, header)
        setCoords(environ['GOOGLE_API'])
        cities = ['Tacoma', 'University Place', 'Parkland', 'Spanaway', 'Lakewood', 'Puyallup',
                    'Fife', 'Federal Way', 'Algona', 'Pacific', 'Joint Base Lewis-McChord', 'Steilacoom']
        disableOutOfRange(cities)
        '''
        # except Exception as e:
            message = "Something went wrong while uploading the spreadsheet. You can view the documentation for correct formatting <a href='https://jaredgoodman03.github.io/Minerva-docs/admin-instructions#file-upload'> here. </a> Here's the error message, so you can figure out what's wrong: <br> <code> " + str(e) + "</code>"
        '''

    return render_template('upload_data.html', title='All Users', message=message)


def importMasterList(request, filename, fileType, delete, header, disabledSheet=True):
    masterDf = pd.DataFrame()
    conn.execute(users.update().where(and_(users.c.foodBankId ==
                 g.user.id, users.c.role == "RECIEVER")).values(inSpreadsheet=0))
    if (fileType == 'csv'):
        masterDf = pd.read_csv(
            request.files['users'], header=header, keep_default_na=False)
    else:
        masterDf = pd.read_excel(request.files['users'].read(
        ), sheet_name="Master list", header=header, keep_default_na=False)
        masterDf = masterDf.dropna(thresh=2)
        if disabledSheet:
            disabledDf = pd.read_excel(request.files['users'].read(
            ), sheet_name="Disabled clients", header=header, keep_default_na=False)
            disabledDf = disabledDf.dropna(thresh=2)
            addUsersFromDf(disabledDf, True)
    addUsersFromDf(masterDf, False)

    if delete:
        conn.execute(users.delete().where(and_(users.c.foodBankId == g.user.id,
                     users.c.role == "RECIEVER", users.c.inSpreadsheet == 0)))


def addUsersFromDf(df, disabled):
    disabledDate = date.today()
    for index, row in df.iterrows():
        if row['First Name'].lower() == "removal":
            disabledDate = row['Last Name'].date()
            continue
        # This checks to make sure email is not nan
        if 'Email' in row.keys() and (type(row['Email']) == str) and not row['Email'] == "" and not row['Email'] == "info@themadfseattle.org":
            emailUser = conn.execute(users.select().where(
                users.c.email == row['Email'])).fetchone()
            if emailUser is not None:
                print("Skipping " + str(row) + " because of a duplicate email")
                conn.execute(users.update().where(users.c.id == emailUser.id).values(
                    inSpreadsheet=1, disabledDate=disabledDate, disabled=disabled))
                continue
        else:
            nameUser = conn.execute(users.select().where(users.c.name == betterStr(
                row['First Name']) + " " + betterStr(row['Last Name']))).fetchone()
            if nameUser is not None:
                print("Found duplicate name in " + str(row))
                conn.execute(users.update().where(users.c.id == nameUser.id).values(
                    inSpreadsheet=1, disabledDate=disabledDate, disabled=disabled))
                continue
        if 'state' not in row.keys():
            state = 'WA'
        else:
            state = row['state']

        if 'Household Size' not in row.keys():
            hh_size = -1
        else:
            hh_size = row['Household Size']
        conn.execute(users.insert(),
                     name=betterStr(row['First Name']) +
                     " " + betterStr(row['Last Name']),
                     email=betterStr(row['Email']),
                     address=betterStr(row['Address']),
                     address2=betterStr(row['Apt']),
                     role="RECIEVER",
                     instructions=betterStr(row['Notes']),
                     cellPhone=betterStr(row['Phone']),
                     zipCode=betterStr(row['Zip']),
                     city=betterStr(row['City']),
                     state=state,
                     householdSize=hh_size,
                     inSpreadsheet=1,
                     foodBankId=g.user.id,
                     disabled=disabled,
                     disabledDate=disabledDate)


def disableOutOfRange(cities):
    usersList = conn.execute(users.select().where(and_(
        users.c.foodBankId == g.user.id, users.c.disabled == False, users.c.role == "RECIEVER")))
    for user in usersList:
        disable = True
        print('User: ' + user.name) 
        for city in cities:
            if (not user.city or city in user.city) or (user.formattedAddress and city in user.formattedAddress):
                disable = False
        if disable:
            conn.execute(users.update().where(users.c.id == user.id).values(
                disabled=True, disabledDate=date.today()))


def betterStr(value):
    if value is None or value == "nan":
        return ""
    else:
        return str(value)


def importRoutesList(request, filename, fileType, delete, header):
    print(type(request.files['users']))
    xlFile = pd.ExcelFile(request.files['users'])
    sheets = xlFile.sheet_names
    dfDict = pd.read_excel(
        request.files['users'], sheet_name=sheets, header=header)
    conn.execute(users.update().where(and_(users.c.foodBankId ==
                 g.user.id, users.c.role == "RECIEVER")).values(inSpreadsheet=0))
    for key in dfDict:
        df = dfDict[key]
        for index, row in df.iterrows():
            print(df.columns)
            if type(row['First Name']) != float:
                if type(row['Last Name']) != float:
                    fullName = row['First Name'] + " " + row['Last Name']
                else:
                    fullName = row['First Name']
                if conn.execute(users.select().where(users.c.name == fullName)).fetchone() is not None:
                    conn.execute(users.update().where(
                        users.c.name == fullName).values(inSpreadsheet=1))
                else:
                    conn.execute(users.insert(),
                                 name=str(row['First Name']) +
                                 " " + str(row['Last Name']),
                                 email="",
                                 address=row['Address 1'],
                                 address2=row['Apt'],
                                 role="RECIEVER",
                                 instructions=row['Notes'],
                                 cellPhone=row['Phone Number'],
                                 zipCode=row['Zip'],
                                 city=row['City'],
                                 state=row['State'],
                                 householdSize=-1,
                                 inSpreadsheet=1,
                                 foodBankId=getFoodBank(row['Address 1']))
    if delete:
        conn.execute(users.delete().where(and_(users.c.foodBankId == g.user.id,
                     users.c.role == "RECIEVER", users.c.inSpreadsheet == 0)))


def importFamilyMemberData(request, filename, fileType, delete, header):
    df = pd.DataFrame()
    conn.execute(users.update().where(and_(users.c.foodBankId ==
                 g.user.id, users.c.role == "RECIEVER")).values(inSpreadsheet=0))
    if (fileType == 'csv'):
        df = pd.read_csv(request.files['users'],
                         header=header, keep_default_na=False)
    else:
        print(dir(request.files['users']))
        df = pd.read_excel(request.files['users'].read(
        ), sheet_name="Master list", header=header, keep_default_na=False)
        df = df.dropna(thresh=2)
        print("asdf")
    for index, row in df.iterrows():
        row_rp = conn.execute(users.select().where(users.c.name == betterStr(
            row['First Name']) + " " + betterStr(row['Last Name']))).fetchone()
        if row_rp == None:  # skip people that have been deleted
            continue
        for x in range(1, 16):
            race = row['Person ' + str(x) + ' Race/Ethnicity']
            if race == None or race == '':
                break
            race = race.split(' & ')
            dob = row['Person ' + str(x) + ' date of birth']
            print('Data: ' + str((row['Person ' + str(x) + ' date of birth'])))
            if type(dob) == str:  # This usually happens when someone only enters the last 4 digits of a date, which breaks the date formatting, so we'll just guess if it's post or pre 2000
                # Using 30 for future proofing, if it's post-2030 why are you still using this software
                if int(dob[-2:]) < 30:
                    dob = dob[:-4] + '20' + dob[-2:]
                else:
                    dob = dob[:-4] + '19' + dob[-2:]
                print(dob)
                dob = datetime.strptime(dob, '%m/%d/%Y')

            dob = dob.date()
            conn.execute(family_members.insert().values(
                user=row_rp.id, dob=dob, race=dumps(race)))


@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == "POST":

        form = request.form.to_dict()

        name = fetch_delete('name', form)
        birthday = datetime.strptime(
            fetch_delete('birthday', form), "%Y-%m-%d")
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

        if conn.execute(users.select().where(users.c.email == email)).fetchone() is not None:
            error += '\nUser {} is already registered.'.format(email)

        if error == "":
            password_hash = generate_password_hash(password)
            print("Length of password hash:" + str(len(password_hash)))

            conn.execute(users.insert(), name=name, birthday=birthday, email=email, password=password_hash, address=address,
                         role="RECIEVER", instructions=instructions, cellPhone=cellPhone, homePhone=homePhone,
                         zipCode=zipCode, completed=0, foodBankId=getFoodBank(address), lastDelivered=datetime.today(), restrictions=dumps(restrictions))

            user_id = conn.execute(users.select().where(
                users.c.email == email)).fetchone().id

            for key in list(form):
                if ('name' not in key and 'race' not in key):
                    form.pop(key, None)

            # Get list of keys
            keys = [*form]

            for i in range(0, len(keys), 2):
                conn.execute(family_members.insert(), user=user_id,
                             name=form[keys[i]], race=form[keys[i + 1]])

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
                        'name': query.values(name=given),
                        'email': query.values(email=given),
                        'address': query.values(address=given),
                        'cellPhone': query.values(cellPhone=given),
                        'instructions': query.values(instructions=given),
                        'homePhone': query.values(homePhone=given),
                        'requestPageDescription': query.values(requestPageDescription=given)
                    }[attribute]
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
    family_raw = conn.execute(family_members.select().where(
        g.user.id == family_members.c.user)).fetchall()
    family = []
    for member in family_raw:
        family.append([member[1], member[2]])
    return render_template("auth/changeinfo.html", user=g.user, family_members=family)


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
