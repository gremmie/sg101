"""
Forms for the downloads application.
"""
import os

from django import forms

from core.html import ImageCheckError
from core.html import image_check
from core.markup import site_markup
from downloads.models import PendingDownload
from downloads.models import AllowedExtension


class AddDownloadForm(forms.ModelForm):
    """Form to allow adding downloads."""
    title = forms.CharField(required=True,
            widget=forms.TextInput(attrs={'size': 64, 'maxlength': 64}))
    description = forms.CharField(required=False,
            widget=forms.Textarea(attrs={'class': 'markItUp smileyTarget'}))

    def clean_description(self):
        description = self.cleaned_data['description'].strip()
        self.html = None
        if not description:
            raise forms.ValidationError("Please enter a description")

        self.html = site_markup(description)
        try:
            image_check(self.html)
        except ImageCheckError as ex:
            raise forms.ValidationError(str(ex))

        return description

    def clean_file(self):
        file = self.cleaned_data['file']
        ext = os.path.splitext(file.name)[1]
        allowed_exts = AllowedExtension.objects.get_extension_list()
        if ext in allowed_exts:
            return file
        raise forms.ValidationError('The file extension "%s" is not allowed.' % ext)

    class Meta:
        model = PendingDownload
        fields = ('title', 'category', 'description', 'file')
