"""
Template tags for the smiley application. 
"""
import re
from django import template
from django.template.defaultfilters import stringfilter
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.utils.safestring import SafeData

from smiley.models import Smiley

register = template.Library()

word_split_re = re.compile(r'(\s+)')

@register.filter
@stringfilter
def smilify(value, autoescape=False):
    """A filter to "smilify" text by replacing text with HTML img tags of smilies."""
    if not autoescape or isinstance(value, SafeData):
        esc = lambda x: x
    else:
        esc = conditional_escape

    smiley_map = Smiley.objects.get_smiley_map()

    words = word_split_re.split(value)
    for i, word in enumerate(words):
        if word in smiley_map:
            words[i] = smiley_map[word]
        else:
            words[i] = esc(words[i])
    return mark_safe(u''.join(words))
smilify.needs_autoescape = True


@register.inclusion_tag('smiley/smiley_farm.html')
def smiley_farm():
    """An inclusion tag that displays all of the smilies in clickable form."""
    return {'smilies': Smiley.objects.get_smilies(), }

