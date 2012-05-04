"""
URLs for the POTD application.
"""
from django.conf.urls import patterns, url

urlpatterns = patterns('potd.views',
    url(r'^$', 'view', name='potd-view'),
    url(r'^archive/(\d+)/$', 'archive', name='potd-archive'),
)
