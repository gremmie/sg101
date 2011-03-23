"""Haystack search index for the news application."""
from haystack.indexes import *
from haystack import site
from queued_search.indexes import QueuedSearchIndex

from podcast.models import Item


class ItemIndex(QueuedSearchIndex):
    text = CharField(document=True, use_template=True)
    author = CharField(model_attr='author')
    pub_date = DateTimeField(model_attr='pubdate')

    def get_updated_field(self):
        return 'update_date'


site.register(Item, ItemIndex)
