"""urls for the polls application"""
from django.conf.urls import patterns, url

urlpatterns = patterns('polls.views',
    url(r'^$', 'poll_index', name='polls-main'),
    url(r'^(?P<poll_id>\d+)/$', 'poll_detail', name='polls-detail'),
    url(r'^(?P<poll_id>\d+)/vote/$', 'poll_vote', name='polls-vote'),
    url(r'^delete_vote/$', 'poll_delete_vote', name='polls-delete_vote'),
)
