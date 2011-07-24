"""Haystack search index for the weblinks application."""
from haystack.indexes import *
from haystack import site
from custom_search import CondQueuedSearchIndex

from forums.models import Forum, Topic, Post


class TopicIndex(CondQueuedSearchIndex):
    text = CharField(document=True, use_template=True)
    author = CharField(model_attr='user')
    pub_date = DateTimeField(model_attr='creation_date')

    def get_queryset(self):
        return Topic.objects.filter(forum__in=Forum.objects.public_forum_ids())

    def get_updated_field(self):
        return 'update_date'

    def can_index(self, instance):
        return instance.forum.id in Forum.objects.public_forum_ids()


class PostIndex(CondQueuedSearchIndex):
    text = CharField(document=True, use_template=True)
    author = CharField(model_attr='user')
    pub_date = DateTimeField(model_attr='creation_date')

    def get_queryset(self):
        return Post.objects.filter(
                topic__forum__in=Forum.objects.public_forum_ids())

    def get_updated_field(self):
        return 'update_date'

    def can_index(self, instance):
        return instance.topic.forum.id in Forum.objects.public_forum_ids()


site.register(Topic, TopicIndex)
site.register(Post, PostIndex)
