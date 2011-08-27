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


class RateLimiterUnavailable(Exception):
    pass


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
    except redis.RedisError, e:
        logger.error("rate limit: %s" % e)
        raise RateLimiterUnavailable

    return conn


def _to_seconds(interval):
    """
    Converts the timedelta interval object into a count of seconds.

    """
    return interval.days * 24 * 3600 + interval.seconds


def block_ip(ip, count=1000000, interval=datetime.timedelta(weeks=2)):
    """
    This function jams the rate limit record for the given IP so that the IP is
    blocked for the given interval. If the record doesn't exist, it is created.
    This is useful for manually blocking an IP after detecting suspicious
    behavior.
    This function may throw RateLimiterUnavailable.

    """
    key = _make_key(ip)
    conn = _get_connection()

    conn.setex(key, count, _to_seconds(interval))
    logger.info("Rate limiter blocked IP %s; %d / %s", ip, count, interval)


class RateLimiter(object):
    """
    This class encapsulates the rate limiting logic for a given IP address.

    """
    def __init__(self, ip, set_point, interval, lockout):
        self.ip = ip
        self.set_point = set_point
        self.interval = interval
        self.lockout = lockout
        self.key = _make_key(ip)
        self.conn = _get_connection()

    def is_blocked(self):
        """
        Return True if the IP is blocked, and false otherwise.

        """
        val = self.conn.get(self.key)
        try:
            val = int(val) if val else 0
        except ValueError:
            return False

        blocked = val >= self.set_point
        if blocked:
            logger.info("Rate limiter blocking %s", self.ip)

        return blocked

    def incr(self):
        """
        One is added to a counter associated with the IP address. If the
        counter exceeds set_point per interval, True is returned, and False
        otherwise. If the set_point is exceeded for the first time, the counter
        associated with the IP is set to expire according to the lockout
        parameter.

        """
        val = self.conn.incr(self.key)

        # Set expire time, if necessary.
        # If this is the first time, set it according to interval.
        # If the set_point has just been exceeded, set it according to lockout.
        if val == 1:
            self.conn.expire(self.key, _to_seconds(self.interval))
        elif val == self.set_point:
            self.conn.expire(self.key, _to_seconds(self.lockout))

        tripped = val >= self.set_point

        if tripped:
            logger.info("Rate limiter tripped for %s; counter = %d", self.ip, val)

        return tripped
