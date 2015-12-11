"""
Forms for the member map application.
"""
from django import forms

from core.html import ImageCheckError
from core.html import image_check
from core.markup import site_markup
from membermap.models import MapEntry


class MapEntryForm(forms.ModelForm):
    location = forms.CharField(required=True,
            widget=forms.TextInput(attrs={'size': 64, 'maxlength': 255}))
    message = forms.CharField(required=False,
            widget=forms.Textarea(attrs={'class': 'markItUp smileyTarget'}))

    def clean_message(self):
        message = self.cleaned_data['message']
        self.html = None

        if message:
            self.html = site_markup(message)
            try:
                image_check(self.html)
            except ImageCheckError as ex:
                raise forms.ValidationError(str(ex))

        return message

    class Meta:
        model = MapEntry
        fields = ('location', 'message')
