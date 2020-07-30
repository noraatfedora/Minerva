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
	html = openHTML() + """
		<!-- H1 -->
			<tr>
				<td class="h1" align="left" bgcolor="#FFFFFF" style="padding-top: 50px; padding-right: 50px; padding-bottom: 20px; padding-left: 50px; font-size: 36px; line-height: 44px; font-weight: 700; text-align: left; color: #37393a;" >
					Order Confirmation
				</td>
			</tr>

		<!-- H2 -->
			<tr>
				<td class="h2" align="left" bgcolor="#FFFFFF" style="padding-top: 0px; padding-right: 50px; padding-bottom: 20px; padding-left: 50px; font-size: 18px; line-height: 27px; font-weight: 700; text-align: left; color: #a2c3a4;" >
				You have requested the following items from Minerva:
				</td>
			</tr>
			<p>
			<ul>

		<!-- PARAGRAPH -->
			<tr>
				<td class="p" align="left" bgcolor="#FFFFFF" style="padding-top: 0px; padding-right: 50px; padding-bottom: 50px; padding-left: 50px; font-size: 16px; line-height: 24px; font-weight: 400; text-align: left; color: ##37393a;">
	""" 
	for item in items.keys():
			if (int(items[item]) > 0):
					html += "<li>" + items[item] + " orders of " + item + "</li>"
	html += "<br> A volunteer should deliver within the next week or two. If you have any questions, respond to this email."
	html += """
			</td>
		</tr>
	""" + endHTML()
	send_email(to = reciever_email, contents = html, subject = "Your Minerva order confirmation")

def send_recieved_notification(reciever_email):
	html = openHTML() + """
	<!-- H1 -->
		<tr>
			<td class="h1" align="left" bgcolor="#FFFFFF" style="padding-top: 50px; padding-right: 50px; padding-bottom: 20px; padding-left: 50px; font-size: 36px; line-height: 44px; font-weight: 700; text-align: left; color: #37393a;" >
				Your Minerva order has arrived!
			</td>
		</tr>

	<!-- H2 -->
		<tr>
			<td class="h2" align="left" bgcolor="#FFFFFF" style="padding-top: 0px; padding-right: 50px; padding-bottom: 20px; padding-left: 50px; font-size: 18px; line-height: 27px; font-weight: 700; text-align: left; color: #a2c3a4;" >
				Thank you for ordering with us. Please reply to this email or notify your foodbank if you have any questions.
			</td>
		</tr>
	""" + endHTML()
	send_email(to = reciever_email, contents = html, subject = "Your Minerva order is here")

def send_new_volunteer_request_notification(reciever_email, name):
	html = openHTML() + """
	<!-- H1 -->
		<tr>
			<td class="h1" align="left" bgcolor="#FFFFFF" style="padding-top: 50px; padding-right: 50px; padding-bottom: 20px; padding-left: 50px; font-size: 36px; line-height: 44px; font-weight: 700; text-align: left; color: #37393a;" >
				A volunteer has requested to join you! 
			</td>
		</tr>

	<!-- H2 -->
		<tr>
			<td class="h2" align="left" bgcolor="#FFFFFF" style="padding-top: 0px; padding-right: 50px; padding-bottom: 20px; padding-left: 50px; font-size: 18px; line-height: 27px; font-weight: 700; text-align: left; color: #a2c3a4;" >
				""" + name + """ has requested to join your organization. Visit the volunteer settings dashboard to aprove them.
			</td>
		</tr>

	<!-- CTA -->
		<tr>
			<td class="CTA_wrap" bgcolor="#FFFFFF" align="left" style="padding-top:0px; padding-bottom: 50px; padding-right: 50px; padding-left: 50px;">
				<table border="0" cellspacing="0" cellpadding="0" align="left">
					<!-- // BUTTON -->
						<tr>
							<td class="CTA" align="left" style="border-radius: 0px; padding-top: 15px; padding-right: 20px; padding-bottom: 15px; padding-left: 20px;" bgcolor="#77b6ea"><a href="https://minervagroceries.org/modify" target="_blank" style="color: #FFFFFF; font-size: 16px; font-weight: 700; text-align: center; text-decoration: none; border-radius: 0px;  display: inline-block;">View Request</a>
							</td>
						</tr>
					<!-- BUTTON // -->
				</table>
			</td>
		</tr>
	""" + endHTML()

def send_volunteer_acceptance_notification(reciever_email, food_bank_name):
	html = openHTML() + """
	<!-- H1 -->
		<tr>
			<td class="h1" align="left" bgcolor="#FFFFFF" style="padding-top: 50px; padding-right: 50px; padding-bottom: 20px; padding-left: 50px; font-size: 36px; line-height: 44px; font-weight: 700; text-align: left; color: #37393a;" >
				Welcome to the team!
			</td>
		</tr>

	<!-- H2 -->
		<tr>
			<td class="h2" align="left" bgcolor="#FFFFFF" style="padding-top: 0px; padding-right: 50px; padding-bottom: 20px; padding-left: 50px; font-size: 18px; line-height: 27px; font-weight: 700; text-align: left; color: #a2c3a4;" >
				Congratulations! You have been accepted by """ + food_bank_name + """ for Minerva.	
			</td>
		</tr>

	<!-- CTA -->
		<tr>
			<td class="CTA_wrap" bgcolor="#FFFFFF" align="left" style="padding-top:0px; padding-bottom: 50px; padding-right: 50px; padding-left: 50px;">
				<table border="0" cellspacing="0" cellpadding="0" align="left">
					<!-- // BUTTON -->
						<tr>
							<td class="CTA" align="left" style="border-radius: 0px; padding-top: 15px; padding-right: 20px; padding-bottom: 15px; padding-left: 20px;" bgcolor="#77b6ea"><a href="https://minervagroceries.org/dashboard" target="_blank" style="color: #FFFFFF; font-size: 16px; font-weight: 700; text-align: center; text-decoration: none; border-radius: 0px;  display: inline-block;">Start Serving</a>
							</td>
						</tr>
					<!-- BUTTON // -->
				</table>
			</td>
		</tr>
	""" + endHTML()
	send_email(to = reciever_email, contents=html, subject="Minerva: " + food_bank_name + " has accepted you into their organization")

def send_bagged_notification(reciever_email, orderId, address):
	html = openHTML() + """
	<!-- H1 -->
		<tr>
			<td class="h1" align="left" bgcolor="#FFFFFF" style="padding-top: 50px; padding-right: 50px; padding-bottom: 20px; padding-left: 50px; font-size: 36px; line-height: 44px; font-weight: 700; text-align: left; color: #37393a;" >
				You have been assigned a new order!
			</td>
		</tr>

	<!-- H2 -->
		<tr>
			<td class="h2" align="left" bgcolor="#FFFFFF" style="padding-top: 0px; padding-right: 50px; padding-bottom: 20px; padding-left: 50px; font-size: 18px; line-height: 27px; font-weight: 700; text-align: left; color: #a2c3a4;" >
				<li> Order ID: """ + str(orderId) + """ </li>
				<li> Delivery address: """ + address + """ </li>
			</td>
		</tr>
	<!-- PARAGRAPH -->
		<tr>
			<td class="p" align="left" bgcolor="#FFFFFF" style="padding-top: 0px; padding-right: 50px; padding-bottom: 50px; padding-left: 50px; font-size: 16px; line-height: 24px; font-weight: 400; text-align: left; color: ##37393a;">
				Please pick this up as soon as possible when available. Your food bank may have restrictions on when you can pick up your order from them. Make sure to be aware of their hours so you can pick up the order and deliver on time.
				Thank you for volunteering! Reply with any questions related to Minerva software, and contact your food bank for any questions about the order.
			</td>
		</tr>
	""" + endHTML()
	send_email(to = reciever_email, contents=html, subject="Minerva: You have been assigned a new order")

def openHTML():
	return """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
			<html xmlns="http://www.w3.org/1999/xhtml">
			<head>
				<title>Minerva Email</title>

				<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
				<meta name="x-apple-disable-message-reformatting" />
				<meta name="viewport" content="width=device-width, initial-scale=1.0" />

				<style type="text/css">
					/* Google font import Lato */
					@import url('https://fonts.googleapis.com/css?family=Lato:400,700&display=swap');

					/* Outlook link fix */
					#outlook a {
						padding: 0;
					}

					/* Hotmail background & line height fixes */
					.ExternalClass {
						width: 100% !important;
					}

					.ExternalClass,
					.ExternalClass p,
					.ExternalClass span,
					.ExternalClass font,
					/* Image borders & formatting */
					img {
						outline: none;
						text-decoration: none;
						-ms-interpolation-mode: bicubic;
					}

					a img {
						border: none;
					}

					/* Re-style iPhone automatic links (eg. phone numbers) */
					
					.appleLinksGrey a {
						color: #919191 !important;
						text-decoration: none !important;
					}

					/* Hotmail symbol fix for mobile devices */
					.ExternalClass img[class^=Emoji] {
						width: 10px !important;
						height: 10px !important;
						display: inline !important;
					}
					
					/* Button hover colour change */
					.CTA:hover {
						background-color: #5FDBC4 !important;
					}


					@media screen and (max-width:640px) {
						.mobilefullwidth {
							width: 100% !important;
							height: auto !important;
						}

						.logo {
							padding-left: 30px !important;
							padding-right: 30px !important;
						}

						.h1 {
							font-size: 36px !important;
							line-height: 48px !important;
							padding-right: 30px !important;
							padding-left: 30px !important;
							padding-top: 30px !important;
						}

						.h2 {
							font-size: 18px !important;
							line-height: 27px !important;
							padding-right: 30px !important;
							padding-left: 30px !important;
						}

						.p {
							font-size: 16px !important;
							line-height: 28px !important;
							padding-left: 30px !important;
							padding-right: 30px !important;
							padding-bottom: 30px !important;
						}

						.CTA_wrap {
							padding-left: 30px !important;
							padding-right: 30px !important;
							padding-bottom: 30px !important;
						}

						.footer {
							padding-left: 30px !important;
							padding-right: 30px !important;
						}

						.number_wrap {
							padding-left: 30px !important;
							padding-right: 30px !important;
						}

						.unsubscribe {
							padding-left: 30px !important;
							padding-right: 30px !important;
						}
				
					}

				</style>
				<meta name="viewport" content="width=device-width, initial-scale=1.0" />
			</head>

			<body style="padding:0; margin:0; -webkit-text-size-adjust:none; -ms-text-size-adjust:100%; background-color:#e8e8e8; font-family: 'Lato', sans-serif; font-size:16px; line-height:24px; color:#919191">

			<!--[if mso]>
				<style type="text/css">
					body, table, td {font-family: Arial, Helvetica, sans-serif !important;}
				</style>
			<![endif]-->


			<!-- // FULL EMAIL -->
			<table width="100%" border="0" cellspacing="0" cellpadding="0">
				<tr>

					<!-- // LEFT SPACER CELL *** MUST HAVE A BACKGROUND COLOUR -->
					<td bgcolor="#EBEBEB" style="font-size:0px">&zwnj;</td>
					<!-- LEFT SPACER CELL // -->

						<!-- // MAIN CONTENT CELL -->
						<td align="center" width="600" bgcolor="#FFFFFF">


							<table width="100%" border="0" cellspacing="0" cellpadding="0">
								<tbody>
									<!-- START OF CONTENT EDIT -->

									<!-- LOGO -->
									<tr>
										<td class="logo" align="left" bgcolor="#77b6ea" style="padding-top: 20px; padding-right: 50px; padding-bottom: 20px; padding-left: 50px;"><img src="https://drive.google.com/uc?export=view&id=1fVw7wuFApMSJ-OWO-_9WwRhmllFJ9DlQ" width="50" height="auto" border="0" alt="Peak Logo"/></td>
									</tr>
	 """

def endHTML():
	return """
						</tbody>
					</table>
				</td>
				<!-- // MAIN CONTENT CELL -->
			<!-- // RIGHT SPACER CELL *** MUST HAVE A BACKGROUND COLOUR -->
			<td bgcolor="#EBEBEB" style="font-size:0px">&zwnj;</td>
			<!-- RIGHT SPACER CELL // -->

		</tr>
	</table>
	<!-- FULL EMAIL // -->
	</body>
	</html>
	"""
