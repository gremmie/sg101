"""
Template tags for the forums application.
"""
import datetime

from pytz import timezone
from django import template
from django.conf import settings
from django.core.cache import cache
from django.contrib.auth.models import User

from forums.models import Forum
from forums.models import Topic
from forums.models import Post
from forums.models import Category
from forums.stats import retrieve_stats


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


@register.inclusion_tag('forums/last_post_info.html', takes_context=True)
def last_post_info(context, post):
    return {
        'post': post,
        'STATIC_URL': context['STATIC_URL'],
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
        'STATIC_URL': settings.STATIC_URL,
    }


def get_time_prefs(user):
    """
    Return the supplied user's time preferences in the form of a 2-tuple:
        (use_24_time, time_zone_name)

    These preferences are cached to reduce database hits.

    """
    cache_key = '%s_tz_prefs' % user.username
    tz_prefs = cache.get(cache_key)
    if tz_prefs is None:
        profile = user.get_profile()
        tz_prefs = profile.use_24_time, profile.time_zone
        cache.set(cache_key, tz_prefs)

    return tz_prefs


@register.simple_tag
def current_forum_time(user):
    """
    This tag displays the current forum time, adjusted by the user's
    time zone preferences.
    """
    curr_time = SERVER_TZ.localize(datetime.datetime.now())

    if user.is_authenticated():
        tz_prefs = get_time_prefs(user)
        user_tz = timezone(tz_prefs[1])
        curr_time = curr_time.astimezone(user_tz)
        fmt = TIME_FMT_24 if tz_prefs[0] else TIME_FMT_12
    else:
        fmt = TIME_FMT_12

    return '<p>The current time is %s. All times shown are %s.</p>' % (
            curr_time.strftime(fmt), curr_time.strftime('%Z%z'))


@register.simple_tag
def forum_date(date, user, long_format=True):
    """
    This tag displays an arbitrary datetime, adjusted by the user's
    time zone preferences.
    """
    fmt_index = 0 if long_format else 1

    date = SERVER_TZ.localize(date)
    if user.is_authenticated():
        tz_prefs = get_time_prefs(user)
        user_tz = timezone(tz_prefs[1])
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
        'STATIC_URL': settings.STATIC_URL,
    }


@register.inclusion_tag('forums/new_posts_tag.html', takes_context=True)
def new_posts(context):
    """
    This tag displays the topics that have the newest posts.
    Only the "public" forums are displayed.
    """
    public_forum_ids = Forum.objects.public_forum_ids()
    topics = Topic.objects.filter(forum__in=public_forum_ids).select_related(
                'last_post', 'last_post__user').order_by('-update_date')[:10]

    return {
        'topics': topics,
        'user': context['user'],
    }


@register.inclusion_tag('forums/forum_stats_tag.html')
def forum_stats():
    """
    Displays forum statistics.
    """
    post_count = retrieve_stats()

    return {
        'post_count': post_count,
    }


@register.inclusion_tag('forums/topic_icons_tag.html')
def topic_icons(topic):
    """Displays the "unread", "sticky", and "locked" icons for a given topic."""
    return {
        'topic': topic,
        'STATIC_URL': settings.STATIC_URL,
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

    if isinstance(obj, str) or isinstance(obj, unicode):
        nav_list.append(dict(name=obj, url=None))
    elif isinstance(obj, Forum):
        nav_list.append(dict(name=obj.name, url=obj.get_absolute_url()))
    elif isinstance(obj, Topic):
        forum = obj.forum
        nav_list.append(dict(name=forum.name, url=forum.get_absolute_url()))
        nav_list.append(dict(name=obj.name, url=obj.get_absolute_url()))

    if subtitle:
        nav_list.append(dict(name=subtitle, url=None))

    return dict(nav_list=nav_list, STATIC_URL=settings.STATIC_URL)
