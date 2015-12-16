"""urls for the polls application"""
from django.conf.urls import url

import polls.views


urlpatterns = [
    url(r'^$', polls.views.poll_index, name='polls-main'),
    url(r'^(?P<poll_id>\d+)/$', polls.views.poll_detail, name='polls-detail'),
    url(r'^(?P<poll_id>\d+)/vote/$', polls.views.poll_vote, name='polls-vote'),
    url(r'^delete_vote/$', polls.views.poll_delete_vote, name='polls-delete_vote'),
]
