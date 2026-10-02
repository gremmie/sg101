"""
Signal handlers for the forums application.

"""
from django.db.models.signals import post_save
from django.db.models.signals import post_delete

from forums.models import Forum, Topic, Post
import forums.latest


# What Topic.post_count_update() changes. Saving only these keeps a reply's
# bookkeeping from writing back the rest of the topic, and from reading as an
# edit to the search index.
POST_COUNT_FIELDS = ['post_count', 'last_post', 'update_date']


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
        post.topic.save(update_fields=POST_COUNT_FIELDS)

        # update the forum
        post.topic.forum.post_count_update()
        post.topic.forum.save()


def on_post_delete(sender, **kwargs):
    post = kwargs['instance']

    # update the topic
    try:
        post.topic.post_count_update()
        post.topic.save(update_fields=POST_COUNT_FIELDS)
    except Topic.DoesNotExist:
        pass
    else:
        # update the forum
        try:
            post.topic.forum.post_count_update()
            post.topic.forum.save()
        except Forum.DoesNotExist:
            pass


post_save.connect(on_topic_save, sender=Topic, dispatch_uid='forums.receivers')
post_delete.connect(on_topic_delete, sender=Topic, dispatch_uid='forums.receivers')
post_save.connect(on_post_save, sender=Post, dispatch_uid='forums.receivers')
post_delete.connect(on_post_delete, sender=Post, dispatch_uid='forums.receivers')
