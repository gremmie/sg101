"""Forms for the Polls application."""

from django import forms
from django.db.models import F

from polls.models import Choice


class VoteForm(forms.Form):
    """Form for voting in a poll."""
    choices = forms.ModelChoiceField(label='', empty_label=None,
            queryset=Choice.objects.none(), widget=forms.RadioSelect)

    def __init__(self, poll, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.user_choice = kwargs.pop('user_choice', None)
        super(VoteForm, self).__init__(*args, **kwargs)
        self.fields['choices'].queryset = poll.choice_set.all()

    def clean(self):
        if self.user_choice:
            raise forms.ValidationError("You've already voted in this poll!")
        return self.cleaned_data

    def save(self):
        choice = self.cleaned_data['choices']
        Choice.objects.filter(id=choice.id).update(votes=F('votes') + 1)
        choice.voters.add(self.user)
