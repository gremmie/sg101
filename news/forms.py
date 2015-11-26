"""
Forms for the news application.

"""
from django import forms
from django.conf import settings

from core.html import ImageCheckError
from core.html import image_check
from core.markup import site_markup
from news.models import PendingStory


class AddNewsForm(forms.ModelForm):
    """Form for a user to submit a news story to the admins for review."""
    title = forms.CharField(widget=forms.TextInput(attrs={'size': 52}))
    short_markup = forms.CharField(
            label="Article text",
            widget=forms.Textarea(attrs={
                'id': 'id_body',    # needed for image related js
                'rows': 60,
                'cols': 80,
                'class': 'markItUp smileyTarget',
                'style': 'height:500px',
            }))

    class Meta:
        model = PendingStory
        fields = ['title', 'category', 'short_markup']

    class Media:
        css = {
            'all': (settings.GPP_THIRD_PARTY_CSS['markitup'] +
                    settings.GPP_THIRD_PARTY_CSS['jquery-ui'])
        }
        js = (
            settings.GPP_THIRD_PARTY_JS['markitup'] +
            settings.GPP_THIRD_PARTY_JS['jquery-ui'] +
            ['js/jquery.form.min.js']
        )

    def clean_short_markup(self):
        md = self.cleaned_data['short_markup']
        self.html = None
        if not md:
            raise forms.ValidationError("Please enter some article text")

        if md:
            self.html = site_markup(md)
            try:
                image_check(self.html)
            except ImageCheckError as ex:
                raise forms.ValidationError(str(ex))

        return md

    def save(self, user):
        pending_story = super(AddNewsForm, self).save(commit=False)
        pending_story.submitter = user
        pending_story.save(short_text=self.html)
        return pending_story


class SendStoryForm(forms.Form):
    """Form for sending a news story via email to a friend."""
    friend_name = forms.CharField(label="Friend's Name", max_length=64)
    friend_email = forms.EmailField(label="Friend's Email")

    def email(self):
        return self.cleaned_data['friend_email']

    def name(self):
        return self.cleaned_data['friend_name']

