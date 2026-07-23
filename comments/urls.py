"""
URLs for the comments application.
"""
from django.urls import path
import django.contrib.contenttypes.views

import comments.views

urlpatterns = [
    path('flag/', comments.views.flag_comment, name='comments-flag'),
    path('markdown/', comments.views.markdown_preview,
        name='comments-markdown_preview'),
    path('markdown/v3/', comments.views.markdown_preview_v3,
        name='comments-markdown_preview_v3'),
    path('post/', comments.views.post_comment, name='comments-post'),
    path('cr/<int:content_type_id>/<int:object_id>/',
        django.contrib.contenttypes.views.shortcut,
        name='comments-url-redirect'),
]
