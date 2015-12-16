"""
URLs for the forums application.
"""
from django.conf.urls import url

import forums.views.attachments as attachments
import forums.views.favorites as favorites
import forums.views.main as main
import forums.views.spam as spam
import forums.views.subscriptions as subscriptions


urlpatterns = [
    url(r'^$', main.index, name='forums-index'),
    url(r'^catchup/$', main.catchup_all, name='forums-catchup_all'),
    url(r'^new-topic-success/(?P<tid>\d+)$', main.new_topic_thanks, name='forums-new_topic_thanks'),
    url(r'^topic/(?P<id>\d+)/$', main.topic_index, name='forums-topic_index'),
    url(r'^topic/(?P<id>\d+)/unread/$', main.topic_unread, name='forums-topic_unread'),
    url(r'^topic/(?P<id>\d+)/latest/$', main.topic_latest, name='forums-topic_latest'),
    url(r'^topic/active/(\d+)/$', main.active_topics, name='forums-active_topics'),
    url(r'^delete-post/$', main.delete_post, name='forums-delete_post'),
    url(r'^edit/(?P<id>\d+)/$', main.edit_post, name='forums-edit_post'),
    url(r'^flag-post/$', main.flag_post, name='forums-flag_post'),
    url(r'^forum/(?P<slug>[\w\d-]+)/$', main.forum_index, name='forums-forum_index'),
    url(r'^forum/(?P<slug>[\w\d-]+)/catchup/$', main.forum_catchup, name='forums-catchup'),
    url(r'^forum/(?P<slug>[\w\d-]+)/new-topic/$', main.new_topic, name='forums-new_topic'),
    url(r'^mod/forum/(?P<slug>[\w\d-]+)/$', main.mod_forum, name='forums-mod_forum'),
    url(r'^mod/topic/delete/(\d+)/$', main.mod_topic_delete, name='forums-mod_topic_delete'),
    url(r'^mod/topic/lock/(\d+)/$', main.mod_topic_lock, name='forums-mod_topic_lock'),
    url(r'^mod/topic/move/(\d+)/$', main.mod_topic_move, name='forums-mod_topic_move'),
    url(r'^mod/topic/split/(\d+)/$', main.mod_topic_split, name='forums-mod_topic_split'),
    url(r'^mod/topic/stick/(\d+)/$', main.mod_topic_stick, name='forums-mod_topic_stick'),
    url(r'^my-posts/$', main.my_posts, name='forums-my_posts'),
    url(r'^post/(\d+)/$', main.goto_post, name='forums-goto_post'),
    url(r'^post/ip/(\d+)/$', main.post_ip_info, name='forums-post_ip_info'),
    url(r'^post/new/(?P<topic_id>\d+)/$', main.new_post, name='forums-new_post'),
    url(r'^posts/(?P<username>[\w.@+-]{1,30})/$', main.posts_for_user, name='forums-posts_for_user'),
    url(r'^quick-reply/$', main.quick_reply_ajax, name='forums-quick_reply'),
    url(r'^unanswered/$', main.unanswered_topics, name='forums-unanswered_topics'),
    url(r'^unread/$', main.unread_topics, name='forums-unread_topics'),

    url(r'^favorite/(\d+)/$', favorites.favorite_topic, name='forums-favorite_topic'),
    url(r'^favorites/$', favorites.manage_favorites, name='forums-manage_favorites'),
    url(r'^favorites/(\d+)/$', favorites.favorites_status, name='forums-favorites_status'),
    url(r'^unfavorite/(\d+)/$', favorites.unfavorite_topic, name='forums-unfavorite_topic'),

    url(r'^subscribe/(\d+)/$', subscriptions.subscribe_topic, name='forums-subscribe_topic'),
    url(r'^subscriptions/$', subscriptions.manage_subscriptions, name='forums-manage_subscriptions'),
    url(r'^subscriptions/(\d+)/$', subscriptions.subscription_status, name='forums-subscription_status'),
    url(r'^unsubscribe/(\d+)/$', subscriptions.unsubscribe_topic, name='forums-unsubscribe_topic'),

    url(r'^spammer/(\d+)/$', spam.spammer, name='forums-spammer'),
    url(r'^spammer/nailed/(\d+)/$', spam.spammer_nailed, name='forums-spammer_nailed'),
    url(r'^stranger/(\d+)/$', spam.stranger, name='forums-stranger'),

    url(r'^fetch_attachments/$', attachments.fetch_attachments, name='forums-fetch_attachments'),
]
