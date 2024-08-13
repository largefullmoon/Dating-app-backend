from twilio.rest import Client
import os
account_sid = os.getenv('account_sid')
auth_token = os.getenv('auth_token')
from_number = os.getenv('from_number')
client = Client(account_sid, auth_token)

def send_sms(phone_number, message_body):
    return "ok"
    message = client.messages.create(
        body=message_body,        # The body of the SMS message
        from_=from_number,        # Your Twilio number
        to=phone_number           # The recipient's phone number
    )
    return message.sid  # Return the message SID