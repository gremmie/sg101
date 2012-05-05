"""
Miscellaneous/utility template tags.

"""
import collections
import datetime
import urllib

from django import template
from django.conf import settings
from django.core.cache import cache
from django.contrib.sites.models import Site

import repoze.timeago

from core.whos_online import get_users_online, get_visitors_online, get_stats
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


@register.inclusion_tag('core/max_users_tag.html')
def max_users():
    """
    Displays max users online information.

    """
    return {
        'stats': get_stats(),
    }

@register.inclusion_tag('core/whos_online_tag.html')
def whos_online():
    """
    Displays a list of who is online.

    """
    users = get_users_online()
    users.sort(key=str.lower)

    visitors = get_visitors_online()

    return {
        'num_users': len(users),
        'users': users,
        'num_guests': len(visitors),
        'total': len(users) + len(visitors),
    }


@register.inclusion_tag('core/social_sharing_tag.html')
def social_sharing(title, url):
    """
    Displays social media sharing buttons.

    """
    site = Site.objects.get_current()
    url = _fully_qualify(url, site.domain)

    return {
        'title': title,
        'url': url,
    }


def _fully_qualify(url, domain):
    """
    Returns a "fully qualified" URL by checking the given url.
    If the url starts with '/' then http://domain is pre-pended
    onto it. Otherwise the original URL is returned.

    """
    if url.startswith('/'):
        url = "http://%s%s" % (domain, url)
    return url


@register.inclusion_tag('core/open_graph_meta_tag.html')
def open_graph_meta_tags(item=None):
    """
    Generates Open Graph meta tags by interrogating the given item.
    To generate tags for the home page, set item to None.

    """
    site = Site.objects.get_current()

    if item:
        props = item.ogp_tags()
    else:
        props = {
            'og:title': site.name,
            'og:type': 'website',
            'og:url': 'http://%s' % site.domain,
            'og:description': settings.OGP_SITE_DESCRIPTION,
        }

    props['og:site_name'] = site.name
    props['fb:admins'] = settings.OGP_FB_ID

    if 'og:image' not in props:
        props['og:image'] = settings.OGP_DEFAULT_IMAGE

    if 'og:url' in props:
        props['og:url'] = _fully_qualify(props['og:url'], site.domain)

    if 'og:image' in props:
        props['og:image'] = _fully_qualify(props['og:image'], site.domain)

    return {'props': props}


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


class Birthday(object):
    """
    A simple named tuple-type class for birthdays.
    This class was created to make things easier in the template.

    """
    day = None
    profiles = []

    def __init__(self, day, profiles=None):
        self.day = day
        self.profiles = profiles if profiles else []


@register.inclusion_tag('core/birthday_block.html')
def birthday_block():
    """
    A template tag to display all the users who have birthdays this month.
    """
    today = datetime.date.today()
    profiles = list(UserProfile.objects.filter(birthday__month=today.month).select_related(
            'user'))

    days = collections.defaultdict(list)
    for profile in profiles:
        days[profile.birthday.day].append(profile)

    birthdays = [Birthday(day, profiles) for day, profiles in days.iteritems()]
    birthdays.sort(key=lambda b: b.day)

    return {
        'STATIC_URL': settings.STATIC_URL,
        'birthdays': birthdays,
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
    This is the compilation function for the encode_params template tag.
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
