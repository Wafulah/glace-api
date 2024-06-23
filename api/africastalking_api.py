import requests
import os
import logging


logger = logging.getLogger(__name__)

AFRICASTALKING_USERNAME = "sandbox"
AFRICASTALKING_API_KEY = os.getenv("AT_API_KEY")
AFRICASTALKING_ENDPOINT = "https://api.sandbox.africastalking.com/version1/messaging"
def send_sms(recipient, message):

    headers = {
        "apiKey": AFRICASTALKING_API_KEY,
        "Content-Type": "application/x-www-form-urlencoded",
    }

    data = {
        "username": AFRICASTALKING_USERNAME,
        "to": recipient,
        "from": "70142",
        "message": message,
    }

    response = requests.post(AFRICASTALKING_ENDPOINT, headers=headers, data=data)
    logger.error("[AFT_POST_RESPONSE] %s", response)
    return response.json()