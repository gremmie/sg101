"""
Template tags for the Polls application. 
"""
from django import template

from polls.models import Poll

register = template.Library()


@register.inclusion_tag("polls/latest_poll_tag.html")
def latest_poll():
    try:
        poll = Poll.objects.get_current_polls()[0]
    except IndexError:
        poll = None

    return {'poll': poll }
