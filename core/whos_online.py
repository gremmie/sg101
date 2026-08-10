"""
This module keeps track of who is online. We maintain records for both
authenticated users ("users") and non-authenticated visitors ("visitors").
"""
import datetime
import logging

from django.utils import timezone
import redis

from core.services import get_redis_connection
from core.models import Statistic


# Users and visitors each have a sorted set in a Redis database. When a user or
# visitor is seen, the respective set is updated with the score of the current
# time. Periodically we remove elements by score (time) to stale out members.

# Redis key names:
USER_SET_KEY = "whos_online:users"
VISITOR_SET_KEY = "whos_online:visitors"

CORE_STATS_KEY = "core:stats"

# the period over which we collect who's online stats:
MAX_AGE = datetime.timedelta(minutes=15)


# Logging: we don't want a Redis malfunction to bring down the site. So we
# catch all Redis exceptions, log them, and press on.
logger = logging.getLogger(__name__)


def _get_connection():
    """
    Create and return a Redis connection. Returns None on failure.
    """
    try:
        conn = get_redis_connection()
        return conn
    except redis.RedisError as e:
        logger.error(e)

    return None


def to_timestamp(dt):
    """
    Turn the supplied aware datetime object into a UNIX timestamp integer.

    """
    # datetime.timestamp(), not time.mktime(dt.timetuple()): timetuple() drops
    # the offset and mktime() reads what is left as container-local time, which
    # gave a self-consistent but absolutely wrong epoch. Only relative order
    # ever mattered here, so the old scores were harmless -- but they are on a
    # different footing than the new ones, so members written before this
    # change age out of the window instead of being seen as recent.
    return int(dt.timestamp())


def _zadd(key, member):
    """
    Adds the member to the given set key, using the current time as the score.

    """
    conn = _get_connection()
    if conn:
        ts = to_timestamp(timezone.now())
        try:
            conn.zadd(key, {member: ts})
        except redis.RedisError as e:
            logger.error(e)


def _zrangebyscore(key):
    """
    Performs a zrangebyscore operation on the set given by key.
    The minimum score will be a timestap equal to the current time
    minus MAX_AGE. The maximum score will be a timestap equal to the
    current time.

    """
    conn = _get_connection()
    if conn:
        now = timezone.now()
        min = to_timestamp(now - MAX_AGE)
        max = to_timestamp(now)
        try:
            return conn.zrangebyscore(key, min, max)
        except redis.RedisError as e:
            logger.error(e)

    return []


def report_user(username):
    """
    Call this function when a user has been seen. The username will be added to
    the set of users online.

    """
    _zadd(USER_SET_KEY, username)


def report_visitor(ip):
    """
    Call this function when a visitor has been seen. The IP address will be
    added to the set of visitors online.

    """
    _zadd(VISITOR_SET_KEY, ip)


def get_users_online():
    """
    Returns a list of user names from the user set.
    sets.
    """
    return _zrangebyscore(USER_SET_KEY)


def get_visitors_online():
    """
    Returns a list of visitor IP addresses from the visitor set.
    """
    return _zrangebyscore(VISITOR_SET_KEY)


def _tick(conn):
    """
    Call this function to "age out" the sets by removing old users/visitors.
    It then returns a tuple of the form:
        (zcard users, zcard visitors)

    """
    cutoff = to_timestamp(timezone.now() - MAX_AGE)

    try:
        pipeline = conn.pipeline(transaction=False)
        pipeline.zremrangebyscore(USER_SET_KEY, 0, cutoff)
        pipeline.zremrangebyscore(VISITOR_SET_KEY, 0, cutoff)
        pipeline.zcard(USER_SET_KEY)
        pipeline.zcard(VISITOR_SET_KEY)
        result = pipeline.execute()
    except redis.RedisError as e:
        logger.error(e)
        return 0, 0

    return result[2], result[3]


def max_users():
    """
    Run this function periodically to clean out the sets and to compute our max
    users and max visitors statistics.

    """
    conn = _get_connection()
    if not conn:
        return

    num_users, num_visitors = _tick(conn)
    now = timezone.now()

    stats = get_stats(conn)
    update = False

    if stats is None:
        stats = Statistic(id=1,
                max_users=num_users,
                max_users_date=now,
                max_anon_users=num_visitors,
                max_anon_users_date=now)
        update = True
    else:
        if num_users > stats.max_users:
            stats.max_users = num_users
            stats.max_users_date = now
            update = True

        if num_visitors > stats.max_anon_users:
            stats.max_anon_users = num_visitors
            stats.max_anon_users_date = now
            update = True

    if update:
        _save_stats_to_redis(conn, stats)
        stats.save()


def get_stats(conn=None):
    """
    This function retrieves the who's online max user stats out of Redis. If
    the keys do not exist in Redis, we fall back to the database. If the stats
    are not available, None is returned.
    Note that if we can find stats data, it will be returned as a Statistic
    object.

    """
    if conn is None:
        conn = _get_connection()

    stats = None
    if conn:
        try:
            stats = conn.hgetall(CORE_STATS_KEY)
        except redis.RedisError as e:
            logger.error(e)

        if stats:
            # The tz argument is what makes these the inverse of to_timestamp():
            # without it fromtimestamp() returns a naive container-local value,
            # which is not what was written and not what a DateTimeField wants.
            return Statistic(
                id=1,
                max_users=int(stats['max_users']),
                max_users_date=datetime.datetime.fromtimestamp(
                    float(stats['max_users_date']), datetime.timezone.utc),
                max_anon_users=int(stats['max_anon_users']),
                max_anon_users_date=datetime.datetime.fromtimestamp(
                    float(stats['max_anon_users_date']), datetime.timezone.utc))

    try:
        stats = Statistic.objects.get(pk=1)
    except Statistic.DoesNotExist:
        return None
    else:
        _save_stats_to_redis(conn, stats)
        return stats


def _save_stats_to_redis(conn, stats):
    """
    Saves the statistics to Redis. A TTL is put on the key to prevent Redis and
    the database from becoming out of sync.

    """
    fields = dict(
        max_users=stats.max_users,
        max_users_date=to_timestamp(stats.max_users_date),
        max_anon_users=stats.max_anon_users,
        max_anon_users_date=to_timestamp(stats.max_anon_users_date))

    try:
        conn.hset(CORE_STATS_KEY, mapping=fields)
        conn.expire(CORE_STATS_KEY, 4 * 60 * 60)
    except redis.RedisError as e:
        logger.error(e)
