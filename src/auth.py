import functools
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash
from src.db import get_db
from json import loads

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=('GET', 'POST'))
def login():
    redirect_url = request.args.get('redirect_url')
    if redirect_url is None:
        redirect_url = 'index'
    print("Redirect url: " + redirect_url)
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM user WHERE email = ?', (email,)
        ).fetchone()

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
        email = request.form['email']
        print(email)
        password = request.form['password']
        confirm = request.form['confirm']
        address = request.form['address']
        instructions = request.form['instructions']
        cellPhone = request.form['cell']
        homePhone = request.form['homePhone']

        db = get_db()
        error = "" 
        
        if not email:
            error += "Email is required.\n"
        elif not password:
            error += "Password is required.\n"
        elif password != confirm:
            error += "Passwords do not match.\n"
        elif not address:
            error += "Home address is required.\n"
        elif not cellPhone:
            error += "Cell phone is required."
        elif db.execute(
            'SELECT id FROM user WHERE email = ?', (email,)
        ).fetchone() is not None:
            error = 'User {} is already registered.'.format(email)
        
        if error == "":
            db.execute(
                'INSERT INTO user (email, password, address, role, instructions, cellPhone, homePhone, completed) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                (email, generate_password_hash(password), address, "RECEIVER", instructions, cellPhone, homePhone, 0)
            )
            db.commit()
            return redirect(url_for('auth.login'))
        
        flash(error)
    return render_template('auth/register.html', title = 'Register')

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()

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
        'email', 'address', 'cellPhone', 'instructions', 'homePhone'
    }
    if request.method=='POST':
        db = get_db()
        for attribute in request.form:
            if request.form[attribute] != '' and attribute != 'submit' and attribute in attributesList:
                db.execute("UPDATE user SET " + attribute + "= ? WHERE id=?", (request.form[attribute], g.user['id']))
                db.commit()
        return redirect('/youraccount')
    return render_template("auth/changeinfo.html", user=g.user)