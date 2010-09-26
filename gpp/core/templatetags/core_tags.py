"""
Miscellaneous/utility template tags.
"""
import datetime

from django import template
from django.conf import settings
from django.core.cache import cache

import repoze.timeago

from core.models import UserLastVisit, AnonLastVisit


register = template.Library()

ICON_PARAMS = {
    True: (settings.MEDIA_URL + 'icons/accept.png', 'Yes'),
    False: (settings.MEDIA_URL + 'icons/delete.png', 'No'),
}

@register.simple_tag
def bool_icon(flag):
    params = ICON_PARAMS[bool(flag)]
    return u"""<img src="%s" alt="%s" title="%s" />""" % (
            params[0], params[1], params[1])


@register.inclusion_tag('core/comment_dialogs.html')
def comment_dialogs():
    return {'MEDIA_URL': settings.MEDIA_URL}


@register.inclusion_tag('core/whos_online_tag.html')
def whos_online():
    """
    Displays a list of who is online.
    """
    info = cache.get('whos_online')
    if info:
        return info

    now = datetime.datetime.now()
    cutoff = now - datetime.timedelta(minutes=10, seconds=5)

    info = {}
    users = UserLastVisit.objects.filter(
            last_visit__gte=cutoff).values_list('user__username', flat=True)
    num_users = len(users)
    info['num_users'] = num_users
    info['users'] = sorted(users)

    num_guests = AnonLastVisit.objects.filter(last_visit__gte=cutoff).count()
    info['num_guests'] = num_guests
    info['total'] = num_users + num_guests

    cache.set('whos_online', info, 300)
    return info


@register.filter(name='elapsed')
def elapsed(timestamp):
    """
    This filter accepts a datetime and computes an elapsed time from "now".
    The elapsed time is displayed as a "humanized" string.
    Examples:
        1 minute ago
        5 minutes ago
        1 hour ago
        10 hours ago
        1 day ago
        7 days ago

    """
    return repoze.timeago.get_elapsed(timestamp)
elapsed.is_safe = True
