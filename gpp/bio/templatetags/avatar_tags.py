"""
Template tags for the bio application. 
"""
from django import template
from django.conf import settings
from django.core.cache import cache

register = template.Library()


@register.simple_tag
def avatar(user, align='bottom'):
    """Returns the HTML for a user's avatar image."""

    # In the cache is stored a tuple containing info about the 
    # avatar: (url, width, height)
    cache_key = 'avatar_' + user.username
    img_info = cache.get(cache_key)
    if img_info is None:
        try:
            profile = user.get_profile()
        except:
            profile = None
        if profile is None or profile.avatar.name == '':
            img_info = (settings.AVATAR_DEFAULT_URL, 
                settings.MAX_AVATAR_SIZE_PIXELS, 
                settings.MAX_AVATAR_SIZE_PIXELS)
        else:
            img_info = (profile.avatar.url, profile.avatar.width,
                profile.avatar.height)
        cache.set(cache_key, img_info)

    alt = user.username
    title = alt

    style = ''
    if align == 'left':
      style = 'style="float:left;margin-right:3px;"'
    # other styles not supported

    img_tag = (u'<img src="%s" alt="%s" title="%s" width="%s" height="%s" '
                'border="0" class="avatar" %s />') % (
         img_info[0], alt, title, img_info[1], img_info[2], style)
    return img_tag
