"""Haystack search index for the weblinks application."""
from haystack.indexes import *
from haystack import site
from custom_search.indexes import CondQueuedSearchIndex

from weblinks.models import Link


class LinkIndex(CondQueuedSearchIndex):
    text = CharField(document=True, use_template=True)
    author = CharField(model_attr='user')
    pub_date = DateTimeField(model_attr='date_added')

    def index_queryset(self):
        return Link.public_objects.all()

    def get_updated_field(self):
        return 'update_date'

    def can_index(self, instance):
        return instance.is_public

site.register(Link, LinkIndex)
