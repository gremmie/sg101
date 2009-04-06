"""
URLs for the comments application.
"""
from django.conf.urls.defaults import *

urlpatterns = patterns('comments.views',
    url(r'^flag/$', 'flag_comment', name='comments-flag'),
    url(r'^markdown/$', 'markdown_preview', name='comments-markdown_preview'),
    url(r'^post/$', 'post_comment', name='comments-post'),
)
