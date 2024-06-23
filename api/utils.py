# utils.py
import africastalking
from django.contrib.auth.models import User

def create_or_update_user(user_info):
    """
    Create or update a user based on the information obtained from Google.
    """
    email = user_info.get('email')
    first_name = user_info.get('given_name')
    last_name = user_info.get('family_name')
    sub=user_info.get('sub')

    user, created = User.objects.update_or_create(
        email=email,
        defaults={
            'first_name': first_name,
            'last_name': last_name,
            'username': sub,
        }
    )
    return user

africastalking.initialize(
    username='sandbox',
    api_key='atsk_0ef33ed384195aa69a7331f4321dc1226fe2b77c1377612a817e8a91136c9084f9234b2e'
)


sms = africastalking.SMS

class SendSMS:
    def __init__(self):
        self.sms = sms

    def sending(self, phone, message):
        recipients = [phone]
        sender = "70142"
        try:
            response = self.sms.send(message, recipients, sender)
            print(response)
        except Exception as e:
            print(f'Houston, we have a problem: {e}')
 

