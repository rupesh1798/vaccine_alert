from datetime import datetime, timedelta
from bson.objectid import ObjectId
from commons.utils.default_model_manager import DefaultManager
from pymongo import ReturnDocument


class UserDetailsManager(DefaultManager):
    def insert_user_details(self, user_details):

        user_details.update({
            'active': True,
            'alertCount': 0
        })
        try:
            doc = self.model.objects.insert_one(user_details)
        except Exception as e:
            print(e)
        return doc

    def fetch_pincode_emails(self):
        pipeline = [
            {
                '$match': {
                    'active': True,
                    'alertCount': {'$lt': 5}
                }
            },
            {
                '$project': {
                    '_id': 0
                }
            },
            {
                '$sort': {
                    'updatedOn': -1,
                    'createdOn': -1
                }
            },
            {
                '$group': {
                    '_id': '$pincode',
                    'userBucket': {"$push": "$$ROOT"}
                }
            }
        ]
        pincode_email_map = list(self.model.objects.aggregate(*pipeline)) or []
        return pincode_email_map

    def fetch_user_details(self, email_id):

        query = {
            'email': email_id
        }

        return self.model.objects.get_one(queries=query)

    def update_user_details(self, email_id, user_details):

        query = {
            'email': email_id
        }

        if user_details['active']:
            user_details.update({
                'alertCount': 0
            })

        data = {
            '$set': user_details
        }

        try:
            doc = self.model.objects.update_one(queries=query, data=data, return_document=ReturnDocument.AFTER)
        except Exception as e:
            print(e)
        return doc
