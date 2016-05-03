"""
Url patterns for the contests application.

"""
from django.conf.urls import url

import contests.views


urlpatterns = [
   url(r'^$',
       contests.views.ContestListView.as_view(),
       name='contests-index'),

   url(r'^enter/$',
       contests.views.enter,
       name='contests-enter'),

   url(r'^c/(?P<slug>[\w-]+)/$',
       contests.views.ContestDetailView.as_view(),
       name='contests-contest'),
]
