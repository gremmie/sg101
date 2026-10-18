"""
Template tags for the smiley application.
"""
from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe

from smiley.models import Smiley
from smiley.utils import smilify_html

register = template.Library()


@register.filter
@stringfilter
def smiley_html(value, autoescape=False):
    """A filter to "smilify" text by replacing text with HTML img tags of smilies."""
    return mark_safe(smilify_html(value, autoescape=autoescape))
smiley_html.needs_autoescape = True


@register.inclusion_tag('smiley/smiley_farm.html')
def smiley_farm():
    """An inclusion tag that displays all of the smilies in clickable form."""
    return {'smilies': Smiley.objects.get_smilies(), }



@register.inclusion_tag('smiley/smiley_picker.html')
def smiley_picker():
    """An inclusion tag that displays every smiley as a button, main set first."""
    return {
        'main': Smiley.objects.get_smilies(),
        'extra': Smiley.objects.get_smilies(extra=True),
    }
