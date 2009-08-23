"""
URLs for the forums application.
"""
from django.conf.urls.defaults import *

urlpatterns = patterns('forums.views',
    url(r'^$', 'index', name='forums-index'),
    url(r'^(?P<slug>[\w\d-]+)/$', 'forum_index', name='forums-forum_index'),
)
