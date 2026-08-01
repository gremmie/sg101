"""URLs for the search application."""
from django.urls import path

from core.views import FixedView
from search import views


urlpatterns = [
    path('', views.search, name='search'),

    # The forums' duplicate-topic quick search still points at a placeholder;
    # its view is restored separately. Named now so the rename off the dead
    # haystack_* names happens once.
    path('ajax/',
        FixedView.as_view(title='About', content_template='fixed/about.html'),
        name='search_ajax'),
]
