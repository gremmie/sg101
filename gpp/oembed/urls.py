"""
URLs for the oembed application.
"""
from django.conf.urls.defaults import *

urlpatterns = patterns('oembed.views',
    url(r'^fetch/$', 'fetch_media', name='oembed-fetch_media'),
)
