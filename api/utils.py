import logging
import os

from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
import vonage

from .models import Product

logger = logging.getLogger(__name__)

def get_product_details(order_items_data):
    """
    Format data to send to the customer after an order is successfully placed.
    
    Args:
        order_items_data (list): List of dictionaries containing order item data.
        
    Returns:
        list: Formatted product details.
        float: Total price of the order.
    """
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
    
    Args:
        user_info (dict): Dictionary containing user information from Google.
        
    Returns:
        User: The created or updated user instance.
    """
    email = user_info.get('email')
    first_name = user_info.get('given_name')
    last_name = user_info.get('family_name')
    sub = user_info.get('sub')

    user, created = User.objects.update_or_create(
        email=email,
        defaults={
            'first_name': first_name,
            'last_name': last_name,
            'username': sub,
        }
    )

    subject = "Welcome to Glace"
    message = (
        f"Dear {first_name} {last_name},\n"
        f"We are thrilled to welcome you as part of our community here at Glace!\n"
        f"Your username is: {sub}\n"
        f"Glace, your Health care partner!"
    )
    send_email(message, subject, email)
    return user

class SendSMS:
    """
    Use Vonage to send SMS messages. Ensure the service is configured correctly.
    """
    def __init__(self):
        api_key = os.getenv("VONAGE_API_KEY")
        api_secret = os.getenv("VONAGE_API_SECRET")
        self.client = vonage.Client(key=api_key, secret=api_secret)
        self.sms = vonage.Sms(self.client)

    def send_message(self, phone, message):
        """
        Send an SMS message.
        
        Args:
            phone (str): The recipient's phone number.
            message (str): The message to send.
        """
        response_data = self.sms.send_message({
            "from": "Vonage APIs",
            "to": phone,
            "text": message,
        })

        if response_data["messages"][0]["status"] == "0":
            logger.info("Message sent successfully.")
        else:
            logger.error("Message failed with error: %s", response_data["messages"][0]["error-text"])

def send_email(message, subject, recipient):
    """
    Send email notifications to users.
    
    Args:
        message (str): The email message content.
        subject (str): The email subject.
        recipient (str): The recipient's email address.
    """
    from_email = os.getenv('EMAIL_HOST_USER')
    recipient_list = [recipient]
    
    email_password = os.getenv('EMAIL_HOST_PASSWORD')
    logger.error("Deatails Email to %s: %s", recipient_list,from_email, email_password)
    try:
        send_mail(subject, message, from_email, recipient_list)
        logger.info("Email sent successfully to %s", recipient)
    except Exception as e:
        logger.error("Failed to send email to %s: %s", recipient, e)
