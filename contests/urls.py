"""
Url patterns for the contests application.

"""
from django.urls import path

import contests.views


urlpatterns = [
   path('',
       contests.views.ContestListView.as_view(),
       name='contests-index'),

   path('enter/',
       contests.views.enter,
       name='contests-enter'),

   path('c/<slug:slug>/',
       contests.views.ContestDetailView.as_view(),
       name='contests-contest'),
]
