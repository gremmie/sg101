"""
This file contains the feed classes for the news application.
"""
from django.contrib.syndication.views import Feed

from news.models import Story
from core.functions import get_full_name
from core.functions import copyright_str


class LatestNewsFeed(Feed):
    """The Feed class for the news application"""

    title = 'SurfGuitar101.com News Feed'
    link = '/feeds/news/'
    description = 'News articles and stories from SurfGuitar101.com'
    ttl = '720'
    author_name = 'Brian Neal'
    author_email = 'admin@surfguitar101.com'

    def feed_copyright(self):
        return copyright_str()
    
    def items(self):
        return Story.objects.order_by('-date_submitted')[:5]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.short_text + item.long_text

    def item_author_name(self, item):
        return get_full_name(item.submitter)

    def item_pubdate(self, item):
        return item.date_submitted

    def item_categories(self, item):
        return (item.category.title, )
