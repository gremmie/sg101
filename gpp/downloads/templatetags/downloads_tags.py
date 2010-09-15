"""
Template tags for the downloads application.
"""
from django import template

from downloads.models import Download


register = template.Library()


@register.inclusion_tag('downloads/latest_tag.html')
def latest_downloads():
    downloads = Download.public_objects.order_by('-date_added')[:10]
    return {
        'downloads': downloads,
    }
