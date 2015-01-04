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
REDIS_SOCKET = getattr(settings, 'REDIS_UNIX_SOCKET', None)


def get_redis_connection(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB,
                         unix_socket_path=REDIS_SOCKET):
    """
    Create and return a Redis connection using the supplied parameters.

    """
    if unix_socket_path:
        return redis.StrictRedis(unix_socket_path=unix_socket_path, db=db)
    return redis.StrictRedis(host=host, port=port, db=db)
