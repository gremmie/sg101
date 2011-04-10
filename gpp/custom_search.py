"""
This module contains custom code to tailor the Haystack search application to
our needs.

"""
import urllib

from django import forms
from haystack.views import SearchView
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


class ModelSearchView(SearchView):
    """
    This custom search view puts an extra value in the template context named
    search_parms. search_parms will contain the search term q plus any models
    arguments all as a urlencoded string. This is useful for generating
    pagination links in the template.

    """
    def search_params(self):
        """
        Return the q and models search parameters as a urlencoded string if the
        form is valid. An empty string is returned if the form is not valid.

        """
        if self.form.is_valid():
            q = self.form.cleaned_data['q']
            models = self.form.cleaned_data['models']

            params = [('q', q)]
            params.extend([('models', model) for model in models])
            return urllib.urlencode(params)

        return ''

    def extra_context(self):
        return {'search_params': self.search_params() }
