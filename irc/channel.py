"""Abstracts the list of users in the IRC channel."""

from redis import RedisError

from core.services import get_redis_connection

def get_users():
    """Return a list of users in the IRC channel."""
    conn = get_redis_connection()
    try:
        nicks = conn.get('irc:channel_members')
    except RedisError:
        nicks = None

    return nicks.split() if nicks else []
