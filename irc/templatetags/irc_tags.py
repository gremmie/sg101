"""
Template tags for the IRC application.
"""
from django import template
from irc.models import IrcChannel

register = template.Library()

@register.inclusion_tag('irc/irc_block.html')
def irc_status():
    nicks = IrcChannel.objects.all()
    return {
        'nicks': nicks,
    }
