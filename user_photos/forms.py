"""Forms for the user_photos application."""
from django import forms


class UploadForm(forms.Form):
    image_file = forms.ImageField()
