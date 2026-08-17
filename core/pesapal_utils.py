import json
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

def get_pesapal_bearer_token():
    """
    Fetches Pesapal API v3 Bearer Token using Consumer Key & Consumer Secret.
    Endpoint: POST /api/Auth/RequestToken
    """
    url = f"{settings.PESAPAL_BASE_URL}/api/Auth/RequestToken"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    payload = {
        "consumer_key": settings.PESAPAL_CONSUMER_KEY,
        "consumer_secret": settings.PESAPAL_CONSUMER_SECRET
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        res_data = response.json()
        if response.status_code == 200 and "token" in res_data:
            return res_data["token"], None
        error_msg = res_data.get("error", {}).get("message") or res_data.get("message") or f"HTTP {response.status_code}"
        return None, error_msg
    except Exception as e:
        logger.error(f"Pesapal RequestToken Exception: {str(e)}")
        return None, str(e)


def register_pesapal_ipn(token):
    """
    Registers IPN URL with Pesapal API v3 to receive async payment notifications.
    Endpoint: POST /api/URLSetup/RegisterIPN
    """
    url = f"{settings.PESAPAL_BASE_URL}/api/URLSetup/RegisterIPN"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    payload = {
        "url": settings.PESAPAL_IPN_URL,
        "ipn_notification_type": "GET"
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        res_data = response.json()
        if response.status_code == 200 and "ipn_id" in res_data:
            return res_data["ipn_id"], None
        return None, f"IPN Registration Failed: {response.text}"
    except Exception as e:
        logger.error(f"Pesapal RegisterIPN Exception: {str(e)}")
        return None, str(e)


def submit_pesapal_order(merchant_reference, amount, description, customer_email, customer_phone, customer_first_name, customer_last_name, callback_url, token, ipn_id=None):
    """
    Submits a payment order request to Pesapal API v3.
    Endpoint: POST /api/Transactions/SubmitOrderRequest
    Returns: redirect_url, order_tracking_id, error
    """
    url = f"{settings.PESAPAL_BASE_URL}/api/Transactions/SubmitOrderRequest"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    # Ensure phone number format
    clean_phone = customer_phone or ""
    if not clean_phone.startswith("+") and not clean_phone.startswith("07"):
        clean_phone = f"0{clean_phone}"

    payload = {
        "id": merchant_reference,
        "currency": getattr(settings, 'PESAPAL_CURRENCY', 'UGX'),
        "amount": float(amount),
        "description": description,
        "callback_url": callback_url,
        "notification_id": ipn_id,
        "billing_address": {
            "email_address": customer_email or "tenant@trustrentug.com",
            "phone_number": clean_phone or "0700000000",
            "first_name": customer_first_name or "TRUST",
            "last_name": customer_last_name or "Client",
            "country_code": "UG"
        }
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=20)
        res_data = response.json()
        if response.status_code == 200 and "redirect_url" in res_data:
            return res_data["redirect_url"], res_data.get("order_tracking_id"), None
        error_msg = res_data.get("error", {}).get("message") or res_data.get("message") or f"HTTP {response.status_code}"
        return None, None, error_msg
    except Exception as e:
        logger.error(f"Pesapal SubmitOrderRequest Exception: {str(e)}")
        return None, None, str(e)


def get_pesapal_transaction_status(order_tracking_id, token):
    """
    Queries Pesapal API v3 for transaction verification status.
    Endpoint: GET /api/Transactions/GetTransactionStatus?orderTrackingId={orderTrackingId}
    Returns: status_dict, error
    """
    url = f"{settings.PESAPAL_BASE_URL}/api/Transactions/GetTransactionStatus?orderTrackingId={orderTrackingId}"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        res_data = response.json()
        if response.status_code == 200:
            return res_data, None
        return None, f"GetTransactionStatus Failed: {response.text}"
    except Exception as e:
        logger.error(f"Pesapal GetTransactionStatus Exception: {str(e)}")
        return None, str(e)
