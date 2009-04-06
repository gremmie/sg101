"""urls for the polls application"""
from django.conf.urls.defaults import *

urlpatterns = patterns('polls.views',
   url(r'^$', 'poll_index', name='polls-main'),
   (r'^(?P<poll_id>\d+)/$', 'poll_detail'),
   (r'^(?P<poll_id>\d+)/results/$', 'poll_results'),
   (r'^(?P<poll_id>\d+)/vote/$', 'poll_vote'),
)
