# Create a file called email_password with your email password in it for development.

import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

port = 465
password = open("src/email_password").read()
sender_email = "contactusminerva@gmail.com"

def send_request_conformation(reciever_email, items):

  context = ssl.create_default_context()
  message = MIMEMultipart("alternative")
  message["Subject"] = "Minerva order conformation"
  message["From"] = sender_email
  message["To"] = reciever_email
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

  print(html)
  message.attach(MIMEText(html, "html"))

  with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
      server.login(sender_email, password)
      server.sendmail(sender_email, reciever_email, message.as_string())

