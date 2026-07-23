"""
URLs for the forums application.
"""
from django.urls import path, re_path

import forums.views.attachments as attachments
import forums.views.favorites as favorites
import forums.views.main as main
import forums.views.spam as spam
import forums.views.subscriptions as subscriptions


urlpatterns = [
    path('', main.index, name='forums-index'),
    path('catchup/', main.catchup_all, name='forums-catchup_all'),
    path('new-topic-success/<int:tid>', main.new_topic_thanks, name='forums-new_topic_thanks'),
    path('topic/<int:id>/', main.topic_index, name='forums-topic_index'),
    path('topic/<int:id>/unread/', main.topic_unread, name='forums-topic_unread'),
    path('topic/<int:id>/latest/', main.topic_latest, name='forums-topic_latest'),
    path('topic/active/<int:num>/', main.active_topics, name='forums-active_topics'),
    path('delete-post/', main.delete_post, name='forums-delete_post'),
    path('edit/<int:id>/', main.edit_post, name='forums-edit_post'),
    path('flag-post/', main.flag_post, name='forums-flag_post'),
    path('forum/<slug:slug>/', main.forum_index, name='forums-forum_index'),
    path('forum/<slug:slug>/catchup/', main.forum_catchup, name='forums-catchup'),
    path('forum/<slug:slug>/new-topic/', main.new_topic, name='forums-new_topic'),
    path('mod/forum/<slug:slug>/', main.mod_forum, name='forums-mod_forum'),
    path('mod/topic/delete/<int:id>/', main.mod_topic_delete, name='forums-mod_topic_delete'),
    path('mod/topic/lock/<int:id>/', main.mod_topic_lock, name='forums-mod_topic_lock'),
    path('mod/topic/move/<int:id>/', main.mod_topic_move, name='forums-mod_topic_move'),
    path('mod/topic/split/<int:id>/', main.mod_topic_split, name='forums-mod_topic_split'),
    path('mod/topic/stick/<int:id>/', main.mod_topic_stick, name='forums-mod_topic_stick'),
    path('my-posts/', main.my_posts, name='forums-my_posts'),
    path('post/<int:post_id>/', main.goto_post, name='forums-goto_post'),
    path('post/ip/<int:post_id>/', main.post_ip_info, name='forums-post_ip_info'),
    path('post/new/<int:topic_id>/', main.new_post, name='forums-new_post'),
    # Regex kept: the username pattern is length-bounded ({1,30}) and allows
    # '.@+-', which no stock path converter expresses.
    re_path(r'^posts/(?P<username>[\w.@+-]{1,30})/$', main.posts_for_user, name='forums-posts_for_user'),
    path('quick-reply/', main.quick_reply_ajax, name='forums-quick_reply'),
    path('unanswered/', main.unanswered_topics, name='forums-unanswered_topics'),
    path('unread/', main.unread_topics, name='forums-unread_topics'),

    path('favorite/<int:topic_id>/', favorites.favorite_topic, name='forums-favorite_topic'),
    path('favorites/', favorites.manage_favorites, name='forums-manage_favorites'),
    path('favorites/<int:topic_id>/', favorites.favorites_status, name='forums-favorites_status'),
    path('unfavorite/<int:topic_id>/', favorites.unfavorite_topic, name='forums-unfavorite_topic'),

    path('subscribe/<int:topic_id>/', subscriptions.subscribe_topic, name='forums-subscribe_topic'),
    path('subscriptions/', subscriptions.manage_subscriptions, name='forums-manage_subscriptions'),
    path('subscriptions/<int:topic_id>/', subscriptions.subscription_status, name='forums-subscription_status'),
    path('unsubscribe/<int:topic_id>/', subscriptions.unsubscribe_topic, name='forums-unsubscribe_topic'),

    path('spammer/<int:post_id>/', spam.spammer, name='forums-spammer'),
    path('spammer/nailed/<int:spammer_id>/', spam.spammer_nailed, name='forums-spammer_nailed'),
    path('stranger/<int:post_id>/', spam.stranger, name='forums-stranger'),

    path('fetch_attachments/', attachments.fetch_attachments, name='forums-fetch_attachments'),
]
