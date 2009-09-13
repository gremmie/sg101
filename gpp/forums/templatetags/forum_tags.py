"""
Template tags for the forums application.
"""
from django import template

register = template.Library()


@register.inclusion_tag('forums/last_post_info.html')
def last_post_info(post, media_url):
    return {
        'post': post,
        'MEDIA_URL': media_url,
    }


@register.inclusion_tag('forums/pagination.html')
def forum_page_navigation(page):
    return {'page': page}
