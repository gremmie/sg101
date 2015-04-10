"""This module contains a custom Haystack signal processing class to update the
search index in realtime. We update our search index by enqueuing edits and
deletes into a queue for batch processing. Our class ensures we only enqueue
content that should be in the search index.

"""
from django.db.models import signals
import queued_search.signals
import haystack

from bio.signals import profile_content_update
from forums.signals import topic_content_update, post_content_update

import ygroup.models
from weblinks.models import Link
from podcast.models import Item
from news.models import Story
from downloads.models import Download
from forums.models import Forum, Topic, Post
from bio.models import UserProfile


UID = 'custom_search.signals'


class QueuedSignalProcessor(queued_search.signals.QueuedSignalProcessor):
    """
    This customized version of queued_search's QueuedSignalProcessor
    conditionally enqueues items to be indexed.

    """
    def __init__(self, *args, **kwargs):

        # We assume that it is okay to attempt to delete a model from the search
        # index even if the model object is not in the index. In other words,
        # attempting to delete an object from the index will not cause any
        # errors if it is not in the index. Thus if we see an object that has an
        # 'is_public' attribute, and it is false, we can safely enqueue a delete
        # in case the 'is_public' attribute just went from True to False. We
        # have no way of knowing that, it could have been False all along, but we
        # just try the delete in case to be safe.

        # To make the code easier to read, use a table to drive our signal
        # connecting and disconnecting:
        self.signal_chain = [
            # Yahoo Group posts are always updated:
            (signals.post_save, ygroup.models.Post, self.enqueue_save),
            (signals.post_delete, ygroup.models.Post, self.enqueue_delete),

            # Weblink Links are updated if they are public:
            (signals.post_save, Link, self.enqueue_public_save),
            (signals.post_delete, Link, self.enqueue_delete),

            # Podcast Items are always updated:
            (signals.post_save, Item, self.enqueue_save),
            (signals.post_delete, Item, self.enqueue_delete),

            # News Stories are always updated:
            (signals.post_save, Story, self.enqueue_save),
            (signals.post_delete, Story, self.enqueue_delete),

            # Downloads are updated if they are public:
            (signals.post_save, Download, self.enqueue_public_save),
            (signals.post_delete, Download, self.enqueue_delete),

            # Forum Topics are updated if they belong to a public forum:
            (topic_content_update, None, self.enqueue_topic_save),
            (signals.post_delete, Topic, self.enqueue_delete),

            # Forum Posts are updated if they belong to a public forum:
            (post_content_update, None, self.enqueue_post_save),
            (signals.post_delete, Post, self.enqueue_delete),

            # UserProfiles are updated when we receive a special signal:
            (profile_content_update, None, self.enqueue_profile),
            (signals.post_delete, UserProfile, self.enqueue_delete),
        ]

        super(QueuedSignalProcessor, self).__init__(*args, **kwargs)

    def setup(self):
        """We override setup() so we can attach signal handlers to only the
        models we search on. In some cases we have custom signals to tell us
        when to update the search index.

        """
        for signal, sender, receiver in self.signal_chain:
            signal.connect(receiver, sender=sender, dispatch_uid=UID)

    def teardown(self):
        """Disconnect all signals we previously connected."""
        for signal, sender, receiver in self.signal_chain:
            signal.disconnect(receiver, sender=sender, dispatch_uid=UID)

    def enqueue_public_save(self, sender, instance, **kwargs):
        """Index only if the instance is_public.

        If not, enqueue a delete just in case the is_public flag got flipped
        from True to False.

        """
        if instance.is_public:
            self.enqueue_save(sender, instance, **kwargs)
        else:
            self.enqueue_delete(sender, instance, **kwargs)

    def enqueue_topic_save(self, sender, **kwargs):
        """Enqueue only if the topic instance belongs to a public forum."""
        if sender.forum.id in Forum.objects.public_forum_ids():
            self.enqueue_save(Topic, sender, **kwargs)

    def enqueue_post_save(self, sender, **kwargs):
        """Enqueue only if the post instance belongs to a public forum."""
        if sender.topic.forum.id in Forum.objects.public_forum_ids():
            self.enqueue_save(Post, sender, **kwargs)

    def enqueue_profile(self, sender, **kwargs):
        """Forward the user profile instance on unconditionally."""
        self.enqueue_save(UserProfile, sender, **kwargs)


# Starting with Django 1.7, we'd see Django generate warnings if we defined
# a HAYSTACK_SIGNAL_PROCESSOR in our settings that referenced the class above.
# This is because Haystack creates an instance of our signal processor class
# (defined above) at import time, and thus imports this module very early in the
# application startup sequence. Warnings are then generated when this module
# imports our models, some of whose applications have not been imported yet.
# This problem will presumably go away when Haystack can fully support Django
# 1.7.x and implements an AppConfig with a ready() method. Until then, we don't
# use Haystack's signal processor object; we'll just create one here. This
# module will be imported when our custom_search app's ready() method runs.

signal_processor = QueuedSignalProcessor(haystack.connections,
                                         haystack.connection_router)
