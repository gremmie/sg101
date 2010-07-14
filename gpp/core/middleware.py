"""Common middleware for the entire project."""
import datetime

from django.contrib.auth import logout
from django.conf import settings

from core.models import UserLastVisit
from core.models import AnonLastVisit
from core.functions import get_ip


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
ONLINE_TIMEOUT = 10 * 60        # online cookie lifetime in seconds

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
                # update the last seen timestamp
                try:
                    ulv = UserLastVisit.objects.get(user=request.user)
                except UserLastVisit.DoesNotExist:
                    ulv = UserLastVisit(user=request.user)

                ulv.last_visit = datetime.datetime.now()
                ulv.save()

                # set a cookie to expire in 10 minutes or so
                response.set_cookie(ONLINE_COOKIE, '1', max_age=ONLINE_TIMEOUT)
        else:
            if request.COOKIES.get(settings.CSRF_COOKIE_NAME) is not None:
                # We have a non-authenticated user that has cookies enabled. This
                # means we can track them.
                if request.COOKIES.get(ONLINE_COOKIE) is None:
                    # update the timestamp for this anonymous visitor
                    ip = get_ip(request)
                    if ip:
                        try:
                            alv = AnonLastVisit.objects.get(ip=ip)
                        except AnonLastVisit.DoesNotExist:
                            alv = AnonLastVisit(ip=ip)

                        alv.last_visit = datetime.datetime.now()
                        alv.save()

                        # set a cookie to expire in 10 minutes or so
                        response.set_cookie(ONLINE_COOKIE, '1', max_age=ONLINE_TIMEOUT)

        return response
