"""Haystack search index for the weblinks application."""
from haystack import indexes

from custom_search.fields import MaxTermSizeCharField
from forums.models import Forum, Topic, Post


class TopicIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    author = indexes.CharField(model_attr='user')
    pub_date = indexes.DateTimeField(model_attr='creation_date')

    def get_model(self):
        return Topic

    def index_queryset(self, using=None):
        return Topic.objects.filter(forum__in=Forum.objects.public_forum_ids())

    def get_updated_field(self):
        return 'update_date'


class PostIndex(indexes.SearchIndex, indexes.Indexable):
    text = MaxTermSizeCharField(document=True, use_template=True)
    author = indexes.CharField(model_attr='user')
    pub_date = indexes.DateTimeField(model_attr='creation_date')

    def get_model(self):
        return Post

    def index_queryset(self, using=None):
        return Post.objects.filter(
                topic__forum__in=Forum.objects.public_forum_ids())

    def get_updated_field(self):
        return 'update_date'
