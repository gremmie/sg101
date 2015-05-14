"""
Haystack search index for the Yahoo Group archives application.

"""
from haystack import indexes

from custom_search.fields import MaxTermSizeCharField
from ygroup.models import Post


class PostIndex(indexes.SearchIndex, indexes.Indexable):
    text = MaxTermSizeCharField(document=True, use_template=True)
    pub_date = indexes.DateTimeField(model_attr='creation_date')

    def get_model(self):
        return Post

    def get_updated_field(self):
        return 'creation_date'

