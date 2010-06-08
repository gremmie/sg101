"""Haystack search index for the news application."""
from haystack.indexes import *
from haystack import site
from podcast.models import Item


class ItemIndex(SearchIndex):
    text = CharField(document=True, use_template=True)
    author = CharField(model_attr='author')
    pub_date = DateTimeField(model_attr='pubdate')


site.register(Item, ItemIndex)
