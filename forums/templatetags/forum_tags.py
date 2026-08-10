"""
Template tags for the forums application.
"""
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django import template
from django.utils import timezone

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

# Where to render times for a user whose stored zone name is unusable. This is
# a "backward" name that only the tzdata package carries -- see the note on the
# tzdata pin in requirements.txt.
DEFAULT_TZ = ZoneInfo('US/Pacific')


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
        (time zone to display in, use_24_time)
    """
    profile = user.profile
    try:
        user_tz = ZoneInfo(profile.time_zone)
    except (ZoneInfoNotFoundError, ValueError):
        # Two exception types, not one: ZoneInfo raises ZoneInfoNotFoundError
        # for a name it does not know, but ValueError for anything empty or
        # path-shaped. time_zone is a free-text column older than the form
        # validation in front of it, so both are reachable.
        user_tz = DEFAULT_TZ
    return user_tz, profile.use_24_time


@register.simple_tag
def current_forum_time(user):
    """
    This tag displays the current forum time, adjusted by the user's
    time zone preferences.
    """
    if user.is_authenticated:
        user_tz, use_24_time = get_time_prefs(user)
        fmt = TIME_FMT_24 if use_24_time else TIME_FMT_12
    else:
        user_tz, fmt = None, TIME_FMT_12

    # localtime(x, None) renders in the current timezone, which is TIME_ZONE --
    # the same thing anonymous visitors saw when this converted by hand.
    curr_time = timezone.localtime(timezone.now(), user_tz)

    return 'The current time is %s. All times shown are %s.' % (
            curr_time.strftime(fmt), curr_time.strftime('%Z%z'))


@register.simple_tag
def forum_date(date, user, long_format=True, none_date_retval='Never'):
    """
    This tag displays an arbitrary datetime, adjusted by the user's
    time zone preferences.
    """
    if date is None:
        return none_date_retval

    if user.is_authenticated:
        user_tz, use_24_time = get_time_prefs(user)
        fmt = DATE_FMT_24 if use_24_time else DATE_FMT_12
    else:
        user_tz, fmt = None, DATE_FMT_12

    date = timezone.localtime(date, user_tz)

    return date.strftime(fmt[0 if long_format else 1])


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
