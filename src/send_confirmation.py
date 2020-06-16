# Create a file called email_password with your email password in it for development.

import yagmail
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys
from datetime import datetime
from os import environ

password = environ['EMAIL_PASSWORD']
sender_email = environ['EMAIL_SENDER']
yag = yagmail.SMTP(sender_email, password)

def send_email(subject, contents, to):
	print("To: " + str(to))
	yag.send(to = to, subject= subject, contents = [contents])

def send_request_confirmation(reciever_email, items, date):
	html = """
	<html>
		<body>
			<p>You have requested the following items from Minerva:
			<ul>
	"""
	for item in items.keys():
			if (int(items[item]) > 0):
					html += "<li>" + items[item] + " orders of " + item + "</li>"
	html += "</ul> A volunteer should deliver within the next week or two. If you have any questions, respond to this email. </p> </body> </html>"
	send_email(to = reciever_email, contents = html, subject = "Your Minerva Order confirmation")

def send_recieved_notification(reciever_email):
	html = """
		<html>
    <head>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@500;700&display=swap');
            @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@500');
            @import url('https://fonts.googleapis.com/css2?family=Pacifico&display=swap');
            body {
                margin-left: auto;
                margin-right: auto;
                width: 40em;
            }

            h1 {
                position:relative;
            
                font-size: 40px;
                font-family: 'Noto Sans TC', sans-serif;
            }

            .meat-text {
                font-size: 18px;
                font-family: 'Montserrat', sans-serif;
            }

            #logo-text {
                font-family: 'Pacifico', cursive;
                position:relative;
                top:10px;
                font-size:25px;
            }
        </style>
    </head>
    <body>
        <img id = "logo" align = "left"  src="https://drive.google.com/uc?export=view&id=1JPAYyTTclCvrJhatLlk4zmmPi-6LBeJZ" alt = "logo" height = "60px" width = "60px"/> 
        <p id = "logo-text">Minerva</p>
        <h1>And... Delivered!</h1>
        <p class = "meat-text"> Your Minerva order has arrived! If you have any questions, respond to this email.</p>
        <hr>
    </body>
</html>
	"""
	send_email(to = reciever_email, contents = html, subject = "Your Minerva order is here")

def send_new_volunteer_request_notification(reciever_email, name):
	html = """
		<html>
			<body>
				<p>""" + name + """ has requested to join your organization. Visit the <a href="https://minervagroceries.org/modify">
				volunteer settings dashboard</a> to aprove them."""
	send_email(to = reciever_email, contents=html, subject="Minerva: " + name + " has requested to join your organization")

def send_volunteer_acceptance_notification(reciever_email, food_bank_name):
	html = """
		<html>
			<body>
				<p> You have been accepted by """ + food_bank_name + """ for Minerva."""
	send_email(to = reciever_email, contents=html, subject="Minerva: " + food_bank_name + " has accepted you into their organization")

def send_bagged_notification(reciever_email, orderId, address):
	html = """
		<html>
			<body>
				<h2>You have been assigned a new order!</h2> <ul>
					<li> Order ID: """ + str(orderId) + """ </li>
					<li> Delivery address: """ + address + """ </li>
				</ul>
				Please pick this up as soon as possible when available. Your food bank may have restrictions on when you can pick up your order from them. Make sure to be aware of their hours so you can pick up the order and deliver on time.
				Thank you for volunteering! Reply with any questions related to Minerva software, and contact your food bank for any questions about the order.
			</body>
		</html>
				"""
	send_email(to = reciever_email, contents=html, subject="Minerva: You have been assigned a new order")