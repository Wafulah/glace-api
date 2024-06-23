import requests
import os

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
        "from": "70142",  # Replace with your desired Sender ID
        "message": message,
    }

    response = requests.post(AFRICASTALKING_ENDPOINT, headers=headers, json=data)
    return response.json()
