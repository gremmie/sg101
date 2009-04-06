"""
Forms for the member map application.
"""
from django import forms
from membermap.models import MapEntry


class MapEntryForm(forms.ModelForm):

    class Meta:
        model = MapEntry
        fields = ('location', 'message')

    class Media:
        css = {
            'all': ('js/markitup/skins/markitup/style.css',
                    'js/markitup/sets/markdown/style.css')
        }
        js = (
            'js/markitup/jquery.markitup.pack.js',
            'js/markitup/sets/markdown/set.js',
        )

# vim: ts=4 sw=4
