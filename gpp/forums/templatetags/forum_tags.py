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


@register.inclusion_tag('forums/post_edit_button.html')
def post_edit_button(post, user, can_moderate, media_url):
    show_button = post.user.id == user.id or can_moderate
    return {
        'post': post,
        'show_button': show_button,
        'MEDIA_URL': media_url,
    }
