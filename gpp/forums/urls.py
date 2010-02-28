"""
URLs for the forums application.
"""
from django.conf.urls.defaults import *

urlpatterns = patterns('forums.views',
    url(r'^$', 'index', name='forums-index'),
    url(r'^new-topic-success/(?P<tid>\d+)$', 'new_topic_thanks', name='forums-new_topic_thanks'),
    url(r'^topic/(?P<id>\d+)/$', 'topic_index', name='forums-topic_index'),
    url(r'^delete-post/$', 'delete_post', name='forums-delete_post'),
    url(r'^edit/(?P<id>\d+)/$', 'edit_post', name='forums-edit_post'),
    url(r'^flag-post/$', 'flag_post', name='forums-flag_post'),
    url(r'^forum/(?P<slug>[\w\d-]+)/$', 'forum_index', name='forums-forum_index'),
    url(r'^forum/(?P<slug>[\w\d-]+)/catchup/$', 'forum_catchup', name='forums-catchup'),
    url(r'^forum/(?P<slug>[\w\d-]+)/new-topic/$', 'new_topic', name='forums-new_topic'),
    url(r'^mod/forum/(?P<slug>[\w\d-]+)/$', 'mod_forum', name='forums-mod_forum'),
    url(r'^mod/topic/delete/(\d+)/$', 'mod_topic_delete', name='forums-mod_topic_delete'),
    url(r'^mod/topic/lock/(\d+)/$', 'mod_topic_lock', name='forums-mod_topic_lock'),
    url(r'^mod/topic/move/(\d+)/$', 'mod_topic_move', name='forums-mod_topic_move'),
    url(r'^mod/topic/split/(\d+)/$', 'mod_topic_split', name='forums-mod_topic_split'),
    url(r'^mod/topic/stick/(\d+)/$', 'mod_topic_stick', name='forums-mod_topic_stick'),
    url(r'^my-posts/$', 'my_posts', name='forums-my_posts'),
    url(r'^post/(\d+)/$', 'goto_post', name='forums-goto_post'),
    url(r'^post/new/(?P<topic_id>\d+)/$', 'new_post', name='forums-new_post'),
    url(r'^posts/(?P<username>[\w\d-]+)/$', 'posts_for_user', name='forums-posts_for_user'),
    url(r'^quick-reply/$', 'quick_reply_ajax', name='forums-quick_reply'),
    url(r'^unanswered/$', 'unanswered_topics', name='forums-unanswered_topics'),
    url(r'^unread/$', 'unread_topics', name='forums-unread_topics'),
)

