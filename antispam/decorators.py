"""
This module contains decorators for the antispam application.

"""
import json
from functools import wraps
import logging


def log_auth_failures(auth_type):

    def decorator(fn):
        logger = logging.getLogger('auth')

        @wraps(fn)
        def wrapped(request, *args, **kwargs):

            response = fn(request, *args, **kwargs)

            if request.method == 'POST':

                # Figure out if the view succeeded; if it is a non-ajax view,
                # then success means a redirect is about to occur. If it is
                # an ajax view, we have to decode the json response.
                success = False
                if not request.is_ajax():
                    success = (response and response.has_header('location') and
                            response.status_code == 302)
                elif response:
                    json_resp = json.loads(response.content)
                    success = json_resp['success']

                if not success:
                    username = request.POST.get('username')
                    username = username if username else '(None)'
                    logger.error("%s failure from [%s] for %s",
                            auth_type,
                            request.META.get('REMOTE_ADDR', '?'),
                            username)

            return response

        return wrapped
    return decorator
