"""
Miscellaneous/utility template tags.
"""
from django import template
from django.conf import settings

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

