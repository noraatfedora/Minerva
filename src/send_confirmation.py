# Create a file called email_password with your email password in it for development.

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys
from os import environ

port = 465
password = environ['EMAIL_PASSWORD']
sender_email = environ['EMAIL_SENDER']


def send_email(reciever_email, html, subject):
	context = ssl.create_default_context()
	message = MIMEMultipart("alternative")
	message["Subject"] = "Minerva order confirmation"
	message["From"] = sender_email
	message["To"] = reciever_email

	print(html)
	message.attach(MIMEText(html, "html"))

	with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
			server.login(sender_email, password)
			server.sendmail(sender_email, reciever_email, message.as_string())


def send_request_confirmation(reciever_email, items):
	html = """\
	<html>
		<body>
			<p>You have requested the following items from Minerva:<br>
			<ul>
	"""
	for item in items.keys():
			if (int(items[item]) > 0):
					html += "<li>" + items[item] + " orders of " + item + "</li>"
			html += """
			</ul>
			</p>
		</body>
	</html>
	"""
	send_email(reciever_email, html, "Your Minerva Order confirmation")

def send_recieved_notification(reciever_email):
	html = """
		<html>
			<body>
				<p> Your Minerva order has arrived. If you have any questions, respond to this email.</p>
			</body>
		</html>
	"""
	send_email(reciever_email, html, "Your Minerva Order Is Here")
