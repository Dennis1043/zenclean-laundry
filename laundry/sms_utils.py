import requests
import urllib3
from django.conf import settings

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def send_sms(phone_number, message):
    """
    Send SMS using Africa's Talking API
    """
    if not settings.SMS_ENABLED:
        print(f"\n{'='*50}")
        print(f"📱 SMS WOULD BE SENT:")
        print(f"   To: {phone_number}")
        print(f"   Message: {message}")
        print(f"{'='*50}\n")
        return True
    
    try:
        phone = phone_number.strip().replace(' ', '').replace('-', '')
        if phone.startswith('0'):
            phone = '254' + phone[1:]
        elif not phone.startswith('254'):
            phone = '254' + phone
        
        # Try different API endpoints
        urls_to_try = [
            "https://api.sandbox.africastalking.com/version1/messaging",
            "http://api.sandbox.africastalking.com/version1/messaging",
        ]
        
        headers = {
            "apiKey": settings.SMS_API_KEY,
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }
        
        data = {
            "username": settings.SMS_USERNAME,
            "to": phone,
            "message": message,
            "from": settings.SMS_SENDER_ID
        }
        
        for url in urls_to_try:
            try:
                response = requests.post(url, headers=headers, data=data, timeout=30, verify=False)
                if response.status_code == 201:
                    print(f"✅ SMS sent successfully to {phone}")
                    return True
            except:
                continue
        
        print(f"❌ SMS failed - all endpoints failed")
        return False
            
    except Exception as e:
        print(f"❌ SMS Error: {str(e)}")
        return False


def send_order_received_sms(customer_name, phone, order_number, total_amount):
    message = f"""🧺 ZenClean Laundry - Order Received

Hi {customer_name},
Order #{order_number}: KSh {total_amount}
Ready in 24 hours. Thank you!"""
    return send_sms(phone, message)


def send_order_ready_sms(customer_name, phone, order_number, total_amount):
    message = f"""✅ ZenClean Laundry - Ready for Pickup

Hi {customer_name},
Order #{order_number} is READY!
Amount: KSh {total_amount}
Please collect. Thank you!"""
    return send_sms(phone, message)


def send_payment_received_sms(customer_name, phone, order_number, amount_paid, balance):
    if balance > 0:
        message = f"""💰 ZenClean Laundry - Payment Received

Hi {customer_name},
KSh {amount_paid} received for order #{order_number}
Remaining: KSh {balance}
Thank you!"""
    else:
        message = f"""✅ ZenClean Laundry - Payment Complete

Hi {customer_name},
Full payment of KSh {amount_paid} received for order #{order_number}
Thank you!"""
    return send_sms(phone, message)