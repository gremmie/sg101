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

    return {'poll': poll}


@register.simple_tag(takes_context=True)
def latest_poll_block(context):
    polls = Poll.objects.get_current_polls()
    t = template.loader.get_template('polls/v3/latest_poll_block_tag.html')
    with context.push():
        context['polls'] = polls
        return t.render(context.flatten())
