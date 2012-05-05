"""
Haystack search index for the Yahoo Group archives application.

"""
from haystack.indexes import *
from haystack import site
from custom_search.indexes import CondQueuedSearchIndex

from ygroup.models import Post


class PostIndex(CondQueuedSearchIndex):
    text = CharField(document=True, use_template=True)
    pub_date = DateTimeField(model_attr='creation_date')

    def get_updated_field(self):
        return 'creation_date'


site.register(Post, PostIndex)
