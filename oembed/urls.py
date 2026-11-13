"""
URLs for the oembed application.
"""
from django.urls import path

import oembed.views


urlpatterns = [
    path('fetch/', oembed.views.fetch_media, name='oembed-fetch_media'),
]
