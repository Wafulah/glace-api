# utils.py
import logging
import africastalking
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.db.models import Sum, F, DecimalField
from .models import Product 


logger = logging.getLogger(__name__)

def get_product_details(order_items_data):
    product_details = []
    total_price = 0
    for item_data in order_items_data:
        product_id = item_data.get('product')
        product = get_object_or_404(Product, id=product_id)
        quantity = item_data.get('quantity', 1)
        price = item_data.product.get('price', 0.00)
        product_total_price = quantity * price
        total_price += product_total_price
        product_details.append({
            'name': product.name,
            'quantity': quantity,
            'price': price,
            'total': product_total_price
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

africastalking.initialize(
    username='sandbox',
    api_key='atsk_0ef33ed384195aa69a7331f4321dc1226fe2b77c1377612a817e8a91136c9084f9234b2e'
)


sms = africastalking.SMS

class SendSMS:

    def sending(self, phone, message):
        recipients = [phone]
        sender = "70142"
        
        try:
            response = self.sms.send(message, recipients, sender)
            
        except Exception as e:
           
            logger.error("[SEND_SMS_ERROR] %s", e)
 

