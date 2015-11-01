"""
Forms for the Shoutbox application.
"""
from django import forms

class ShoutBoxForm(forms.Form):
   msg = forms.CharField(label='', max_length=2048, required=True)
