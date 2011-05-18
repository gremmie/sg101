"""
Miscellaneous/utility template tags.
"""
import datetime
import urllib

from django import template
from django.conf import settings
from django.core.cache import cache

import repoze.timeago

from core.whos_online import get_users_online, get_visitors_online
from bio.models import UserProfile


register = template.Library()

ICON_PARAMS = {
    True: (settings.STATIC_URL + 'icons/accept.png', 'Yes'),
    False: (settings.STATIC_URL + 'icons/delete.png', 'No'),
}

@register.simple_tag
def bool_icon(flag):
    params = ICON_PARAMS[bool(flag)]
    return u"""<img src="%s" alt="%s" title="%s" />""" % (
            params[0], params[1], params[1])


@register.inclusion_tag('core/comment_dialogs.html')
def comment_dialogs():
    return {'STATIC_URL': settings.STATIC_URL}


@register.inclusion_tag('core/whos_online_tag.html')
def whos_online():
    """
    Displays a list of who is online.
    """
    users = get_users_online()
    visitors = get_visitors_online()

    return {
        'num_users': len(users),
        'users': sorted(users),
        'num_guests': len(visitors),
        'total': len(users) + len(visitors),
    }


# A somewhat ugly hack until we decide if we should be using UTC time
# everywhere or not.
repoze.timeago._NOW = datetime.datetime.now

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


@register.inclusion_tag('core/birthday_block.html')
def birthday_block():
    """
    A template tag to display all the users who have birthdays this month.
    """
    today = datetime.date.today()
    profiles = list(UserProfile.objects.filter(birthday__month=today.month).select_related(
            'user'))
    profiles.sort(key=lambda p: p.birthday.day)

    return {
        'STATIC_URL': settings.STATIC_URL,
        'profiles': profiles,
        'today': today,
    }


class EncodeParamsNode(template.Node):
    """
    This is the Node class for the encode_params template tag.
    This template tag retrieves the named parameters from the supplied
    querydict and returns them as a urlencoded string.

    """
    def __init__(self, querydict, args):
        self.querydict = template.Variable(querydict)
        self.args = args

    def render(self, context):
        querydict = self.querydict.resolve(context)
        params = []
        for arg in self.args:
            params.extend([(arg, value) for value in querydict.getlist(arg)])

        return urllib.urlencode(params)


@register.tag
def encode_params(parser, token):
    """
    This is the compilation function for the encore_params template tag.
    This template tag retrieves the named parameters from the supplied
    querydict and returns them as a urlencoded string.

    """
    bits = token.split_contents()
    if len(bits) < 3:
        raise template.TemplateSyntaxError("%s takes at least 2 arguments: "
                                "querydict arg1 [arg2 arg3 ... argN]" % bits[0])

    querydict = bits[1]
    args = [arg[1:-1] for arg in bits[2:]]
    return EncodeParamsNode(querydict, args)
