"""
URLs for the comments application.
"""
from django.conf.urls import url
import django.contrib.contenttypes.views

import comments.views

urlpatterns = [
    url(r'^flag/$', comments.views.flag_comment, name='comments-flag'),
    url(r'^markdown/$', comments.views.markdown_preview,
        name='comments-markdown_preview'),
    url(r'^markdown/v3/$', comments.views.markdown_preview_v3,
        name='comments-markdown_preview_v3'),
    url(r'^post/$', comments.views.post_comment, name='comments-post'),
    url(r'^cr/(\d+)/(\d+)/$',
        django.contrib.contenttypes.views.shortcut,
        name='comments-url-redirect'),
]
