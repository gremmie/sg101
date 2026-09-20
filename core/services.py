"""
This module provides a common way for the various apps to integrate with services
that are installed at this site.

"""
from django.conf import settings
import redis

# Redis connection and database settings

REDIS_HOST = getattr(settings, 'REDIS_HOST', 'localhost')
REDIS_PORT = getattr(settings, 'REDIS_PORT', 6379)
REDIS_DB = getattr(settings, 'REDIS_DB', 0)


def get_redis_connection(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB):
    """
    Create and return a Redis connection using the supplied parameters.

    """
    # decode_responses=True returns str (not bytes) from reads. Every value this
    # app stores in Redis is text/int/JSON, and on Python 2 the code treated
    # reads as str; this keeps that behavior on Python 3.
    return redis.StrictRedis(host=host, port=port, db=db,
                             decode_responses=True)
