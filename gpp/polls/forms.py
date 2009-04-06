"""Forms for the Polls application."""

from django import forms

from polls.models import Choice


class VoteForm(forms.Form):
   """Form for voting in a poll."""
   choices = forms.ModelChoiceField(label='', empty_label=None,
         queryset=Choice.objects.none(), widget=forms.RadioSelect)

   def __init__(self, poll, *args, **kwargs):
      super(VoteForm, self).__init__(*args, **kwargs)
      self.fields['choices'].queryset = poll.choice_set.all()

