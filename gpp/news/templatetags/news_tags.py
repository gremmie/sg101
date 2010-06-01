"""
Template tags for the news application.
"""
import datetime

from django import template

from news.models import Story


register = template.Library()


@register.inclusion_tag('news/current_news.html', takes_context=True)
def current_news(context):
    stories = Story.objects.exclude(
            front_page_expiration__lt=datetime.date.today())[:10]
    return {
        'stories': stories,
        'MEDIA_URL': context['MEDIA_URL'],
        'on_home': True,
    }
