"""urls for the podcast application"""
from django.conf.urls.defaults import *

urlpatterns = patterns('podcast.views',
   url(r'^$', 'index', name='podcast-main'),
   (r'^(\d+)/$', 'detail'),
   (r'^feed.xml/$', 'feed'),
)
