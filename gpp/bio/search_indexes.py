"""Haystack search index for the bio application."""
from haystack.indexes import *
from haystack import site

from bio.models import UserProfile


class UserProfileIndex(SearchIndex):
    text = CharField(document=True, use_template=True)
    author = CharField(model_attr='user')

    def get_queryset(self):
        return UserProfile.objects.filter(user__is_active=True)

    def get_updated_field(self):
        return 'update_date'


site.register(UserProfile, UserProfileIndex)
