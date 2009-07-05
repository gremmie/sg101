"""
Signal handlers for the forums application.
"""
from django.db.models.signals import post_save
from django.db.models.signals import post_delete
from models import Topic
from models import Post


def on_topic_save(sender, **kwargs):
    if kwargs['created']:
        topic = kwargs['instance']
        topic.forum.topic_count_update()
        topic.forum.save()


def on_topic_delete(sender, **kwargs):
    topic = kwargs['instance']
    topic.forum.topic_count_update()
    topic.forum.save()


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
    post.topic.post_count_update()
    post.topic.save()

    # update the forum
    post.topic.forum.post_count_update()
    post.topic.forum.save()


post_save.connect(on_topic_save, sender=Topic)
post_delete.connect(on_topic_delete, sender=Topic)

post_save.connect(on_post_save, sender=Post)
post_delete.connect(on_post_delete, sender=Post)
