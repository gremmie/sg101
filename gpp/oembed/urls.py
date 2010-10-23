"""
URLs for the oembed application.
"""
from django.conf.urls.defaults import *

urlpatterns = patterns('oembed.views',
    url(r'^fetch/$', 'fetch_media', name='oembed-fetch_media'),
    url(r'^fetch_saved/$', 'fetch_saved_media', name='oembed-fetch_saved_media'),
)
