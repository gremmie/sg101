"""
Urls for the core application.
"""
from django.conf.urls import url

import core.views


urlpatterns = [
    url(r'^markdown_help/$', core.views.markdown_help, name='core-markdown_help'),
    url(r'^ajax/users/$', core.views.ajax_users, name='core-ajax_users'),
]
