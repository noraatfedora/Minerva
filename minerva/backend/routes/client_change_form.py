from flask import ( Blueprint, flash, g, redirect, render_template,
    request, session, url_for, Flask, make_response, send_file
)
from werkzeug.exceptions import abort
import usaddress
from json import loads, dumps
from collections import OrderedDict
from minerva.backend.apis import google_maps_qr
from minerva.backend.apis.assign import getUsers
from minerva.backend.apis.db import users, conn, items, routes
from sqlalchemy import and_, select, desc
from fuzzywuzzy import fuzz
from minerva.backend.apis.email import send_recieved_notification, send_bagged_notification
bp = Blueprint('client_change_form', __name__)

@bp.route('/client_form', methods=('GET', 'POST'))
def client_form():
    return render_template('auth/change_form.html', intro_text='Eloise\'s Cooking Pot Delivery Information Update Form')
