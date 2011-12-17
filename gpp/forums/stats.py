"""
This module is responsible for managing various forum statistics.

"""
from django.core.cache import cache

from forums.models import Post


CACHE_KEY = 'forums-stats-2'
CACHE_TIMEOUT = 4 * 60 * 60         # seconds


def calc_stats():
    """
    This function is responsible for computing the forum statistics.
    The forums post count is returned.

    """
    post_count = Post.objects.all().count()
    return post_count


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
