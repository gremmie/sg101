"""Haystack search index for the weblinks application."""
from haystack import indexes

from weblinks.models import Link


class LinkIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    author = indexes.CharField(model_attr='user')
    pub_date = indexes.DateTimeField(model_attr='date_added')

    def get_model(self):
        return Link

    def index_queryset(self, using=None):
        return Link.public_objects.all()

    def get_updated_field(self):
        return 'update_date'

