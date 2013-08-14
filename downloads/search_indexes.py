"""Haystack search index for the downloads application."""
from haystack.indexes import CharField, DateTimeField
from haystack import site
from custom_search.indexes import PublicQueuedSearchIndex

from downloads.models import Download


class DownloadIndex(PublicQueuedSearchIndex):
    text = CharField(document=True, use_template=True)
    author = CharField(model_attr='user')
    pub_date = DateTimeField(model_attr='date_added')

    def index_queryset(self):
        return Download.public_objects.all()

    def get_updated_field(self):
        return 'update_date'

site.register(Download, DownloadIndex)
