"""Forms for the bandmap application.

"""
from django import forms

from bandmap.models import BandEntry


class BandForm(forms.ModelForm):
    """This form is used to add bands to the map."""
    class Meta:
        model = BandEntry
        fields = ['name', 'url', 'location', 'note', 'is_active', 'lat', 'lon']
        labels = {
            'name': 'Band name',
            'url': 'Link',
            'is_active': 'Band is currently active',
        }
        help_texts = {
            'url': 'Link to website or web presence (optional)',
            'location': 'See examples, above',
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'size': 64,
                'class': 'text'}),
            'url': forms.TextInput(attrs={
                'size': 64,
                'class': 'text',
                'placeholder': 'http://'}),
            'location': forms.TextInput(attrs={
                'size': 64,
                'class': 'text',
                'placeholder': 'Huntington Beach, CA, USA'}),
            'note': forms.TextInput(attrs={
                'size': 64,
                'class': 'text',
                'placeholder': 'Optional short note about the band'}),
            'lat': forms.HiddenInput(),
            'lon': forms.HiddenInput(),
        }
