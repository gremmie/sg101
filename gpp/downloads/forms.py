"""
Forms for the downloads application.
"""
import os

from django import forms

from downloads.models import Download
from downloads.models import AllowedExtension


class SearchForm(forms.Form):
    """Downloads search form."""
    text = forms.CharField(max_length=30)

    def query(self):
        return self.cleaned_data['text']


class AddDownloadForm(forms.ModelForm):
    """Form to allow adding downloads."""

    def clean_file(self):
        file = self.cleaned_data['file']
        ext = os.path.splitext(file.name)[1]
        allowed_exts = AllowedExtension.objects.get_extension_list()
        if ext in allowed_exts:
            return file
        raise forms.ValidationError('The file extension "%s" is not allowed.' % ext)

    class Meta:
        model = Download
        fields = ('title', 'category', 'description', 'file')
        
    class Media:
        css = {
            'all': ('js/markitup/skins/markitup/style.css',
                    'js/markitup/sets/markdown/style.css')
        }
        js = (
            'js/jquery-1.2.6.min.js',
            'js/downloads/add.js',
            'js/markitup/jquery.markitup.pack.js',
            'js/markitup/sets/markdown/set.js',
        )
