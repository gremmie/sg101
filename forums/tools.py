"""
This module contains misc. utility functions for forum management.
"""
import logging

from forums.models import Post, Topic, Forum, ForumLastVisit, TopicLastVisit
from forums.signals import notify_new_topic, notify_new_post


def delete_user_posts(user):
    """
    This function deletes all the posts for a given user.
    It also cleans up any last visit database records for the user.
    This function adjusts the last post foreign keys before deleting
    the posts to avoid the cascading delete behavior.
    """
    posts = Post.objects.filter(user=user).select_related()

    # delete attachments
    for post in posts:
        post.attachments.clear()

    # build a set of topics and forums affected by the post deletions

    topics = set(post.topic for post in posts)
    forums = set(topic.forum for topic in topics)

    post_ids = [post.pk for post in posts]
    pending_delete = []

    for topic in topics:
        if topic.last_post.pk in post_ids:
            topic_posts = Post.objects.filter(topic=topic).exclude(
                    pk__in=post_ids)
            topic.post_count = topic_posts.count()
            if topic.post_count > 0:
                topic.last_post = topic_posts.latest()
                topic.update_date = topic.last_post.creation_date
                topic.save()
            else:
                # Topic should be deleted, it has no posts;
                # We can't delete it now as it could cascade and take out a 
                # forum. Remember it for later deletion.
                pending_delete.append(topic)

    for forum in forums:
        if forum.last_post.pk in post_ids:
            forum_posts = Post.objects.filter(topic__forum=forum).exclude(
                    pk__in=post_ids)
            forum.post_count = forum_posts.count()
            if forum.post_count > 0:
                forum.last_post = forum_posts.latest()
            else:
                forum.last_post = None
            forum.save()

    # Delete pending topics now because forums have just adjusted their
    # foreign keys into Post
    if pending_delete:
        topic_ids = [topic.pk for topic in pending_delete]
        Topic.objects.filter(pk__in=topic_ids).delete()

        # Topics have been deleted, re-compute topic counts for forums
        for forum in forums:
            forum.topic_count = Topic.objects.filter(forum=forum).count()
            forum.save()

    # All foreign keys are accounted for, we can now delete the posts in bulk.
    # Since some posts in our original queryset may have been deleted already,
    # run a new query (although it may be ok)
    Post.objects.filter(pk__in=post_ids).delete()

    # delete all the last visit records for this user
    TopicLastVisit.objects.filter(user=user).delete()
    ForumLastVisit.objects.filter(user=user).delete()


def create_topic(forum_slug, user, topic_name, post_body, ip='', sticky=False,
        locked=False):
    """Programmatically create a topic & first post in a given forum.

    This function creates a new topic in the forum that has the slug
    specified by the 'forum_slug' argument. Other arguments are as follows:
    'user' - create the topic and post with this user as the owner
    'topic_name' - topic name (title)
    'post_body' - topic post body (as markup, not HTML)
    'ip' - IP address for the post (as a string)
    'sticky' - if True, the post will be stickied
    'locked' - if True, the post will be locked

    """
    try:
        forum = Forum.objects.get(slug=forum_slug)
    except Forum.DoesNotExist:
        logging.error('could not create_topic for forum_slug=%s', forum_slug)
        raise

    topic = Topic(forum=forum,
            name=topic_name,
            user=user,
            sticky=sticky,
            locked=locked)
    topic.save()

    post = Post(topic=topic,
            user=user,
            body=post_body,
            user_ip=ip)
    post.save()

    notify_new_topic(topic)
    notify_new_post(post)


def auto_favorite(post):
    """
    Given a newly created post, perform an auto-favorite action if the post
    creator has that option set in their profile.

    """
    profile = post.user.get_profile()
    if profile.auto_favorite:
        post.topic.bookmarkers.add(post.user)


def auto_subscribe(post):
    """
    Given a newly created post, perform an auto-subscribe action if the post
    creator has that option set in their profile.

    """
    profile = post.user.get_profile()
    if profile.auto_subscribe:
        post.topic.subscribers.add(post.user)
