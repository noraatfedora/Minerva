import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import set_environment_variables

message = Mail(
    from_email='contactusminerva@gmail.com',
    to_emails='jaredgoodman03@gmail.com',
    subject='Sending with Twilio SendGrid is Fun',
    html_content='<strong>and easy to do anywhere, even with Python</strong>')
print("message: " + str(message))
try:
    print("API key: " + os.environ.get('SENDGRID_API_KEY'))
    sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
    response = sg.send(message)
    print(response.status_code)
    print(response.body)
    print(response.headers)
except Exception as e:
    print(e.message)