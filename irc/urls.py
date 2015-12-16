"""urls for the IRC application"""
from django.conf.urls import url

import irc.views


urlpatterns = [
   url(r'^$', irc.views.view, name='irc-main'),
]
