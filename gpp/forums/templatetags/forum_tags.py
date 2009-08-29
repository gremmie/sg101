"""
Template tags for the forums application.
"""
from django import template

register = template.Library()


@register.inclusion_tag('forums/last_post_info.html')
def last_post_info(post):
    return {'post': post}
