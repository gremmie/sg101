"""
URLs for the POTD application.
"""
from django.urls import path

import potd.views


urlpatterns = [
    path('', potd.views.view, name='potd-view'),
    path('archive/<int:id>/', potd.views.archive, name='potd-archive'),
]
