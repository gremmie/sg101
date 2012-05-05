"""
URLs for the member map application.
"""
from django.conf.urls import patterns, url

urlpatterns = patterns('membermap.views',
    url(r'^$', 'index', name='membermap-index'),
    url(r'^add/$', 'add', name='membermap-add'),
    url(r'^delete/$', 'delete', name='membermap-delete'),
    url(r'^query/$', 'query', name='membermap-query'),
)
