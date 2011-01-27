"""
Template tags for the news application.
"""
import datetime

from django import template
from django.conf import settings

from news.models import Story


register = template.Library()


@register.inclusion_tag('news/current_news.html')
def current_news():
    stories = Story.objects.exclude(
            front_page_expiration__lt=datetime.date.today())[:10]
    return {
        'stories': stories,
        'STATIC_URL': settings.STATIC_URL,
        'on_home': True,
    }
