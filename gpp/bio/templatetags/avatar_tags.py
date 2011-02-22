"""
Template tags for the bio application.
"""
from django import template
from django.conf import settings
from django.core.cache import cache

from bio.models import UserProfile


register = template.Library()


def get_img_info(profile=None):
    """
    This function returns a 3-tuple: (url, width, height) for a user profile
    avatar. If the profile is None or the profile doesn't contain a valid
    avatar, info for the default avatar is returned.

    """
    if profile is None or profile.avatar.name == '':
        return (settings.AVATAR_DEFAULT_URL,
                settings.MAX_AVATAR_SIZE_PIXELS,
                settings.MAX_AVATAR_SIZE_PIXELS)
    else:
        return (profile.avatar.url,
                profile.avatar.width,
                profile.avatar.height)


@register.simple_tag
def avatar(user, align='bottom'):
    """
    Returns the HTML for a user's avatar image.

    If the user object has an attribute 'user_profile', this is assumed to be
    the user's profile that has been pre-fetched. Otherwise, the cache is
    consulted to retrieve the avatar info for the user. If there is a cache
    miss, only then will a get_profile() call be made.
    """
    # img_info is a tuple that contains info about the avatar:
    # (url, width, height)

    if hasattr(user, 'user_profile'):
        img_info = get_img_info(user.user_profile)
    else:
        # try the cache
        cache_key = 'avatar_' + user.username
        img_info = cache.get(cache_key)
        if img_info is None:
            try:
                profile = user.get_profile()
            except UserProfile.DoesNotExist:
                profile = None

            img_info = get_img_info(profile)
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
