"""
URLs for the oembed application.
"""
from django.conf.urls import patterns, url

urlpatterns = patterns('oembed.views',
    url(r'^fetch/$', 'fetch_media', name='oembed-fetch_media'),
    url(r'^fetch_saved/$', 'fetch_saved_media', name='oembed-fetch_saved_media'),
)
