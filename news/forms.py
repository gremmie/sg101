"""
Forms for the news application.

"""
from django import forms
from django.conf import settings

from news.models import PendingStory
from news.models import Category


class AddNewsForm(forms.ModelForm):
   """Form for a user to submit a news story to the admins for review."""
   title = forms.CharField(widget=forms.TextInput(attrs={'size': 52}))
   short_text = forms.CharField(
           label="Article text",
           widget=forms.Textarea(
               attrs={'rows': 60, 'cols': 80, 'style': 'height:500px'}))

   class Meta:
      model = PendingStory
      fields = ['title', 'category', 'short_text']

   class Media:
      js = settings.GPP_THIRD_PARTY_JS['tiny_mce']


class SendStoryForm(forms.Form):
   """Form for sending a news story via email to a friend."""
   friend_name = forms.CharField(label="Friend's Name", max_length=64)
   friend_email = forms.EmailField(label="Friend's Email")

   def email(self):
      return self.cleaned_data['friend_email']

   def name(self):
      return self.cleaned_data['friend_name']

