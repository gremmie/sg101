"""
Urls for the core application.
"""
from django.conf.urls import patterns, url

urlpatterns = patterns('core.views',
    url(r'^markdown_help/$', 'markdown_help', name='core-markdown_help'),
    url(r'^ajax/users/$', 'ajax_users', name='core-ajax_users'),
)
