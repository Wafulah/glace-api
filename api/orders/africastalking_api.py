import requests
import os
import logging
import xml.etree.ElementTree as ET

"""
Could have used
import africastalking

This Overral Approach offers more flexibility and better debbuging
"""

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
        "message": message,
        "from": 70142,
    }

    response = requests.post(AFRICASTALKING_ENDPOINT, headers=headers, data=data)
    logger.debug("[AFT_POST_RESPONSE_STATUS_CODE] %s", response.status_code)
    logger.debug("[AFT_POST_RESPONSE_HEADERS] %s", response.headers)
    logger.debug("[AFT_POST_RESPONSE_CONTENT] %s", response.content)

    try:
        # Parse XML response
        xml_root = ET.fromstring(response.content)
        message = xml_root.find('SMSMessageData/Message').text
        recipients = xml_root.find('SMSMessageData/Recipients')
        recipient_list = []
        for recipient in recipients.findall('Recipient'):
            recipient_data = {
                'statusCode': int(recipient.find('statusCode').text),
                'number': recipient.find('number').text,
                'cost': recipient.find('cost').text,
                'status': recipient.find('status').text,
                'messageId': recipient.find('messageId').text,
            }
            recipient_list.append(recipient_data)

        result = {
            'Message': message,
            'Recipients': recipient_list,
        }
        return result

    except Exception as e:
        logger.error("[AFT_POST_RESPONSE_XML_PARSE_ERROR] %s", e)
        return {"error": "Error parsing XML response", "content": response.content}