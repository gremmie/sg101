"""urls for the bandmap application"""
from django.urls import path

import bandmap.views

urlpatterns = [
    path('',
        bandmap.views.map_view,
        name='bandmap-map'),
    path('add/',
        bandmap.views.add_band,
        name='bandmap-add'),
    path('query/',
        bandmap.views.query,
        name='bandmap-query'),
]
