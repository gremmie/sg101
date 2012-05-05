"""
This module contains the rate limiting functionality.

"""
import datetime
import logging

import redis

from core.services import get_redis_connection


logger = logging.getLogger(__name__)


# This exception is thrown upon any Redis error. This insulates client code from
# knowing that we are using Redis and will allow us to use something else in the
# future.
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
        conn = get_redis_connection()
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

    try:
        conn.setex(key, time=_to_seconds(interval), value=count)
    except redis.RedisError, e:
        logger.error("rate limit (block_ip): %s" % e)
        raise RateLimiterUnavailable

    logger.info("Rate limiter blocked IP %s; %d / %s", ip, count, interval)


def unblock_ip(ip):
    """
    This function removes the block for the given IP address.

    """
    key = _make_key(ip)
    conn = _get_connection()
    try:
        conn.delete(key)
    except redis.RedisError, e:
        logger.error("rate limit (unblock_ip): %s" % e)
        raise RateLimiterUnavailable

    logger.info("Rate limiter unblocked IP %s", ip)


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
        try:
            val = self.conn.get(self.key)
        except redis.RedisError, e:
            logger.error("RateLimiter (is_blocked): %s" % e)
            raise RateLimiterUnavailable

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
        try:
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

        except redis.RedisError, e:
            logger.error("RateLimiter (incr): %s" % e)
            raise RateLimiterUnavailable
