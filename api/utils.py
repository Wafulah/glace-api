# utils.py
import logging

import os
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
import vonage
from .models import Product 


logger = logging.getLogger(__name__)

def get_product_details(order_items_data):
    product_details = []
    total_price = 0
    for item_data in order_items_data:
        product_id = item_data.get('product')
        product = get_object_or_404(Product, id=product_id)
        quantity = item_data.get('quantity', 1)
        price = product.price
        product_total_price = quantity * price
        total_price += product_total_price
        product_details.append({
            'name': product.name,
            'quantity': quantity,
            'price': price,
            'total': product_total_price,
            })
    return product_details, total_price


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
    message = (
                f"Dear {first_name}, {last_name} \n"
                f"We are thrilled to welcome you as part of our community here at Glace!\n"
                f"Your username is : {sub}\n"
                f"Glace your Health care partner!"
            )
    subject = "Welcome to Glace"
    recipient= email
    send_email(message,subject,recipient)
    return user


#This service has a limited plan that sends actually sms,the trial amount maybe over when you are accessing this
client = vonage.Client(key=os.getenv("VONAGE_API_KEY"), secret=os.getenv("VONAGE_API_SECRET"))
sms = vonage.Sms(client)

class SendSMS:
    def __init__(self):
        # Initialize the SMS service using environment variables
        api_key = os.getenv("VONAGE_API_KEY")
        api_secret = os.getenv("VONAGE_API_SECRET")
        self.client = vonage.Client(key=api_key, secret=api_secret)
        self.sms = vonage.Sms(self.client)

    def send_message(self, phone, message):
        responseData = self.sms.send_message(
            {
                "from": "Vonage APIs",
                "to": phone,
                "text": message,
            }
        )

        if responseData["messages"][0]["status"] == "0":
            logger.info("Message sent successfully.")
        else:
            logger.error("Message failed with error: %s", responseData['messages'][0]['error-text'])


def send_email(message,subject,recipient):
    from_email = os.getenv('EMAIL_HOST_USER')

    recipient_list = [recipient]

    send_mail(subject, message, from_email, recipient_list)