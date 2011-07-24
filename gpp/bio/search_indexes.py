"""Haystack search index for the bio application."""
from haystack.indexes import *
from haystack import site
from custom_search import CondQueuedSearchIndex

from bio.models import UserProfile


class UserProfileIndex(CondQueuedSearchIndex):
    text = CharField(document=True, use_template=True)
    author = CharField(model_attr='user')

    def get_queryset(self):
        return UserProfile.objects.filter(user__is_active=True)

    def get_updated_field(self):
        return 'update_date'

    def can_index(self, instance):
        return instance.user.is_active


site.register(UserProfile, UserProfileIndex)
