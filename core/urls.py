"""
Urls for the core application.
"""
from django.urls import path

import core.views


urlpatterns = [
    path('markdown_help/', core.views.markdown_help, name='core-markdown_help'),
    path('ajax/users/', core.views.ajax_users, name='core-ajax_users'),
]
