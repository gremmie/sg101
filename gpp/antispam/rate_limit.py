"""
This module contains the rate limiting functionality.

"""
import datetime
import logging

import redis
from django.conf import settings


logger = logging.getLogger(__name__)

# Redis connection and database settings
HOST = getattr(settings, 'RATE_LIMIT_REDIS_HOST', 'localhost')
PORT = getattr(settings, 'RATE_LIMIT_REDIS_PORT', 6379)
DB = getattr(settings, 'RATE_LIMIT_REDIS_DB', 0)


def _make_key(ip):
    """
    Creates and returns a key string from a given IP address.

    """
    return 'rate-limit-' + ip


def _get_connection():
    """
    Create and return a Redis connection. Returns None on failure.
    """
    try:
        conn = redis.Redis(host=HOST, port=PORT, db=DB)
        return conn
    except redis.RedisError, e:
        logger.error("rate limit: %s" % e)

    return None


def _to_seconds(interval):
    """
    Converts the timedelta interval object into a count of seconds.

    """
    return interval.days * 24 * 3600 + interval.seconds


def rate_check(ip, set_point, interval, lockout):
    """
    This function performs a rate limit check.
    One is added to a counter associated with the IP address. If the
    counter exceeds set_point per interval, True is returned, and False
    otherwise. If the set_point is exceeded for the first time, the counter
    associated with the IP is set to expire according to the lockout parameter.
    This locks the IP address as this function will then return True for the
    period specified by lockout.

    """
    if not ip:
        logger.error("rate_limit.rate_check could not get IP")
        return False
    key = _make_key(ip)

    conn = _get_connection()
    if not conn:
        return False

    val = conn.incr(key)

    # Set expire time, if necessary.
    # If this is the first time, set it according to interval.
    # If the set_point has just been exceeded, set it according to lockout.
    if val == 1:
        conn.expire(key, _to_seconds(interval))
    elif val == set_point:
        conn.expire(key, _to_seconds(lockout))

    tripped = val >= set_point

    if tripped:
        logger.info("Rate limiter tripped for %s; counter = %d", ip, val)

    return tripped


def block_ip(ip, count=1000000, interval=datetime.timedelta(weeks=2)):
    """
    This function jams the rate limit record for the given IP so that the IP is
    blocked for the given interval. If the record doesn't exist, it is created.
    This is useful for manually blocking an IP after detecting suspicious
    behavior.

    """
    if not ip:
        logger.error("rate_limit.block_ip could not get IP")
        return

    key = _make_key(ip)
    conn = _get_connection()
    if not conn:
        return

    conn.setex(key, count, _to_seconds(interval))
    logger.info("Rate limiter blocked IP %s; %d / %s", ip, count, interval)
