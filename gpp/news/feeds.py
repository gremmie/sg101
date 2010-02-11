"""
This file contains the feed classes for the news application.
"""
import datetime

from django.contrib.syndication.feeds import Feed

from news.models import Story

BASE_YEAR = 2010


class LatestNewsFeed(Feed):
    """The Feed class for the news application"""

    title = 'SurfGuitar101.com News Feed'
    link = '/feeds/news/'
    description = 'News articles and stories from SurfGuitar101.com'
    ttl = '720'

    title_template = 'news/feed_title.html'
    description_template = 'news/feed_description.html'

    def copyright(self):
        curr_year = datetime.datetime.now().year
        if curr_year == BASE_YEAR:
            year_range = str(BASE_YEAR)
        else:
            year_range = "%d - %d" % (BASE_YEAR, curr_year)

        return 'Copyright (C) %s, SurfGuitar101.com' % year_range
    
    def items(self):
        return Story.objects.order_by('-date_published')[:5]

    def item_pubdate(self, item):
        return item.date_published

    def item_categories(self, item):
        return (item.category.title, )
