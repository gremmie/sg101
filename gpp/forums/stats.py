"""
This module is responsible for managing various forum statistics.

"""
from django.core.cache import cache
from django.contrib.auth.models import User

from forums.models import Post


CACHE_KEY = 'forums-stats'
CACHE_TIMEOUT = 4 * 60 * 60         # seconds


def calc_stats():
    """
    This function is responsible for computing the forum statistics.
    A tuple is returned: (forums post count, active user count, latest username)

    """
    post_count = Post.objects.all().count()
    user_count = User.objects.all().count()

    if user_count > 0:
        latest_user = User.objects.filter(is_active=True).values_list(
                'username', flat=True).order_by('-date_joined')[0]
    else:
        latest_user = None

    return post_count, user_count, latest_user


def update_stats():
    """
    This function is responsible for computing the forum statistics and
    inserting them into the cache. The stats are returned.

    This function should be run periodically, preferably outside of the
    request/response cycle. On MySQL under InnoDb it is expensive to retrieve
    the total post count.

    """
    stats = calc_stats()
    cache.set(CACHE_KEY, stats, CACHE_TIMEOUT)
    return stats


def retrieve_stats():
    """
    This function retrieves the forum stats from the cache if they are
    available. If there is a cache-miss, the stats are calcuated, the cache is
    updated, and the stats returned.

    """
    stats = cache.get(CACHE_KEY)
    if stats is None:
        stats = update_stats()

    return stats
