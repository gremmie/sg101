"""
Template tags for the weblinks application.
"""
from django import template
from weblinks.models import Link

register = template.Library()

@register.inclusion_tag('weblinks/latest_tag.html')
def latest_weblinks():
    links = Link.public_objects.order_by('-date_added')[:10]
    return {
        'links': links,
    }
