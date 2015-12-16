"""
urls for the podcast application

"""
from django.conf.urls import url
from django.views.decorators.cache import cache_page

import podcast.views


urlpatterns = [
   url(r'^$', podcast.views.index, name='podcast-main'),
   url(r'^(\d+)/$', podcast.views.detail, name='podcast-detail'),
   url(r'^feed.xml/$', cache_page(3600)(podcast.views.feed), name='podcast-feed'),
]
