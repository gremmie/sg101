"""
Template tags for the downloads application.
"""
from django import template

from downloads.forms import SearchForm


register = template.Library()

@register.inclusion_tag('downloads/navigation.html')
def downloads_navigation():
    return {'search_form': SearchForm()}
