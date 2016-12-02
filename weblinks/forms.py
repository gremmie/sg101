"""
Forms for the weblinks application.
"""

from django import forms
from weblinks.models import PendingLink, Link


class AddLinkForm(forms.ModelForm):
   title = forms.CharField(widget = forms.TextInput(attrs = {'size': 52}))
   url = forms.CharField(widget = forms.TextInput(attrs = {'size': 52}))

   def clean_url(self):
      new_url = self.cleaned_data['url']
      try:
         Link.objects.get(url__iexact = new_url)
      except Link.DoesNotExist:
         return new_url
      raise forms.ValidationError('That link already exists in our database.')

   class Meta:
      model = PendingLink
      fields = ['category', 'title', 'url', 'description']
