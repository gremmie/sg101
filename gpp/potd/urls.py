"""
URLs for the POTD application.
"""
from django.conf.urls.defaults import *

urlpatterns = patterns('potd.views',
    url(r'^$', 'view', name='potd-view'),
)
