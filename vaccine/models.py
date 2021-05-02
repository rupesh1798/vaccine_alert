from datetime import datetime, timedelta

from pymodm import MongoModel, fields
from pymongo import DESCENDING, IndexModel
from vaccine.managers import UserDetailsManager


class UserDetails(MongoModel):
    '''Model to maintain user details.

    Attributes:
        createdOn: Datetime object
        updatedOn: Datetime object
    '''

    createdOn = fields.DateTimeField(required=True, default=lambda: datetime.now())
    updatedOn = fields.DateTimeField(required=True, default=lambda: datetime.now())
    email = fields.EmailField(required=True, primary_key=False)
    pincode = fields.CharField(required=False, blank=True)
    district = fields.CharField(required=False, blank=True)
    active = fields.BooleanField(required=True, default=False)
    alertCount = fields.IntegerField(required=True, default=0)
    age = fields.IntegerField(required=True)
    objects = UserDetailsManager()

    class Meta:
        collection_name = 'UserDetails'
        indexes = [
            IndexModel(
                [
                    ('pincode', DESCENDING),
                    ('district', DESCENDING)
                ],
                background=True
            )
        ]
        final = True
