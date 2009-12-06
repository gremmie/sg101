"""
Urls for the core application.
"""
from django.conf.urls.defaults import *

urlpatterns = patterns('core.views',
    url(r'^markdown_help/$', 'markdown_help', name='core-markdown_help'),
)
