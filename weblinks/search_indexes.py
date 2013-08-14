"""Haystack search index for the weblinks application."""
from haystack.indexes import CharField, DateTimeField
from haystack import site
from custom_search.indexes import PublicQueuedSearchIndex

from weblinks.models import Link


class LinkIndex(PublicQueuedSearchIndex):
    text = CharField(document=True, use_template=True)
    author = CharField(model_attr='user')
    pub_date = DateTimeField(model_attr='date_added')

    def index_queryset(self):
        return Link.public_objects.all()

    def get_updated_field(self):
        return 'update_date'

site.register(Link, LinkIndex)
