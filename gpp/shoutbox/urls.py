"""
Urls for the Shoutbox application.
"""

from django.conf.urls.defaults import *

urlpatterns = patterns('shoutbox.views',
    url(r'^delete/$', 'delete', name='shoutbox-delete'),
    url(r'^edit/$', 'edit', name='shoutbox-edit'),
    url(r'^shout/$', 'shout', name='shoutbox-shout'),
    url(r'^text/$', 'text', name='shoutbox-text'),
    url(r'^view/(?P<page>\d+)/$', 'view', name='shoutbox-view'),
)
