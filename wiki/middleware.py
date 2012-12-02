"""Middleware for wiki integration.

"""
import datetime
import hashlib
import logging
import random
import string
import time

from django.conf import settings
import redis

from core.services import get_redis_connection
from wiki.constants import SESSION_SET_MEMBER


logger = logging.getLogger(__name__)


def cookie_value(user, now):
    """Creates the value for the external wiki cookie."""

    # The key part of the cookie is just a string that would make things
    # difficult for a spoofer; something that can't be easily made up:

    h = hashlib.sha256()
    h.update(user.username + user.email)
    h.update(now.isoformat())
    h.update(''.join(random.sample(string.printable, 64)))
    h.update(settings.SECRET_KEY)
    key = h.hexdigest()

    parts = (user.username, user.email, key)
    return '#'.join(parts)


def create_wiki_session(request, response):
    """Sets up the session for the external wiki application.

    Creates the external cookie for the Wiki.
    Updates the Redis set so the Wiki can verify the cookie.

    """
    now = datetime.datetime.utcnow()
    value = cookie_value(request.user, now)
    response.set_cookie(settings.WIKI_COOKIE_NAME,
            value=value,
            max_age=settings.WIKI_COOKIE_AGE,
            domain=settings.WIKI_COOKIE_DOMAIN)

    # Update a sorted set in Redis with a hash of our cookie and a score
    # of the current time as a timestamp. This allows us to delete old
    # entries by score periodically. To verify the cookie, the external wiki
    # application computes a hash of the cookie value and checks to see if
    # it is in our Redis set.

    h = hashlib.sha256()
    h.update(value)
    name = h.hexdigest()
    score = time.mktime(now.utctimetuple())
    conn = get_redis_connection()

    try:
        conn.zadd(settings.WIKI_REDIS_SET, score, name)
    except redis.RedisError:
        logger.error("Error adding wiki cookie key")

    # Store the set member name in the session so we can delete it when the
    # user logs out:
    request.session[SESSION_SET_MEMBER] = name


def destroy_wiki_session(set_member, response):
    """Destroys the session for the external wiki application.

    Delete the external cookie.
    Deletes the member from the Redis set as this entry is no longer valid.

    """
    response.delete_cookie(settings.WIKI_COOKIE_NAME,
                           domain=settings.WIKI_COOKIE_DOMAIN)

    if set_member:
        conn = get_redis_connection()
        try:
            conn.zrem(settings.WIKI_REDIS_SET, set_member)
        except redis.RedisError:
            logger.error("Error deleting wiki cookie set member")


class WikiMiddleware(object):
    """
    Check for flags on the request object to determine when to set or delete an
    external cookie for the wiki application. When creating a cookie, also
    set an entry in Redis that the wiki application can validate to prevent
    spoofing.

    """

    def process_response(self, request, response):

        if hasattr(request, 'wiki_set_cookie'):
            create_wiki_session(request, response)
        elif hasattr(request, 'wiki_delete_cookie'):
            destroy_wiki_session(request.wiki_delete_cookie, response)

        return response
