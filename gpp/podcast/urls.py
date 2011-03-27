"""
urls for the podcast application

"""
from django.conf.urls.defaults import *
from django.views.decorators.cache import cache_page

from podcast.views import feed


urlpatterns = patterns('podcast.views',
   url(r'^$', 'index', name='podcast-main'),
   url(r'^(\d+)/$', 'detail', name='podcast-detail'),
   url(r'^feed.xml/$', cache_page(feed, 3600), name='podcast-feed'),
)
