"""Haystack search index for the news application."""
from haystack import indexes

from news.models import Story


class StoryIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    author = indexes.CharField(model_attr='submitter')
    pub_date = indexes.DateTimeField(model_attr='date_submitted')

    def get_model(self):
        return Story

    def get_updated_field(self):
        return 'update_date'
