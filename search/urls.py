"""URLs for the search application."""
from django.urls import path

from search import views


urlpatterns = [
    path('', views.search, name='search'),

    # The path is fixed by forums/static/js/forums.js, which requests
    # '/search/topics/' literally rather than reversing this name.
    path('topics/', views.search_topics, name='search_topics'),
]
