import requests
from requests.auth import HTTPBasicAuth
import datetime
import base64

# M-Pesa credentials
consumer_key = 'jfwlVsN2rEvuDTffw790ZqbLymXgHRP4eVnO3NrvLyMOzzae'
consumer_secret = 'RrEhBk5VGpAL7NHFyiqr1gHnQHYgxMBv1RrQUWCBsAuGLf9wTG2l8KM1ZNwZZiSO'
shortcode = '174379'
passkey = 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919'
callback_url = 'https://your-domain.com/mpesa/callback'

def generate_oauth_token():
    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    response = requests.get(url, auth=HTTPBasicAuth(consumer_key, consumer_secret))
    json_response = response.json()
    return json_response['access_token']

def generate_password():
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    data_to_encode = shortcode + passkey + timestamp
    encoded_string = base64.b64encode(data_to_encode.encode())
    return encoded_string.decode('utf-8'), timestamp

def stk_push_request(phone_number, amount):
    access_token = generate_oauth_token()
    password, timestamp = generate_password()
    
    url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    headers = {
        "Authorization": "Bearer " + access_token
    }
    payload = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone_number,  # This is the phone number of the customer making the payment
        "PartyB": shortcode,
        "PhoneNumber": phone_number,
        "CallBackURL": callback_url,
        "AccountReference": "SaleTransaction",
        "TransactionDesc": "Payment for book"
    }

    response = requests.post(url, json=payload, headers=headers)
    return response.json()
