"""
Signal handlers & signals for the forums application.

"""
from django.db.models.signals import post_save
from django.db.models.signals import post_delete
import django.dispatch

from forums.models import Forum, Topic, Post


def on_topic_save(sender, **kwargs):
    if kwargs['created']:
        topic = kwargs['instance']
        topic.forum.topic_count_update()
        topic.forum.save()


def on_topic_delete(sender, **kwargs):
    topic = kwargs['instance']
    topic.forum.topic_count_update()
    topic.forum.save()
    forums.latest.notify_topic_delete(topic)


def on_post_save(sender, **kwargs):
    if kwargs['created']:
        post = kwargs['instance']

        # update the topic
        post.topic.post_count_update()
        post.topic.save()

        # update the forum
        post.topic.forum.post_count_update()
        post.topic.forum.save()


def on_post_delete(sender, **kwargs):
    post = kwargs['instance']

    # update the topic
    try:
        post.topic.post_count_update()
        post.topic.save()
    except Topic.DoesNotExist:
        pass
    else:
        # update the forum
        try:
            post.topic.forum.post_count_update()
            post.topic.forum.save()
        except Forum.DoesNotExist:
            pass


post_save.connect(on_topic_save, sender=Topic, dispatch_uid='forums.signals')
post_delete.connect(on_topic_delete, sender=Topic, dispatch_uid='forums.signals')

post_save.connect(on_post_save, sender=Post, dispatch_uid='forums.signals')
post_delete.connect(on_post_delete, sender=Post, dispatch_uid='forums.signals')


# Signals for the forums application.
#
# This signal is sent when a topic has had its textual content (title) changed.
# The provided arguments are: 
#   sender - the topic model instance 
#   created - True if the topic is new, False if updated

topic_content_update = django.dispatch.Signal(providing_args=['created'])

# This signal is sent when a post has had its textual content (body) changed.
# The provided arguments are: 
#   sender - the post model instance 
#   created - True if the post is new, False if updated

post_content_update = django.dispatch.Signal(providing_args=['created'])


def notify_new_topic(topic):
    """
    Sends the topic_content_update signal for a new topic instance.

    """
    topic_content_update.send_robust(topic, created=True)


def notify_updated_topic(topic):
    """
    Sends the topic_content_update signal for an updated topic instance.

    """
    topic_content_update.send_robust(topic, created=False)


def notify_new_post(post):
    """
    Sends the post_content_update signal for a new post instance.

    """
    post_content_update.send_robust(post, created=True)


def notify_updated_post(post):
    """
    Sends the post_content_update signal for an updated post instance.

    """
    post_content_update.send_robust(post, created=False)


# Avoid circular imports
import forums.latest
