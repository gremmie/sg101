"""
Template tags for the smiley application. 
"""
from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe

from smiley.models import Smiley

register = template.Library()


@register.filter
@stringfilter
def smiley_html(value, autoescape=False):
    """A filter to "smilify" text by replacing text with HTML img tags of smilies."""
    from smiley import smilify_html
    return mark_safe(smilify_html(value, autoescape=autoescape))
smiley_html.needs_autoescape = True


@register.filter
@stringfilter
def smiley_markdown(value, autoescape=False):
    """A filter to "smilify" text by replacing text with HTML img tags of smilies."""
    from smiley import smilify_markdown
    return mark_safe(smilify_markdown(value, autoescape=autoescape))
smiley_markdown.needs_autoescape = True


@register.inclusion_tag('smiley/smiley_farm.html')
def smiley_farm():
    """An inclusion tag that displays all of the smilies in clickable form."""
    return {'smilies': Smiley.objects.get_smilies(), }

