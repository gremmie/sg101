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

# How many of the newest usernames we keep
MAX_NEW_USERS = 10


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
    pipeline.ltrim(NEW_USERS_KEY, 0, MAX_NEW_USERS - 1)
    pipeline.execute()


def rebuild(redis):
    """
    Replaces the user statistics with what the database says they should be.
    For use after a database restore.

    """
    usernames = _newest_usernames()

    pipeline = redis.pipeline()
    pipeline.set(USER_COUNT_KEY, User.objects.count())
    pipeline.delete(NEW_USERS_KEY)
    if usernames:
        pipeline.rpush(NEW_USERS_KEY, *usernames)
    pipeline.execute()


def verify(redis):
    """
    Compares the user statistics with the database, and returns a list of the
    differences found, as messages. An empty list means they agree.

    """
    problems = []

    count = User.objects.count()
    actual = redis.get(USER_COUNT_KEY)
    if actual is None or int(actual) != count:
        problems.append("%s is %s, expected %d" % (USER_COUNT_KEY, actual,
                                                   count))

    usernames = _newest_usernames()
    actual = redis.lrange(NEW_USERS_KEY, 0, -1)
    if actual != usernames:
        problems.append("%s holds %s, expected %s" % (NEW_USERS_KEY, actual,
                                                      usernames))

    return problems


def _newest_usernames():
    """The newest usernames, newest first, as update_user_stats() keeps them."""
    return list(User.objects.order_by('-date_joined', '-id').values_list(
            'username', flat=True)[:MAX_NEW_USERS])


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
