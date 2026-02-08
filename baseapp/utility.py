import re
from rest_framework.exceptions import ValidationError

phone_regex = re.compile(r"^\+998[\s-]?\d{2}[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}$")
email_regex = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

def check_email_or_phone(user_input):
    if re.fullmatch(email_regex, user_input):
        user_type = 'email'
    elif re.fullmatch(phone_regex, user_input):
        user_type = 'phone'
        
    else:
        data = {
            'succes': False,
            'msg': 'Email yoki Telefon raqam xato kiritilgan'
            
        }
        
        raise ValidationError(data)
    return user_type



import random
from django.core.mail import send_mail
from django.conf import settings

def send_email_code(email, code):
    """
    Emailga kod yuborish funksiyasi.
    """
    subject = "Ro'yxatdan o'tish kodi"
    message = f"Assalomu alaykum! Sizning tasdiqlash kodingiz: {code}"
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [email]
    
    try:
        send_mail(subject, message, email_from, recipient_list, fail_silently=False)
        print(f"EMAIL SENT TO {email}")
        return True
    except Exception as e:
        print(f"EMAIL ERROR: {e}")
        return False

def send_sms(phone, code):
    print(f"SMS SENT TO {phone} -> CODE: {code}")
    return True