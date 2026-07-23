"""
URLs for the oembed application.
"""
from django.urls import path

import oembed.views


urlpatterns = [
    path('fetch/', oembed.views.fetch_media, name='oembed-fetch_media'),
    path('fetch_saved/', oembed.views.fetch_saved_media, name='oembed-fetch_saved_media'),
]
