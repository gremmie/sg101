"""
Forms for the member map application.
"""
from django import forms
from django.conf import settings

from membermap.models import MapEntry


class MapEntryForm(forms.ModelForm):

    class Meta:
        model = MapEntry
        fields = ('location', 'message')

    class Media:
        css = {
            'all': settings.GPP_THIRD_PARTY_CSS['markitup']
        }
        js = settings.GPP_THIRD_PARTY_JS['markitup']

# vim: ts=4 sw=4
