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
			<body>
				<p> Your Minerva order has arrived. If you have any questions, respond to this email.</p>
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

def send_bagged_notification(reciever_email, orderId, address, date):
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