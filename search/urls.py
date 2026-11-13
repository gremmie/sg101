"""URLs for the search application."""
from django.urls import path

from search import views


urlpatterns = [
    path('', views.search, name='search'),

    # The path is fixed by sg101/static/js/v3/forums/quick_search.js, which
    # requests '/search/topics/' literally rather than reversing this name.
    path('topics/', views.search_topics, name='search_topics'),
]
