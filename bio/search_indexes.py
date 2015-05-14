"""Haystack search index for the bio application."""
from haystack import indexes

from bio.models import UserProfile
from custom_search.fields import MaxTermSizeCharField


class UserProfileIndex(indexes.SearchIndex, indexes.Indexable):
    text = MaxTermSizeCharField(document=True, use_template=True)
    author = indexes.CharField(model_attr='user')

    def get_model(self):
        return UserProfile

    def index_queryset(self, using=None):
        return UserProfile.objects.filter(user__is_active=True)

    def get_updated_field(self):
        return 'update_date'
