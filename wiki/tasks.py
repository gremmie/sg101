"""
Celery tasks for the wiki app.

"""
import datetime
import logging
import time

from celery.task import task
from django.conf import settings
import redis

from core.services import get_redis_connection


logger = logging.getLogger(__name__)


@task
def expire_cookies():
    """
    Periodically run this task to remove expired cookies from the Redis set
    that is shared between this Django application & the MoinMoin wiki for
    authentication.

    """
    now = datetime.datetime.utcnow()
    cutoff = now - datetime.timedelta(seconds=settings.WIKI_COOKIE_AGE)
    min_score = time.mktime(cutoff.utctimetuple())

    conn = get_redis_connection()

    set_name = settings.WIKI_REDIS_SET
    try:
        count = conn.zcard(set_name)
    except redis.RedisError:
        logger.error("Error getting zcard")
        return

    try:
        removed = conn.zremrangebyscore(set_name, 0.0, min_score)
    except redis.RedisError:
        logger.error("Error removing by score")
        return

    total = count - removed
    logger.info("Expire wiki cookies: removed %d, total is now %d",
            removed, total)
