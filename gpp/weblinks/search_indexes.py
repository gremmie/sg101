"""Haystack search index for the weblinks application."""
from haystack.indexes import *
from haystack import site

from weblinks.models import Link


class LinkIndex(SearchIndex):
    text = CharField(document=True, use_template=True)
    author = CharField(model_attr='user')
    pub_date = DateTimeField(model_attr='date_added')

    def get_queryset(self):
        return Link.public_objects.all()


site.register(Link, LinkIndex)
