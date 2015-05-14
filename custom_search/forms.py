"""
This module contains custom forms to tailor the Haystack search application to
our needs.

"""
import logging

from django import forms
from django.conf import settings
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

logger = logging.getLogger(__name__)


class CustomModelSearchForm(ModelSearchForm):
    """
    This customized ModelSearchForm allows us to explictly label and order
    the model choices.

    We also provide "all words", "exact phrase", and "exclude" text input boxes.
    Haystack 2.1.0's auto_query() function did not seem to work right so we just
    rolled our own.

    This form can optionally receive the user making the search as a keyword
    argument ('user') to __init__. This will be used for logging search queries.

    """
    q = forms.CharField(required=False, label='All these words',
            widget=forms.TextInput(attrs={'type': 'search', 'class': 'search',
                'size': 48}))
    exact = forms.CharField(required=False, label='This exact word or phrase',
            widget=forms.TextInput(attrs={'type': 'search', 'class': 'search',
                'size': 48}))
    exclude = forms.CharField(required=False, label='None of these words',
            widget=forms.TextInput(attrs={'type': 'search', 'class': 'search',
                'size': 48}))

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(CustomModelSearchForm, self).__init__(*args, **kwargs)
        self.fields['models'] = forms.MultipleChoiceField(choices=MODEL_CHOICES,
                label='Search in', widget=forms.CheckboxSelectMultiple)

    def clean(self):
        if not settings.SEARCH_QUEUE_ENABLED:
            raise forms.ValidationError("Our search function is offline for "
                    "maintenance. Please try again later. "
                    "We apologize for any inconvenience.")

        if not (self.cleaned_data['q'] or self.cleaned_data['exact'] or
                self.cleaned_data['exclude']):
            raise forms.ValidationError('Please supply some search terms')

        return self.cleaned_data

    def clean_exact(self):
        exact_field = self.cleaned_data['exact']
        if "'" in exact_field or '"' in exact_field:
            raise forms.ValidationError("Quotes are not needed in this field")
        return exact_field

    def search(self):
        if not self.is_valid():
            return self.no_query_found()

        if self.user is None:
            username = 'UNKNOWN'
        elif self.user.is_authenticated():
            username = self.user.username
        else:
            username = 'ANONYMOUS'

        logger.info('Search executed: /%s/%s/%s/ in %s by %s',
            self.cleaned_data['q'],
            self.cleaned_data['exact'],
            self.cleaned_data['exclude'],
            self.cleaned_data['models'],
            username)

        # Note that in Haystack 2.x content is untrusted and is automatically
        # auto-escaped for us.
        #
        # Gather regular search terms
        terms = ' '.join(self.cleaned_data['q'].split())

        # Exact words or phrases:
        exact = self.cleaned_data['exact'].strip()
        if exact:
            exact = '"{}"'.format(exact)

        # Exclude terms:
        exclude = ["-{}".format(term) for term in self.cleaned_data['exclude'].split()]
        exclude = ' '.join(exclude)

        query = ' '.join([terms, exact, exclude]).strip()
        logger.debug("auto_query: %s", query)

        sqs = self.searchqueryset.auto_query(query)

        if self.load_all:
            sqs = sqs.load_all()

        # Apply model filtering
        sqs = sqs.models(*self.get_models())

        return sqs
