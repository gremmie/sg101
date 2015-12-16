"""
URLs for the member map application.
"""
from django.conf.urls import url

import membermap.views

urlpatterns = [
    url(r'^$', membermap.views.index, name='membermap-index'),
    url(r'^add/$', membermap.views.add, name='membermap-add'),
    url(r'^delete/$', membermap.views.delete, name='membermap-delete'),
    url(r'^query/$', membermap.views.query, name='membermap-query'),
]
