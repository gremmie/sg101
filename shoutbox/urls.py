"""
Urls for the Shoutbox application.
"""

from django.conf.urls import url

import shoutbox.views


urlpatterns = [
    url(r'^delete/$', shoutbox.views.delete, name='shoutbox-delete'),
    url(r'^edit/$', shoutbox.views.edit, name='shoutbox-edit'),
    url(r'^flag/$', shoutbox.views.flag, name='shoutbox-flag'),
    url(r'^shout/$', shoutbox.views.shout, name='shoutbox-shout'),
    url(r'^text/$', shoutbox.views.text, name='shoutbox-text'),
    url(r'^view/(\d+)/$', shoutbox.views.view_shout, name='shoutbox-view'),
    url(r'^view/history/$', shoutbox.views.view_history, name='shoutbox-history'),
]
