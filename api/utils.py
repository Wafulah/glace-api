# utils.py
import logging
import africastalking
import os
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.db.models import Sum, F, DecimalField
import vonage
from .models import Product 


logger = logging.getLogger(__name__)

def get_product_details(order_items_data,store):
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
            'store': store.name
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
    return user

# africastalking.initialize(
#     username='sandbox',
#     api_key='atsk_0ef33ed384195aa69a7331f4321dc1226fe2b77c1377612a817e8a91136c9084f9234b2e'
# )



# sms = africastalking.SMS

# class SendSMS:
#     def __init__(self):
#         # Initialize the SMS service
#         self.sms = africastalking.SMS

#     def sending(self, phone, message):
#         recipients = [phone]
#         sender = "70142"
        
#         try:
#             response = self.sms.send(message, recipients, sender)
            
#         except Exception as e:
           
#             logger.error("[SEND_SMS_ERROR] %s", e)



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


