"""urls for the IRC application"""
from django.conf.urls.defaults import *

urlpatterns = patterns('irc.views',
   url(r'^$', 'view', name='irc-main'),
)
