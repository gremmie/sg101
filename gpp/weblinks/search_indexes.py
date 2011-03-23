"""Haystack search index for the weblinks application."""
from haystack.indexes import *
from haystack import site
from queued_search.indexes import QueuedSearchIndex

from weblinks.models import Link


class LinkIndex(QueuedSearchIndex):
    text = CharField(document=True, use_template=True)
    author = CharField(model_attr='user')
    pub_date = DateTimeField(model_attr='date_added')

    def get_queryset(self):
        return Link.public_objects.all()

    def get_updated_field(self):
        return 'update_date'


site.register(Link, LinkIndex)
