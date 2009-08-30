"""
URLs for the forums application.
"""
from django.conf.urls.defaults import *

urlpatterns = patterns('forums.views',
    url(r'^$', 'index', name='forums-index'),
    url(r'^new-topic-success/(?P<tid>\d+)$', 'new_topic_thanks', name='forums-new_topic_thanks'),
    url(r'^topic/(?P<id>\d+)/$', 'topic_index', name='forums-topic_index'),
    url(r'^forum/(?P<slug>[\w\d-]+)/$', 'forum_index', name='forums-forum_index'),
    url(r'^forum/(?P<slug>[\w\d-]+)/new-topic/$', 'new_topic', name='forums-new_topic'),
)

