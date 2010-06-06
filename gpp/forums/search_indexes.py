"""Haystack search index for the weblinks application."""
from haystack.indexes import *
from haystack import site

from forums.models import Forum, Post


class PostIndex(SearchIndex):
    text = CharField(document=True, use_template=True)
    author = CharField(model_attr='user')
    pub_date = DateTimeField(model_attr='creation_date')

    def get_queryset(self):
        return Post.objects.filter(
                topic__forum__in=Forum.objects.public_forums())


site.register(Post, PostIndex)
