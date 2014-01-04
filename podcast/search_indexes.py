"""Haystack search index for the news application."""
from haystack import indexes

from podcast.models import Item


class ItemIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    author = indexes.CharField(model_attr='author')
    pub_date = indexes.DateTimeField(model_attr='pubdate')

    def get_model(self):
        return Item

    def get_updated_field(self):
        return 'update_date'
