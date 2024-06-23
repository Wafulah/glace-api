import requests
import os
import logging


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

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
    logger.debug("[AFT_POST_RESPONSE_STATUS_CODE] %s", response.status_code)
    logger.debug("[AFT_POST_RESPONSE_HEADERS] %s", response.headers)
    logger.debug("[AFT_POST_RESPONSE_CONTENT] %s", response.content)

    try:
        response_json = response.json()
        logger.debug("[AFT_POST_RESPONSE_JSON] %s", response_json)
        return response_json
    except ValueError as e:
        logger.error("[AFT_POST_RESPONSE_JSON_ERROR] %s", e)
        return {"error": "Invalid JSON response", "content": response.content}