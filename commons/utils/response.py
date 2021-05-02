from datetime import datetime

from bson.objectid import ObjectId
from django.core.serializers.json import DjangoJSONEncoder
from django.http.response import JsonResponse


class CustomJsonEncoder(DjangoJSONEncoder):
    '''A custom JSON encoder handling JSON native encoding for following python types
        - datetime
        - bson object id
    '''

    def default(self, obj):
        '''JSON Encoding handler method
        '''

        if isinstance(obj, ObjectId):
            return str(obj)

        if isinstance(obj, datetime):
            return int(float(obj.strftime('%s')) * 1000)

        return super(CustomJsonEncoder, self).default(obj)


class JSONResponse(JsonResponse):
    '''A Django JsonResponse class that consumes data to be serialized to JSON using CustomJsonEncoder.
    '''

    def __init__(self, data, encoder=CustomJsonEncoder, safe=True, json_dumps_params=None, **kwargs):
        '''
        Args:
            data: Data to be dumped into JSON. By default only dict objects
                  are allowed to be passed due to a security flaw.
            encoder: A JSON encoder class.
            safe: Controls if only dict objects may be serialized. Defaults to True.
            json_dumps_params: A dictionary of kwargs passed to json.dumps().
            kwargs: key word args for Django's JsonResponse class (params of HttpResponseBase class)
        '''

        super(JSONResponse, self).__init__(data, encoder, safe, json_dumps_params, **kwargs)


class OK(JSONResponse):
    '''A Custom JSONResponse class that append response with 200 http status code.
    '''

    def __init__(self, data, encoder=CustomJsonEncoder, safe=True, json_dumps_params=None, **kwargs):
        '''
        Args:
            data: Data to be dumped into JSON. By default only dict objects
                  are allowed to be passed due to a security flaw.
            encoder: A JSON encoder class.
            safe: Controls if only dict objects may be serialized. Defaults to True.
            json_dumps_params: A dictionary of kwargs passed to json.dumps().
            kwargs: key word args for Django's JsonResponse class (params of HttpResponseBase class)
        '''

        kwargs.pop('status', None)
        kwargs['status'] = 200

        super(JSONResponse, self).__init__(data, encoder, safe, json_dumps_params, **kwargs)
