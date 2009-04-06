"""
This file contains the feed classes for the news application.
"""

from django.contrib.syndication.feeds import Feed
from news.models import Story


class LatestNewsFeed(Feed):
   """The Feed class for the news application"""

   title = 'SurfGuitar101.com News Feed'
   link = '/feeds/news/'
   description = 'News articles and stories from SurfGuitar101.com'
   copyright = 'Copyright (C) 2008, Brian Neal'
   ttl = '720'

   title_template = 'news/feed_title.html'
   description_template = 'news/feed_description.html'
   
   def items(self):
      return Story.objects.order_by('-date_published')[:5]

   def item_pubdate(self, item):
      return item.date_published

   def item_categories(self, item):
      return (item.category.title, )
