"""Forms for the search application."""
from django import forms

from search.documents import document_choices


class SearchForm(forms.Form):
    """
    The search page's form: one query box and the type checkboxes.

    One box rather than the old three. That form offered "all these words" /
    "this exact word or phrase" / "none of these words" and joined them into
    `terms "exact phrase" -excluded` before handing the engine a single string
    -- which is precisely the syntax websearch_to_tsquery parses. Collapsing to
    one box changes the interface, not the query language.

    """
    q = forms.CharField(
            label='Search for',
            widget=forms.TextInput(attrs={'type': 'search'}),
            error_messages={'required': 'Please supply some search terms'})

    # No box starts checked, as on the old form. Landing on a blank page of
    # choices asks the member which areas they actually want, rather than
    # handing them a whole-site search they rarely meant.
    models = forms.MultipleChoiceField(
            label='Search in',
            widget=forms.CheckboxSelectMultiple,
            required=False,
            choices=document_choices)

    def clean_models(self):
        """
        Returns the type keys to search, defaulting to all of them.

        A form submitting no `models` at all searches everything, which covers
        two cases that cannot be told apart: the masthead box in v3/base.html
        posts a bare `q`, and a browser submits nothing for a checkbox group
        with no box checked. So unchecking every box searches everything, as it
        did before -- the alternative would break the masthead.

        """
        keys = self.cleaned_data['models']
        return keys or [key for key, _ in document_choices()]
