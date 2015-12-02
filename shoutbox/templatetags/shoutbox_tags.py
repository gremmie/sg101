"""
Template tags for the shoutbox application.
"""
from django import template

from shoutbox.models import Shout

register = template.Library()

@register.inclusion_tag('shoutbox/shoutbox.html', takes_context=True)
def shoutbox(context):
   shouts = Shout.objects.select_related('user')[:10]
   return {
      'shouts': shouts,
      'user': context['user'],
   }
