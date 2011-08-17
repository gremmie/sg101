"""Haystack search index for the bio application."""
from haystack.indexes import *
from haystack import site
from custom_search.indexes import CondQueuedSearchIndex

from bio.models import UserProfile
from bio.signals import profile_content_update


class UserProfileIndex(CondQueuedSearchIndex):
    text = CharField(document=True, use_template=True)
    author = CharField(model_attr='user')

    def get_queryset(self):
        return UserProfile.objects.filter(user__is_active=True)

    def get_updated_field(self):
        return 'update_date'

    def _setup_save(self, model):
        profile_content_update.connect(self.enqueue_save)

    def _teardown_save(self, model):
        profile_content_update.disconnect(self.enqueue_save)

    def enqueue_save(self, sender, **kwargs):
        return self.enqueue('update', sender)

    def can_index(self, instance):
        return instance.user.is_active


site.register(UserProfile, UserProfileIndex)
