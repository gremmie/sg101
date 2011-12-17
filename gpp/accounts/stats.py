"""
This module performs user account related statistics.

"""
import logging

from django.db.models.signals import post_save
from django.contrib.auth.models import User

from core.services import get_redis_connection


# Redis key names
USER_COUNT_KEY = "accounts:user_count"
NEW_USERS_KEY = "accounts:new_users"


logger = logging.getLogger(__name__)


def on_user_save(sender, **kwargs):
    """
    This function is our signal handler for when a User object is saved.

    """
    from accounts.tasks import user_stats_task

    if kwargs['created']:
        user = kwargs['instance']

        # kick off a task to update user stats

        user_stats_task.delay(user.id)


def update_user_stats(user_id):
    """
    This function is given a new user id and is responsible for updating various
    user account statistics.

    """
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        logger.warning("update_user_stats: user id %d doesn't exist", user_id)
        return

    redis = get_redis_connection()

    # update the count of registered users

    count = redis.incr(USER_COUNT_KEY)
    if count == 1:
        # it is likely redis got wiped out; update it now
        count = User.objects.all().count()
        redis.set(USER_COUNT_KEY, count)

    # update the list of new users

    pipeline = redis.pipeline()
    pipeline.lpush(NEW_USERS_KEY, user.username)
    pipeline.ltrim(NEW_USERS_KEY, 0, 9)
    pipeline.execute()


def get_user_count(redis=None):
    """
    This function returns the current count of users.

    """
    if redis is None:
        redis = get_redis_connection()
    return redis.get(USER_COUNT_KEY)


def get_new_users(redis=None):
    """
    This function returns a list of new usernames.

    """
    if redis is None:
        redis = get_redis_connection()
    return redis.lrange(NEW_USERS_KEY, 0, -1)


def get_user_stats(redis=None):
    """
    This function returns a tuple of the user stats. Element 0 is the user count
    and element 1 is the list of new users.

    """
    if redis is None:
        redis = get_redis_connection()
    return get_user_count(redis), get_new_users(redis)


post_save.connect(on_user_save, sender=User, dispatch_uid='accounts.stats')
