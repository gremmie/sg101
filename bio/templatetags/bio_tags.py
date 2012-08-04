"""
Template tags for the bio application.
"""
from django import template
from django.conf import settings
from django.core.cache import cache
from django.db.models import Count

import bio.flags
import bio.models
from bio.models import UserProfile


register = template.Library()


def get_img_url(profile=None):
    """
    This function returns a URL for a user profile avatar. 
    If the profile is None or the profile doesn't contain a valid
    avatar, the URL for the default avatar is returned.

    """
    if profile is None or profile.avatar.name == '':
        return settings.AVATAR_DEFAULT_URL
    else:
        return profile.avatar.url


@register.inclusion_tag('bio/avatar_tag.html')
def avatar(user, profile_link=True, align='bottom'):
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
        img_url = get_img_url(user.user_profile)
    else:
        # try the cache
        cache_key = 'avatar_' + user.username
        img_url = cache.get(cache_key)
        if img_url is None:
            try:
                profile = user.get_profile()
            except UserProfile.DoesNotExist:
                profile = None

            img_url = get_img_url(profile)
            cache.set(cache_key, img_url)

    title = user.username
    style = ''
    if align == 'left':
      style = 'style="float:left;margin-right:3px;"'
    # other styles not supported

    return {
        'url': img_url,
        'title': title,
        'style': style,
        'username': user.username,
        'profile_link': profile_link,
    }


@register.inclusion_tag('bio/profile_link_tag.html')
def profile_link(username, trailing_text=''):
    """
    Renders a link to a given user's profile page.
    Trailing text is any text that you want displayed after the final </a> tag.
    Because of the way the Django template system works, a newline will
    automatically be inserted after this tag is expanded. If you want a period
    to follow immediately after the link, then set trailing_text to '.'.
    Otherwise a space will appear between the linked text and any text that
    follows the tag.

    """
    return {'username': username, 'trailing_text': trailing_text }


@register.simple_tag
def profile_status(profile):
    """Returns a string to indicate member status for use on the view profile
    page.

    """
    if (profile.status == bio.models.STA_ACTIVE or
        profile.status == bio.models.STA_STRANGER):
        return u''
    else:
        return u'(%s)' % profile.get_status_display()


@register.inclusion_tag('bio/flag_icon.html')
def flag_icon(code, size='small'):
    """Renders a flag icon for the requested ISO-3166-1 alpha 2
    code.

    """
    try:
        name = bio.flags.FLAG_DATA[code]
    except KeyError:
        code = 'zz'
        name = ''

    return {
        'code': code,
        'name': name,
        'size': size,
        'STATIC_URL': settings.STATIC_URL,
    }


@register.inclusion_tag('bio/member_flags_tag.html')
def member_flags():
    """Displays a list of member flags."""

    flag_data = UserProfile.objects.exclude(country='').values('country').\
            annotate(count=Count('country')).order_by('country')

    for rec in flag_data:
        rec['name'] = bio.flags.FLAG_DATA[rec['country']]

    return {
        'flag_data': flag_data,
        'STATIC_URL': settings.STATIC_URL,
    }
