"""
Template tags for the news application.
"""
import datetime

from django import template

from news.models import Story
from news.utils import attach_extra_attrs


register = template.Library()


@register.inclusion_tag('news/current_news.html')
def current_news():
    # Defer the tags field because we are going to get all the
    # tags out in 1 query later...
    stories = Story.objects.defer('tags')\
            .exclude(front_page_expiration__lt=datetime.date.today())\
            .select_related('forums_topic')\
            .order_by('-priority', '-date_submitted')[:10]

    attach_extra_attrs(stories)

    return {
        'stories': stories,
        'on_home': True,
    }
