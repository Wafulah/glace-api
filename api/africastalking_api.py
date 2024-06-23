import requests
import os
import logging


logger = logging.getLogger(__name__)

AFRICASTALKING_USERNAME = "sandbox"
AFRICASTALKING_API_KEY = os.getenv("AT_API_KEY")
AFRICASTALKING_ENDPOINT = "https://api.sandbox.africastalking.com/version1/messaging"

def send_sms(recipient, message):

    headers = {
        "Authorization": f"Bearer {AFRICASTALKING_API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "to": recipient,
        "from": "70142",  
        "message": message,
    }

    response = requests.post(AFRICASTALKING_ENDPOINT, headers=headers, json=data)
    logger.error("[AFT_POST_RESPONSE] %s", response)
    return response.json()
