"""
Template tags for the bulletins application.
"""
from django import template

from bulletins.models import Bulletin


register = template.Library()


@register.inclusion_tag('bulletins/bulletins.html')
def current_bulletins():
    bulletins = Bulletin.objects.get_current()
    return {
        'bulletins': bulletins,
    }
