"""
Forms for the member map application.
"""
from django import forms
from django.conf import settings

from membermap.models import MapEntry


class MapEntryForm(forms.ModelForm):
    location = forms.CharField(required=True,
            widget=forms.TextInput(attrs={'size': 64, 'maxlength': 255}))
    message = forms.CharField(required=False,
            widget=forms.Textarea(attrs={'class': 'markItUp smileyTarget'}))

    class Meta:
        model = MapEntry
        fields = ('location', 'message')

    class Media:
        css = {
            'all': (settings.GPP_THIRD_PARTY_CSS['markitup'] +
                    settings.GPP_THIRD_PARTY_CSS['jquery-ui'])
        }
        js = (settings.GPP_THIRD_PARTY_JS['markitup'] +
              settings.GPP_THIRD_PARTY_JS['jquery-ui'])

