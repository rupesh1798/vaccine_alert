from __future__ import absolute_import, unicode_literals

import os
import re
import traceback
import json
from copy import deepcopy
from datetime import date, datetime, timedelta

from bson.objectid import ObjectId
from celery import current_task, shared_task, task, group, chain
from dateutil.relativedelta import relativedelta
from django.conf import settings
from commons.utils.email import Gmail, validate_email, validate_pincode
from vaccine.models import UserDetails
from vaccine.helpers import fetch_calender_by_pin
gmail = Gmail(settings.GMAIL_USER, settings.GMAIL_PASSWORD)


@shared_task()
def send_vaccine_alert(*args, **kwargs):

    pincode_users_map_list = UserDetails.objects.fetch_pincode_emails()
    pincode_chunks = [pincode_users_map_list[x:x+5] for x in range(0, len(pincode_users_map_list), 5)]
    job = group([fetch_vaccine_availability.s(pincode_users_map_sub_list) for pincode_users_map_sub_list in pincode_chunks])

    report_sub_task = _report_task.s()

    chain(job, report_sub_task)()


@shared_task()
def fetch_vaccine_availability(pincode_users_map_sub_list):

    try:
        gmail = Gmail(settings.GMAIL_USER, settings.GMAIL_PASSWORD)

        for pincode_users in pincode_users_map_sub_list:

            user_list_45 = []
            user_list_18 = []
            centre_list_18 = []
            centre_list_45 = []

            all_users = pincode_users.get('userBucket', [])

            for user in all_users:
                if user['age'] >= 45:
                    user_list_45.append(user['email'])
                elif user['age'] >= 18:
                    user_list_18.append(user['email'])

            date_time = datetime.now().strftime("%d-%m-%Y")

            url_params = {
                "pincode": pincode_users.get("_id"),
                "date": date_time
            }

            pincode_availability = fetch_calender_by_pin(url_params)

            for center in pincode_availability.get('centers'):
                for session in center.get('sessions'):
                    if session.get("available_capacity", 0) > 0:
                        if session.get("min_age_limit", 45) > 18:
                            centre_list_18.append(center)
                        centre_list_45.append(center)

            if centre_list_18 and user_list_18:
                for user in user_list_18:
                    gmail.send_message(user, 'IMP-Vaccine Available Alert', f'vaccine available at {json.dumps(centre_list_18, indent=4)}')

            if user_list_18 and centre_list_45:
                for user in user_list_45:
                    gmail.send_message(user, 'IMP-Vaccine Available Alert', f'vaccine available at {json.dumps(centre_list_45, indent=4)}')

    except Exception:
        pass


@shared_task
def _report_task(args):
    pass
