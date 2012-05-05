"""
This module contains custom forms to tailor the Haystack search application to
our needs.

"""
from django import forms
from haystack.forms import ModelSearchForm


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
