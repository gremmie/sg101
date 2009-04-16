"""
Urls for the Shoutbox application.
"""

from django.conf.urls.defaults import *

urlpatterns = patterns('shoutbox.views',
    url(r'^delete/$', 'delete', name='shoutbox-delete'),
    url(r'^edit/$', 'edit', name='shoutbox-edit'),
    url(r'^flag/$', 'flag', name='shoutbox-flag'),
    url(r'^shout/$', 'shout', name='shoutbox-shout'),
    url(r'^text/$', 'text', name='shoutbox-text'),
    url(r'^view/(\d+)/$', 'view_shout', name='shoutbox-view'),
    url(r'^view/history/(?P<page>\d+)/$', 'view_history', name='shoutbox-history'),
)

# vim: ts=4 sw=4
