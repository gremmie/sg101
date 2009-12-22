"""
Middleware for the forums application.
"""
import datetime

from django.core.cache import cache
from django.conf import settings


USER_ONLINE_TIMEOUT = datetime.timedelta(minutes=15)
USERS_ONLINE_KEY = 'users_online'
GUESTS_ONLINE_KEY = 'guests_online'
USERS_CACHE_TIMEOUT = 60 * 60 * 24      # units are seconds


class WhosOnline(object):
    """
    This middleware class keeps track of which registered users have
    been seen recently, and the number of unique unregistered users.
    We use the Django cache system to store this information.
    This middleware should come after the authentication middleware,
    as we count on the user attribute being attached to the request.
    """

    def process_request(self, request):
        """
        Keep track of who is online.
        """
        now = datetime.datetime.now()
        cutoff = now - USER_ONLINE_TIMEOUT
        users_online = cache.get(USERS_ONLINE_KEY, {})
        guests_online = cache.get(GUESTS_ONLINE_KEY, {})

        # update timestamp for user
        if request.user.is_authenticated():
            users_online[request.user.username] = now
        else:
            sid = request.COOKIES.get(settings.SESSION_COOKIE_NAME, '')
            guests_online[sid] = now

        # expire old records
        for username, timestamp in users_online.items():
            if timestamp < cutoff:
                del users_online[username]

        for sid, timestamp in guests_online.items():
            if timestamp < cutoff:
                del guests_online[sid]

        cache.set(USERS_ONLINE_KEY, users_online, USERS_CACHE_TIMEOUT)
        cache.set(GUESTS_ONLINE_KEY, guests_online, USERS_CACHE_TIMEOUT)
