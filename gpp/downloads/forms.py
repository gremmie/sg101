"""
Forms for the downloads application.
"""
import os

from django import forms
from django.conf import settings

from downloads.models import Download
from downloads.models import AllowedExtension


class SearchForm(forms.Form):
    """Downloads search form."""
    text = forms.CharField(max_length=30)

    def query(self):
        return self.cleaned_data['text']


class AddDownloadForm(forms.ModelForm):
    """Form to allow adding downloads."""
    title = forms.CharField(required=True, 
            widget=forms.TextInput(attrs={'size': 64, 'maxlength': 64}))
    description = forms.CharField(required=False, 
            widget=forms.Textarea(attrs={'class': 'markItUp smileyTarget'}))

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
            'all': (settings.GPP_THIRD_PARTY_CSS['markitup'] +
                    settings.GPP_THIRD_PARTY_CSS['jquery-ui'])
        }
        js = (settings.GPP_THIRD_PARTY_JS['markitup'] +
              settings.GPP_THIRD_PARTY_JS['jquery-ui'])
