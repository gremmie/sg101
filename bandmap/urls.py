"""urls for the bandmap application"""
from django.conf.urls import url

import bandmap.views

urlpatterns = [
    url(r'^$',
        bandmap.views.map_view,
        name='bandmap-map'),
    url(r'^add/$',
        bandmap.views.add_band,
        name='bandmap-add'),
    url(r'^query/$',
        bandmap.views.query,
        name='bandmap-query'),
]
