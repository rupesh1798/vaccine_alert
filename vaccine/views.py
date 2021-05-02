from commons.utils.response import OK
from commons.utils.http_error import BadRequest
from django.views.decorators.http import require_http_methods
import json
from vaccine.helpers import fetch_states, fetch_districts, fetch_calender_by_pin, fetch_calender_by_district
from commons.utils.email import Gmail, validate_email, validate_pincode
from commons.utils.otp import otpgen, encrypt, decrypt, authorize_user
from vaccine.models import UserDetails
from vaccine.tasks import send_vaccine_alert
from django.conf import settings


@require_http_methods(["GET"])
def manage_states(request):
    """View to manage states request
    Args:
        request: A Django HttpRequest
    Returns:
        response: states list
    """

    states = fetch_states()
    return OK(states)


@require_http_methods(["GET"])
def manage_districts(request, state_code):
    """View to manage states request
    Args:
        request: A Django HttpRequest
    Returns:
        response: districts list
    """

    districts = fetch_districts(state_code)
    return OK(districts)


@require_http_methods(["GET"])
def calendar_pin(request):
    """View to manage states request
    Args:
        request: A Django HttpRequest
    Returns:
        response: calendar by pin
    """

    url_params = {
        "pincode": request.GET.get('pincode', ''),
        "date": request.GET.get('date', '')
    }

    calendar_pin = fetch_calender_by_pin(url_params)

    return OK(calendar_pin)


@require_http_methods(["GET"])
def calendar_district(request):
    """View to manage states request
    Args:
        request: A Django HttpRequest
    Returns:
        response: calendar by districts
    """

    url_params = {
        "district_id": request.GET.get('district_id', ''),
        "date": request.GET.get('date', '')
    }

    calendar_district = fetch_calender_by_district(url_params)

    return OK(calendar_district)


@require_http_methods(["GET", "POST"])
def auth(request):

    if request.method == 'GET':
        email = request.GET.get('email', '')

        if not email or not validate_email(email):
            raise BadRequest("Invalid Email Address")

        otp = otpgen()

        gmail = Gmail(settings.GMAIL_USER, settings.GMAIL_PASSWORD)
        gmail.send_message(email, 'Vaccine Alert One Time Password', f'Please use OTP - {otp} to register for vaccine alert')

        encrypted_key = encrypt(otp).decode()

        data = {
            'encrypted_key': encrypted_key
        }

        return OK(data)

    if request.method == 'POST':

        body_unicode = request.body.decode('utf-8')
        request_data = json.loads(body_unicode)

        authorize_user(request_data['encrypted_key'], request_data['otp'])
        validate_email(request_data['email'])

        user_details = UserDetails.objects.fetch_user_details(request_data['email'])

        data = {
            "data": {
                "userDetails": user_details
            }
        }

        return OK(data)


@require_http_methods(["POST", "PATCH"])
def register_user(request):

    body_unicode = request.body.decode('utf-8')
    request_data = json.loads(body_unicode)

    authorize_user(request_data['encrypted_key'], request_data['otp'])

    if request.method == 'POST':
        email = request_data['email']
        pincode = request_data.get("pincode")

        if not email or not validate_email(email):
            raise BadRequest("Invalid Email Address")

        user_details = UserDetails.objects.fetch_user_details(email)
        if user_details:
            raise BadRequest("User Alerady registered")

        if pincode and not validate_pincode(pincode):
            raise BadRequest("Invalid Pincode")

        try:

            user_details = {
                "email": request_data['email'],
                "district": request_data.get("district"),
                "pincode": request_data.get("pincode"),
                "age": request_data["age"],
            }

            user_details = UserDetails.objects.insert_user_details(user_details)

        except Exception:
            raise BadRequest("Email, district, pincode, age are required")

        return OK({'data': user_details})

    if request.method == 'PATCH':
        email = request_data['email']
        user_details = UserDetails.objects.fetch_user_details(email)

        if (user_details['active'] == request_data['active'] and user_details.get("pincode", '') == request_data.get("pincode", '') and 
                user_details['age'] == request_data['age'] and user_details.get("district", '') == request_data.get("district", '')):

            raise BadRequest("Nothing to Update")

        if not email or not validate_email(email) or not user_details:
            raise BadRequest("Invalid Email Address")

        if request_data.get("district", '') and validate_pincode(request_data.get("district", '')):
            raise BadRequest("Invalid Pincode")

        try:
            user_details = {
                "district": request_data.get("district"),
                "pincode": request_data.get("pincode"),
                "age": request_data["age"],
                "active": request_data["active"]
            }

            user_details = UserDetails.objects.update_user_details(email, user_details)

        except Exception:
            raise BadRequest("Email, district, pincode, age are required")

        return OK(user_details)
