"""urls for the IRC application"""
from django.conf.urls import patterns, url

urlpatterns = patterns('irc.views',
   url(r'^$', 'view', name='irc-main'),
)
