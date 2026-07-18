"""
Template tags for the banners application.

"""
import logging

from django import template
import redis

from core.services import get_redis_connection
from banners.models import Banner


register = template.Library()
logger = logging.getLogger(__name__)

BANNER_URL_KEY = 'banners:url:%s'


@register.simple_tag
def banner_url(slug):
    """
    Returns the URL for the next banner in the campaign whose slug is 'slug'.

    For each campaign, a list of banner URLs are kept in Redis. Each time this
    tag is called, the front banner is popped off the list. When the list is
    empty, we refresh the list from the database. In this way the banners for a
    campaign are cycled through.
    """
    key = BANNER_URL_KEY % slug

    try:
        conn = get_redis_connection()
        url = conn.lpop(key)
    except redis.RedisError as e:
        logger.error("banner_url: '%s' on lpop", e)
        return u''

    if url:
        return url

    # list not found or empty, rebuild it from the database

    qs = Banner.objects.filter(campaign__slug=slug)
    urls = [banner.image.url for banner in qs]
    if not urls:
        logger.warning("banner_url: no banners for campaign '%s'", slug)
        return u''

    url = urls[0]
    urls = urls[1:]

    if urls:
        try:
            conn.rpush(key, *urls)
        except redis.RedisError as e:
            logger.error("banner_url: '%s' on rpush", e)
            pass

    return url
