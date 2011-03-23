"""Haystack search index for the downloads application."""
from haystack.indexes import *
from haystack import site
from queued_search.indexes import QueuedSearchIndex

from downloads.models import Download


class DownloadIndex(QueuedSearchIndex):
    text = CharField(document=True, use_template=True)
    author = CharField(model_attr='user')
    pub_date = DateTimeField(model_attr='date_added')

    def get_queryset(self):
        return Download.public_objects.all()

    def get_updated_field(self):
        return 'update_date'


site.register(Download, DownloadIndex)
