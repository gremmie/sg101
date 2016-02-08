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
    context['polls'] = polls
    template_name = ('polls/v3/latest_poll_block_tag.html'
            if 'V3_DESIGN' in context else 'polls/latest_poll_block_tag.html')
    t = template.loader.get_template(template_name)
    return t.render(context)
