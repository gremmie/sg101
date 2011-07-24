"""
This module contains custom code to tailor the Haystack search application to
our needs.

"""
import urllib

from django import forms
from haystack.forms import ModelSearchForm
from queued_search.indexes import QueuedSearchIndex


MODEL_CHOICES = (
    ('forums.topic', 'Forum Topics'),
    ('forums.post', 'Forum Posts'),
    ('news.story', 'News Stories'),
    ('bio.userprofile', 'User Profiles'),
    ('weblinks.link', 'Links'),
    ('downloads.download', 'Downloads'),
    ('podcast.item', 'Podcasts'),
    ('ygroup.post', 'Yahoo Group Archives'),
)


class CustomModelSearchForm(ModelSearchForm):
    """
    This customized ModelSearchForm allows us to explictly label and order
    the model choices.

    """
    q = forms.CharField(required=False, label='',
            widget=forms.TextInput(attrs={'class': 'text', 'size': 48}))

    def __init__(self, *args, **kwargs):
        super(CustomModelSearchForm, self).__init__(*args, **kwargs)
        self.fields['models'] = forms.MultipleChoiceField(choices=MODEL_CHOICES,
                label='', widget=forms.CheckboxSelectMultiple)


class CondQueuedSearchIndex(QueuedSearchIndex):
    """
    This customized version of QueuedSearchIndex conditionally enqueues items
    to be indexed by calling the can_index() method.

    """
    def can_index(self, instance):
        """
        The default is to index all instances. Override this method to
        customize the behavior. This will be called on all update operations.

        """
        return True

    def enqueue(self, action, instance):
        """
        This method enqueues the instance only if the can_index() method
        returns True.

        """
        if (action == 'update' and self.can_index(instance) or
                action == 'delete'):
            super(CondQueuedSearchIndex, self).enqueue(action, instance)
