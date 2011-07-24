"""Haystack search index for the news application."""
from haystack.indexes import *
from haystack import site
from custom_search import CondQueuedSearchIndex

from news.models import Story


class StoryIndex(CondQueuedSearchIndex):
    text = CharField(document=True, use_template=True)
    author = CharField(model_attr='submitter')
    pub_date = DateTimeField(model_attr='date_submitted')

    def get_updated_field(self):
        return 'update_date'


site.register(Story, StoryIndex)
