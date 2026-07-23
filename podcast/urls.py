"""
urls for the podcast application

"""
from django.urls import path
from django.views.decorators.cache import cache_page

import podcast.views


urlpatterns = [
   path('', podcast.views.index, name='podcast-main'),
   path('<int:id>/', podcast.views.detail, name='podcast-detail'),
   path('feed.xml/', cache_page(3600)(podcast.views.feed), name='podcast-feed'),
]
