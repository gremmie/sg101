"""Haystack search index for the downloads application."""
from haystack import indexes

from downloads.models import Download


class DownloadIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    author = indexes.CharField(model_attr='user')
    pub_date = indexes.DateTimeField(model_attr='date_added')

    def get_model(self):
        return Download

    def index_queryset(self, using=None):
        return Download.public_objects.all()

    def get_updated_field(self):
        return 'update_date'
