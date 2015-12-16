"""
URLs for the oembed application.
"""
from django.conf.urls import url

import oembed.views


urlpatterns = [
    url(r'^fetch/$', oembed.views.fetch_media, name='oembed-fetch_media'),
    url(r'^fetch_saved/$', oembed.views.fetch_saved_media, name='oembed-fetch_saved_media'),
]
