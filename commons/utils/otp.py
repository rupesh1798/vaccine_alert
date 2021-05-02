import time
from datetime import datetime
from random import randint
from commons.utils.http_error import Unauthorized
from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings


def otpgen():

    otp = randint(1000, 9999)
    return otp


def encrypt(message, key=settings.ENCRYPTION_KEY.encode()):

    return Fernet(key).encrypt_at_time(str(message).encode(), int(time.time()))


def decrypt(token, key=settings.ENCRYPTION_KEY.encode()):

    token = token.encode()

    return Fernet(key).decrypt_at_time(token, 1200, int(time.time())).decode()


def authorize_user(encrypted_key, otp):
    try:
        _otp = decrypt(encrypted_key)

        if not int(_otp) == otp:
            raise BadRequest("Invalid OTP Please try again")

    except InvalidToken:
        raise Unauthorized
