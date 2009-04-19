"""
Template tags for the weblinks application.
"""
from django import template

from weblinks.models import Link
from weblinks.forms import SearchForm


register = template.Library()

@register.inclusion_tag('weblinks/navigation.html', takes_context=True)
def weblinks_navigation(context):
    return {
        'search_form': SearchForm(),
        'user': context['user'],
    }


@register.inclusion_tag('weblinks/latest_tag.html')
def latest_weblinks():
    links = Link.public_objects.order_by('-date_added')[:10]
    return {
        'links': links,
    }
