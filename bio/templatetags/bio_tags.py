"""
Template tags for the bio application.
"""
from django import template
from django.conf import settings
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
    Renders a user's avatar image.

    For best results, ensure the user's profile has already been loaded (perhaps
    via a select_related()). We no longer cache the avatar url because with
    proper use of select_related we will have the user profile already so there
    is no need to go spend time checking the cache.

    """
    img_url = get_img_url(user.profile)

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
        src = None
    else:
        n = '24' if size == 'small' else '64'
        src = "flags/{n}/{code}.png".format(n=n, code=code)

    return {
        'src': src,
        'name': name,
    }


@register.inclusion_tag('bio/member_flags_tag.html')
def member_flags():
    """Displays a list of member flags."""

    flag_data = UserProfile.objects.exclude(country='').values('country').\
            annotate(count=Count('country')).order_by('country')

    for rec in flag_data:
        country = rec['country']
        rec['name'] = bio.flags.FLAG_DATA[country]
        rec['src'] = "flags/24/{}.png".format(country)

    return {
        'flag_data': flag_data,
    }
