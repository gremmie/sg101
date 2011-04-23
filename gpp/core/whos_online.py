"""
This module keeps track of who is online. We maintain records for both
authenticated users ("users") and non-authenticated visitors ("visitors").
"""
import logging

from django.conf import settings
import redis

# Users and visitors each have 2 sets that we store in a Redis database:
# a current set and an old set. Whenever a user or visitor is seen, the
# current set is updated. At some interval, the current set is renamed
# to the old set, thus destroying it. At any given time, the union of the
# current and old sets is the "who's online" set.

# Redis connection and database settings

HOST = getattr(settings, 'WHOS_ONLINE_REDIS_HOST', 'localhost')
PORT = getattr(settings, 'WHOS_ONLINE_REDIS_PORT', 6379)
DB = getattr(settings, 'WHOS_ONLINE_REDIS_DB', 0)

# Redis key names:
USER_CURRENT_KEY = "wo_user_current"
USER_OLD_KEY = "wo_user_old"
USER_KEYS = [USER_CURRENT_KEY, USER_OLD_KEY]

VISITOR_CURRENT_KEY = "wo_visitor_current"
VISITOR_OLD_KEY = "wo_visitor_old"
VISITOR_KEYS = [VISITOR_CURRENT_KEY, VISITOR_OLD_KEY]


# Logging: we don't want a Redis malfunction to bring down the site. So we
# catch all Redis exceptions, log them, and press on.
logger = logging.getLogger(__name__)


def _get_connection():
    """
    Create and return a Redis connection. Returns None on failure.
    """
    try:
        conn = redis.Redis(host=HOST, port=PORT, db=DB)
        return conn
    except redis.RedisError, e:
        logger.error(e)

    return None


def report_user(username):
    """
    Call this function when a user has been seen. The username will be added to
    the current set.
    """
    conn = _get_connection()
    if conn:
        try:
            conn.sadd(USER_CURRENT_KEY, username)
        except redis.RedisError, e:
            logger.error(e)


def report_visitor(ip):
    """
    Call this function when a visitor has been seen. The IP address will be
    added the current set.
    """
    conn = _get_connection()
    if conn:
        try:
            conn.sadd(VISITOR_CURRENT_KEY, ip)
        except redis.RedisError, e:
            logger.error(e)


def get_users_online():
    """
    Returns a set of user names which is the union of the current and old
    sets.
    """
    conn = _get_connection()
    if conn:
        try:
            # Note that keys that do not exist are considered empty sets
            return conn.sunion(USER_KEYS)
        except redis.RedisError, e:
            logger.error(e)

    return set()


def get_visitors_online():
    """
    Returns a set of visitor IP addresses which is the union of the current
    and old sets.
    """
    conn = _get_connection()
    if conn:
        try:
            # Note that keys that do not exist are considered empty sets
            return conn.sunion(VISITOR_KEYS)
        except redis.RedisError, e:
            logger.error(e)

    return set()


def _tick_set(conn, current, old):
    """
    This function renames the set named "current" to "old".
    """
    # An exception may be raised if the current key doesn't exist; if that
    # happens we have to delete the old set because no one is online.
    try:
        conn.rename(current, old)
    except redis.ResponseError:
        try:
            del conn[old]
        except redis.RedisError, e:
            logger.error(e)
    except redis.RedisError, e:
        logger.error(e)


def tick():
    """
    Call this function to "age out" the old sets by renaming the current sets
    to the old.
    """
    conn = _get_connection()
    if conn:
        _tick_set(conn, USER_CURRENT_KEY, USER_OLD_KEY)
        _tick_set(conn, VISITOR_CURRENT_KEY, VISITOR_OLD_KEY)
