"""
This module contains decorators for the antispam application.

"""
from functools import wraps
import logging


def log_auth_failures(auth_type):

    def decorator(fn):
        logger = logging.getLogger('auth')

        @wraps(fn)
        def wrapped(request, *args, **kwargs):

            response = fn(request, *args, **kwargs)

            if request.method == 'POST':

                # Figure out if the view succeeded; success means a redirect is
                # about to occur.
                success = (response and response.has_header('location') and
                        response.status_code == 302)

                if not success:
                    username = request.POST.get('username')
                    username = username if username else '(None)'
                    logger.error("%s failure from [%s] for %r",
                            auth_type,
                            request.META.get('REMOTE_ADDR', '?'),
                            username)

            return response

        return wrapped
    return decorator
