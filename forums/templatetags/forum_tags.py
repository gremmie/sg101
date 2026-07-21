"""
Template tags for the forums application.
"""
import datetime

from pytz import timezone, UnknownTimeZoneError
from django import template
from django.conf import settings

from forums.models import Forum
from forums.models import Topic
from forums.latest import get_stats, get_latest_topics


register = template.Library()

TIME_FMT_24 = "%H:%M"
TIME_FMT_12 = "%I:%M %p"

DATE_FMT = "%b %d %Y"
SHORT_DATE_FMT = "%b %d"

DATE_FMT_24 = (
    "%s %s" % (DATE_FMT, TIME_FMT_24),          # long format
    "%s %s" % (TIME_FMT_24, SHORT_DATE_FMT),    # short format
)
DATE_FMT_12 = (
    "%s %s" % (DATE_FMT, TIME_FMT_12),          # long format
    "%s %s" % (TIME_FMT_12, SHORT_DATE_FMT),    # short format
)

SERVER_TZ = timezone(settings.TIME_ZONE)
DEFAULT_TZ = timezone('US/Pacific')


@register.inclusion_tag('forums/last_post_info.html', takes_context=True)
def last_post_info(context, post):
    return {
        'post': post,
        'user': context['user'],
    }


@register.inclusion_tag('forums/pagination.html')
def forum_page_navigation(page):
    return {'page': page}


@register.inclusion_tag('forums/post_edit_button.html')
def post_edit_button(post, user, can_moderate):
    show_button = post.user.id == user.id or can_moderate
    return {
        'post': post,
        'show_button': show_button,
    }


def get_time_prefs(user):
    """
    Return the supplied user's time preferences in the form of a 2-tuple:
        (use_24_time, time_zone_name)
    """
    profile = user.profile
    return profile.use_24_time, profile.time_zone


@register.simple_tag
def current_forum_time(user):
    """
    This tag displays the current forum time, adjusted by the user's
    time zone preferences.
    """
    curr_time = SERVER_TZ.localize(datetime.datetime.now())

    if user.is_authenticated:
        tz_prefs = get_time_prefs(user)
        try:
            user_tz = timezone(tz_prefs[1])
        except UnknownTimeZoneError:
            user_tz = DEFAULT_TZ
        curr_time = curr_time.astimezone(user_tz)
        fmt = TIME_FMT_24 if tz_prefs[0] else TIME_FMT_12
    else:
        fmt = TIME_FMT_12

    return 'The current time is %s. All times shown are %s.' % (
            curr_time.strftime(fmt), curr_time.strftime('%Z%z'))


@register.simple_tag
def forum_date(date, user, long_format=True, none_date_retval=u'Never'):
    """
    This tag displays an arbitrary datetime, adjusted by the user's
    time zone preferences.
    """
    if date is None:
        return none_date_retval

    fmt_index = 0 if long_format else 1

    date = SERVER_TZ.localize(date)
    if user.is_authenticated:
        tz_prefs = get_time_prefs(user)
        try:
            user_tz = timezone(tz_prefs[1])
        except UnknownTimeZoneError:
            user_tz = DEFAULT_TZ
        date = date.astimezone(user_tz)
        fmt = DATE_FMT_24 if tz_prefs[0] else DATE_FMT_12
    else:
        fmt = DATE_FMT_12

    return date.strftime(fmt[fmt_index])


@register.inclusion_tag('forums/show_form.html')
def show_form(legend_text, form, submit_value, is_ajax):
    """
    This tag displays the common HTML for a forum form.
    """
    return {
        'legend_text': legend_text,
        'form': form,
        'submit_value': submit_value,
        'is_ajax': is_ajax,
    }


@register.inclusion_tag('forums/new_posts_tag.html')
def new_posts():
    """
    This tag displays the topics that have the newest posts.
    Only the "public" forums are displayed.
    """
    return {
        'topics': get_latest_topics(20),
    }


@register.inclusion_tag('forums/forum_stats_tag.html')
def forum_stats():
    """
    Displays forum statistics.
    """
    topic_count, post_count = get_stats()

    return {
        'topic_count': topic_count,
        'post_count': post_count,
    }


@register.inclusion_tag('forums/topic_icons_tag.html')
def topic_icons(topic):
    """Displays the "unread", "sticky", and "locked" icons for a given topic."""
    return {
        'topic': topic,
    }


@register.inclusion_tag('forums/topic_page_range_tag.html')
def topic_page_range(topic):
    """Displays the page range links for a topic."""
    return {
        'topic': topic,
    }


@register.inclusion_tag('forums/navigation_tag.html')
def forum_navigation(obj, subtitle=None):
    """
    Generates forum navigation links based upon the arguments passed.
    If obj is:
        * a string: Index >> String Text
        * a forum:  Index >> Forum Name
        * a topic:  Index >> Forum Name >> Topic Name

    If the optional subtitle argument is passed, it is assumed to be
    a string, and is added as one more "level" in the navigation.

    """
    nav_list = []

    if isinstance(obj, str):
        nav_list.append(dict(name=obj, url=None))
    elif isinstance(obj, Forum):
        nav_list.append(dict(name=obj.name, url=obj.get_absolute_url()))
    elif isinstance(obj, Topic):
        forum = obj.forum
        nav_list.append(dict(name=forum.name, url=forum.get_absolute_url()))
        nav_list.append(dict(name=obj.name, url=obj.get_absolute_url()))

    if subtitle:
        nav_list.append(dict(name=subtitle, url=None))

    return dict(nav_list=nav_list)
