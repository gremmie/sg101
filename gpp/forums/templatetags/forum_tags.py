"""
Template tags for the forums application.
"""
import datetime

from pytz import timezone
from django import template
from django.conf import settings

register = template.Library()


TIME_FMT_24 = "%H:%M"
TIME_FMT_12 = "%I:%M %p"

DATE_FMT = "%b %d %Y"
DATE_FMT_24 = "%s %s" % (DATE_FMT, TIME_FMT_24)
DATE_FMT_12 = "%s %s" % (DATE_FMT, TIME_FMT_12)

SERVER_TZ = timezone(settings.TIME_ZONE)


@register.inclusion_tag('forums/last_post_info.html', takes_context=True)
def last_post_info(context, post):
    return {
        'post': post,
        'MEDIA_URL': context['MEDIA_URL'],
        'user': context['user'],
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


@register.simple_tag
def current_forum_time(user):
    """
    This tag displays the current forum time, adjusted by the user's
    time zone preferences.
    """
    curr_time = SERVER_TZ.localize(datetime.datetime.now())

    if user.is_authenticated():
        profile = user.get_profile()
        user_tz = timezone(profile.time_zone)
        curr_time = curr_time.astimezone(user_tz)
        fmt = TIME_FMT_24 if profile.use_24_time else TIME_FMT_12
    else:
        fmt = TIME_FMT_12

    return 'The current time is %s. All times shown are %s.' % (
            curr_time.strftime(fmt), curr_time.strftime('%Z%z'))


@register.simple_tag
def forum_date(date, user):
    """
    This tag displays an arbitrary datetime, adjusted by the user's
    time zone preferences.
    """
    date = SERVER_TZ.localize(date)
    if user.is_authenticated():
        profile = user.get_profile()
        user_tz = timezone(profile.time_zone)
        date = date.astimezone(user_tz)
        fmt = DATE_FMT_24 if profile.use_24_time else DATE_FMT_12
    else:
        fmt = DATE_FMT_12

    return date.strftime(fmt)


@register.inclusion_tag('forums/show_form.html')
def show_form(legend_text, form, submit_value, is_ajax, media_url):
    """
    This tag displays the common HTML for a forum form.
    """
    return {
        'legend_text': legend_text,
        'form': form,
        'submit_value': submit_value,
        'is_ajax': is_ajax,
        'MEDIA_URL': media_url,
    }
