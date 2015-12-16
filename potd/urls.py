"""
URLs for the POTD application.
"""
from django.conf.urls import url

import potd.views


urlpatterns = [
    url(r'^$', potd.views.view, name='potd-view'),
    url(r'^archive/(\d+)/$', potd.views.archive, name='potd-archive'),
]
