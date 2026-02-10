"""
Paystack Payment Service
Handles payment initialization and verification via Paystack API.
"""
import requests
import uuid
from django.conf import settings


PAYSTACK_BASE_URL = "https://api.paystack.co"


def get_headers():
    """Return authorization headers for Paystack API."""
    return {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }


def generate_reference():
    """Generate a unique payment reference."""
    return f"EV-{uuid.uuid4().hex[:12].upper()}"


def initialize_payment(email: str, amount_kobo: int, reference: str, metadata: dict = None) -> dict:
    """
    Initialize a Paystack transaction.
    
    Args:
        email: Customer email address
        amount_kobo: Amount in kobo (100 kobo = ₦1)
        reference: Unique payment reference
        metadata: Optional metadata dict
    
    Returns:
        dict with 'authorization_url', 'access_code', 'reference'
        or dict with 'error' key on failure
    """
    url = f"{PAYSTACK_BASE_URL}/transaction/initialize"
    
    payload = {
        "email": email,
        "amount": amount_kobo,
        "reference": reference,
        "currency": "NGN",
        "channels": ["card", "bank", "ussd", "bank_transfer"],
    }
    
    if metadata:
        payload["metadata"] = metadata
    
    try:
        response = requests.post(url, json=payload, headers=get_headers(), timeout=30)
        data = response.json()
        
        if data.get("status"):
            return {
                "success": True,
                "authorization_url": data["data"]["authorization_url"],
                "access_code": data["data"]["access_code"],
                "reference": data["data"]["reference"],
            }
        else:
            return {"success": False, "error": data.get("message", "Unknown error")}
    
    except requests.RequestException as e:
        return {"success": False, "error": str(e)}


def verify_payment(reference: str) -> dict:
    """
    Verify a Paystack transaction.
    
    Args:
        reference: Payment reference to verify
    
    Returns:
        dict with payment status and details
    """
    url = f"{PAYSTACK_BASE_URL}/transaction/verify/{reference}"
    
    try:
        response = requests.get(url, headers=get_headers(), timeout=30)
        data = response.json()
        
        if data.get("status"):
            tx_data = data["data"]
            return {
                "success": True,
                "status": tx_data["status"],  # 'success', 'failed', 'abandoned'
                "amount": tx_data["amount"],
                "reference": tx_data["reference"],
                "paid_at": tx_data.get("paid_at"),
                "channel": tx_data.get("channel"),
                "data": tx_data,
            }
        else:
            return {"success": False, "error": data.get("message", "Unknown error")}
    
    except requests.RequestException as e:
        return {"success": False, "error": str(e)}
