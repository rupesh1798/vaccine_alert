import asyncio
import codecs
import time
import traceback
from uuid import uuid4
from copy import deepcopy

import requests
import ujson
from commons.utils.http_error import InternalServerError, GatewayTimeout
from django.conf import settings

from .loggers import app_logger, error_logger


def make_request(
    url, method, params=None, headers=None, data=None, json=None, timeout=20, files=None, request_id=None):
    '''Make external request to a URL using python's request module.

    Args:
        url: URL of the request.
        method: method of the request.
        params: (optional) Dictionary or bytes to be sent in the query string.
        headers: (optional) Dictionary of HTTP Headers to send.
        data: (optional) Dictionary or list of tuples, bytes, or file-like object to send in the body.
        json: (optional) A JSON serializable Python object to send in the body.
        timeout: (optional) How many seconds to wait for the server to send data.
        files: (optional) File object.

    Returns:
        A tuple containing response of the request in JSON format, binary format and HTTP code of the response and
        message of the error in making request (if any).
    '''
    request_id = request_id or str(uuid4())
    response_json = {}
    response_content = None
    response_code = None
    error = None

    req = {}

    if headers:
        req.update({'headers': headers})

    if params:
        req.update({'params': params})

    if data:
        req.update({'data': data})

    if json:
        req.update({'json': json})

    if timeout:
        req.update({'timeout': timeout})

    request_dict = deepcopy(req)
    if files:

        req.update({'files': files})

        files_req = {key: value.name for (key, value) in files.items()}

        request_dict.update({
            'files': files_req
        })

    error_logger.error(
        'API_REQUEST',
        extra={
            'meta': {
                'logType': 'APP',
                'requestPath': url,
                'requestMethod': method,
                'requestDict': ujson.dumps(request_dict),
                'requestId': request_id
            }
        }
    )

    try:
        request_epoch = time.time() * 1000
        response = requests.request(method, url, **req)
        response_epoch = time.time() * 1000
        response_content = response.content
        response_code = response.status_code

        error_logger.error(
            'API_RESPONSE',
            extra={
                'meta':{
                    'logType': 'APP',
                    'responseCode': response_code,
                    'responseTime': str(response_epoch - request_epoch),
                    'responseContent': (
                        response_content if (int(response_code/100) != 2 or settings.DEBUG) else b'{}'
                    ).decode('utf-8'),
                    'requestId': request_id
                }
            }
        )
        response_json = response.json()

    except ValueError:
        error_logger.error('API_ERROR')
        raise InternalServerError()

    except requests.exceptions.ReadTimeout:
        error_logger.error('API_TIMEOUT_ERROR')
        raise GatewayTimeout()

    except Exception as e:
        error_logger.error('API_ERROR')
        raise InternalServerError()

    return (response_json, response_content, response_code, error)


def make_basic_authorization_request(
    url, method, params=None, headers=None, data=None, json=None, timeout=20, files=None):
    '''Make external basic authorized request to a URL using python's request module without logging the request data.

    Args:
        url: URL of the request.
        method: method of the request.
        params: (optional) Dictionary or bytes to be sent in the query string.
        headers: (optional) Dictionary of HTTP Headers to send.
        data: (optional) Dictionary or list of tuples, bytes, or file-like object to send in the body.
        json: (optional) A JSON serializable Python object to send in the body.
        timeout: (optional) How many seconds to wait for the server to send data.
        files: (optional) File object.

    Returns:
        A tuple containing response of the request in JSON format, binary format and HTTP code of the response and
        message of the error in making request (if any).
    '''

    request_id = str(uuid4())
    response_json = {}
    response_content = None
    response_code = None
    error = None

    req = {}

    if headers:
        req.update({'headers': headers})

    if timeout:
        req.update({'timeout': timeout})

    if params:
        req.update({'params': params})

    if data:
        req.update({'data': data})

    if json:
        req.update({'json': json})

    request_data = dict(req)

    if request_data.get('headers', {}).get('Authorization'):
        request_data.update({
            'headers': {
                'Authorization': '## HIDDEN ##'
            }
        })

    if files:
        req.update({'files': files})

        if isinstance(files, list):
            files_req = {}
            for file in files:
                if isinstance(file[1], tuple):
                    files_req.setdefault(file[1][0], []).append(file[1][1])
                else:
                    files_req.setdefault(file[0], []).append(file[1].name)
        else:
            files_req = {key: value.name for (key, value) in files.items()}

        request_data.update({
            'files': ''
        })

    app_logger.info(
        'API_REQUEST',
        extra={
            'meta':{
                'logType': 'APP',
                'requestPath': url,
                'requestMethod': method,
                'requestDict': ujson.dumps(request_data),
                'requestId': request_id
            }
        }
    )

    try:
        request_epoch = time.time() * 1000
        response = requests.request(method, url, **req)
        response_epoch = time.time() * 1000
        if not response.content:
            response_json = {}
            response_content = b'{}'

            if int(response.status_code) == 500:
                response_json = {
                    "statusCode": 500,
                    "error": {
                        "message": "Looks like something went wrong! Please try again.\nIf the issue persists please contact support."
                    }
                }
                response_content = b'{"statusCode": 500,"error": {"message": "Looks like something went wrong! Please try again.\nIf the issue persists please contact }'
        else:
            response_json = response.json()
            response_content = response.content

        response_code = response.status_code

        app_logger.info(
            'API_RESPONSE',
            extra={
                'meta':{
                    'logType': 'APP',
                    'responseCode': response_code,
                    'responseTime': str(response_epoch - request_epoch),
                    'responseContent': (
                        response_content if (int(response_code/100) != 2 or settings.DEBUG) else b'{}'
                    ).decode('utf-8'),
                    'requestId': request_id
                }
            }
        )

    except ValueError:
        app_logger.exception('API_ERROR')
        raise InternalServerError()

    except requests.exceptions.ReadTimeout:
        app_logger.exception('API_TIMEOUT_ERROR')
        raise GatewayTimeout()

    except Exception as e:
        app_logger.exception('API_ERROR')
        raise InternalServerError()

    return (response_json, response_content, response_code, error)


async def make_async_request(
    session, url, method, params=None, headers=None, data=None, json=None, timeout=20, files=None, content_type=None):
    '''Make external request to a URL using python's request module.

    Args:
        url: URL of the request.
        method: method of the request.
        params: (optional) Dictionary or bytes to be sent in the query string.
        headers: (optional) Dictionary of HTTP Headers to send.
        data: (optional) Dictionary or list of tuples, bytes, or file-like object to send in the body.
        json: (optional) A JSON serializable Python object to send in the body.
        timeout: (optional) How many seconds to wait for the server to send data.
        files: (optional) File object.

    Returns:
        A tuple containing response of the request in JSON format, binary format and HTTP code of the response and
        message of the error in making request (if any).
    '''

    request_id = str(uuid4())
    response_json = {}
    response_content = None
    response_code = None
    error = None

    req = {}

    if headers:
        req.update({'headers': headers})

    if params:
        req.update({'params': params})

    if data:
        req.update({'data': data})

    if json:
        req.update({'json': json})

    if timeout:
        req.update({'timeout': timeout})

    request_dict = deepcopy(req)

    if files:
        req.update({'files': files})

        files_req = {key: value.name for (key, value) in files.items()}

        request_dict.update({
            'files': files_req
        })

    app_logger.info(
        'API_REQUEST',
        extra={
            'meta': {
                'logType': 'APP',
                'requestPath': url,
                'requestMethod': method,
                'requestDict': ujson.dumps(request_dict),
                'requestId': request_id
            }
        }
    )

    try:
        request_epoch = time.time() * 1000
        response = await session.request(method, url, **req)

        response_code = response.status
        if content_type:
            response_json = await response.json(content_type=content_type)
        else:
            response_json = await response.json()
        response_content = await response.text()
        response_epoch = time.time() * 1000

        app_logger.info(
            'API_RESPONSE',
            extra={
                'meta': {
                    'logType': 'APP',
                    'responseCode': response_code,
                    'responseTime': str(response_epoch - request_epoch),
                    'responseContent': (
                        response_content if (int(response_code/100) != 2 or settings.DEBUG) else "{}"
                    ),
                    'requestId': request_id
                }
            }
        )

    except ValueError:
        app_logger.exception('API_ERROR')
        raise InternalServerError()

    except requests.exceptions.ReadTimeout:
        app_logger.exception('API_TIMEOUT_ERROR')
        raise GatewayTimeout()

    except Exception as e:
        app_logger.exception('API_ERROR')
        raise InternalServerError()

    return (response_json, response_content, response_code, error)


def make_auth_request(
        url, method, params=None, headers=None, data=None, json=None, timeout=20, files=None, request_mask_map=None, request_id=None):
    '''Make external auth request to a URL using python's request module without logging the request data.

    Args:
        url: URL of the request.
        method: method of the request.
        params: (optional) Dictionary or bytes to be sent in the query string.
        headers: (optional) Dictionary of HTTP Headers to send.
        data: (optional) Dictionary or list of tuples, bytes, or file-like object to send in the body.
        json: (optional) A JSON serializable Python object to send in the body.
        timeout: (optional) How many seconds to wait for the server to send data.
        request_mask_map: Dictionary of request objects which needs to be hidden. (Level 1 hiding only)
        eg - {
            'params' : ['key1', 'key2']
        }

    Returns:
        A tuple containing response of the request in JSON format, binary format and HTTP code of the response and
        message of the error in making request (if any).
    '''

    request_id = request_id or str(uuid4())
    response_json = {}
    response_content = None
    response_code = None
    error = None

    req = {}

    if headers:
        req.update({'headers': headers})

    if timeout:
        req.update({'timeout': timeout})

    if params:
        req.update({'params': params})

    if data:
        req.update({'data': data})

    if json:
        req.update({'json': json})

    request_data = deepcopy(req)

    try:
        if request_mask_map:
            for request_attr, hidden_key_list in request_mask_map.items():
                for hidden_key in hidden_key_list:
                    if request_data.get(request_attr, {}).get(hidden_key, None):
                        request_data[request_attr][hidden_key] = '## HIDDEN ##'
    except Exception:
        app_logger.exception('API_ERROR_WHILE_MASKING')

    app_logger.info(
        'API_REQUEST',
        extra={
            'meta': {
                'requestPath': url,
                'requestMethod': method,
                'requestDict': ujson.dumps(request_data),
                'requestId': request_id
            }
        }
    )

    try:
        request_epoch = time.time() * 1000
        response = requests.request(method, url, **req)
        response_epoch = time.time() * 1000
        if not response.content:
            response_json = {}
            response_content = b'{}'

            if int(response.status_code) == 500:
                response_json = {
                    "statusCode": 500,
                    "error": {
                        "message": "Looks like something went wrong! Please try again.\nIf the issue persists please contact support."
                    }
                }
                response_content = b'{"statusCode": 500,"error": {"message": "Looks like something went wrong! Please try again.\nIf the issue persists please contact }'
        else:
            response_json = response.json()
            response_content = response.content

        response_code = response.status_code

        app_logger.info(
            'API_RESPONSE',
            extra={
                'meta': {
                    'responseCode': response_code,
                    'responseTime': str(response_epoch - request_epoch),
                    'responseContent': (
                        response_content if (int(response_code/100) != 2 or settings.DEBUG) else b'{}'
                    ).decode('utf-8'),
                    'requestId': request_id
                }
            }
        )

    except ValueError:
        app_logger.exception('API_ERROR')
        raise InternalServerError()

    except requests.exceptions.ReadTimeout:
        app_logger.exception('API_TIMEOUT_ERROR')
        raise GatewayTimeout()

    except Exception as e:
        app_logger.exception('API_ERROR')
        raise InternalServerError()

    return (response_json, response_content, response_code, error)


def make_session_request(
    url, method, params=None, headers=None, data=None, json=None, timeout=20, files=None, request_id=None, cookies=None, content_type=None):
    '''Make external request to a URL using python's request module.

    Args:
        url: URL of the request.
        method: method of the request.
        params: (optional) Dictionary or bytes to be sent in the query string.
        headers: (optional) Dictionary of HTTP Headers to send.
        data: (optional) Dictionary or list of tuples, bytes, or file-like object to send in the body.
        json: (optional) A JSON serializable Python object to send in the body.
        timeout: (optional) How many seconds to wait for the server to send data.
        files: (optional) File object.
        request_id: Id of request
        cookies: Cookies for api sessiom
        content_type: content type of response

    Returns:
        A tuple containing response of the request in JSON format, binary format and HTTP code of the response and
        message of the error in making request (if any).
    '''
    request_id = request_id or str(uuid4())
    response_json = {}
    response_content = None
    response_code = None
    error = None

    req = {}

    if headers:
        req.update({'headers': headers})

    if params:
        req.update({'params': params})

    if data:
        req.update({'data': data})

    if json:
        req.update({'json': json})

    if timeout:
        req.update({'timeout': timeout})

    if cookies:
        req.update({'cookies': cookies})

    request_dict = deepcopy(req)
    if files:

        req.update({'files': files})

        files_req = {key: value.name for (key, value) in files.items()}

        request_dict.update({
            'files': files_req
        })

    app_logger.info(
        'API_REQUEST',
        extra={
            'meta': {
                'logType': 'APP',
                'requestPath': url,
                'requestMethod': method,
                'requestDict': ujson.dumps(request_dict),
                'requestId': request_id
            }
        }
    )

    try:
        request_epoch = time.time() * 1000

        response = requests.request(method, url, **req)
        response_epoch = time.time() * 1000
        response_content = response.content
        response_text = response.text
        response_code = response.status_code

        app_logger.info(
            'API_RESPONSE',
            extra={
                'meta':{
                    'logType': 'APP',
                    'responseCode': response_code,
                    'responseTime': str(response_epoch - request_epoch),
                    'responseContent': (
                        response_content if (int(response_code/100) != 2 or settings.DEBUG) else b'{}'
                    ).decode('utf-8'),
                    'requestId': request_id
                }
            }
        )
        if content_type == 'application/json':
            response_json = response.json()

    except ValueError:
        app_logger.exception('API_ERROR')
        raise InternalServerError()

    except requests.exceptions.ReadTimeout:
        app_logger.exception('API_TIMEOUT_ERROR')
        raise GatewayTimeout()

    except Exception as e:
        app_logger.exception('API_ERROR')
        raise InternalServerError()

    return (response_json, response_content, response_code, response.cookies, error)