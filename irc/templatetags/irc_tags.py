"""Template tags for the IRC application."""

from django import template

from irc.channel import get_users

register = template.Library()

@register.inclusion_tag('irc/irc_block.html')
def irc_status():
    return {
        'nicks': get_users(),
    }
