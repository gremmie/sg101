"""Common middleware for the entire project."""
import datetime
import logging

from django.db import IntegrityError
from django.contrib.auth import logout
from django.conf import settings

from core.functions import get_ip
from core.whos_online import report_user, report_visitor


class InactiveUserMiddleware(object):
    """
    This middleware ensures users with is_active set to False get their
    session destroyed and are treated as logged out.
    This middleware should come after the 'django.contrib.auth.middleware.
    AuthenticationMiddleware' in settings.py.
    Idea taken from: http://djangosnippets.org/snippets/1105/
    """

    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.user.is_authenticated() and not request.user.is_active:
            logout(request)


ONLINE_COOKIE = 'sg101_online'  # online cookie name
ONLINE_TIMEOUT = 5 * 60         # online cookie lifetime in seconds


class WhosOnline(object):
    """
    This middleware class keeps track of which registered users have
    been seen recently, and the number of unique unregistered users.
    This middleware should come after the authentication middleware,
    as we count on the user attribute being attached to the request.
    """

    def process_response(self, request, response):
        """
        Keep track of who is online.
        """
        # Note that some requests may not have a user attribute
        # as these may have been redirected in the middleware chain before
        # the auth middleware got a chance to run. If this is the case, just
        # bail out. We also ignore AJAX requests.

        if not hasattr(request, 'user') or request.is_ajax():
            return response

        if request.user.is_authenticated():
            if request.COOKIES.get(ONLINE_COOKIE) is None:
                # report that we've seen the user
                report_user(request.user.username)

                # set a cookie to expire
                response.set_cookie(ONLINE_COOKIE, '1', max_age=ONLINE_TIMEOUT)
        else:
            if request.COOKIES.get(settings.CSRF_COOKIE_NAME) is not None:
                # We have a non-authenticated user that has cookies enabled. This
                # means we can track them.
                if request.COOKIES.get(ONLINE_COOKIE) is None:
                    # see if we can get the IP address
                    ip = get_ip(request)
                    if ip:
                        # report that we've seen this visitor
                        report_visitor(ip)

                        # set a cookie to expire
                        response.set_cookie(ONLINE_COOKIE, '1', max_age=ONLINE_TIMEOUT)

        return response
