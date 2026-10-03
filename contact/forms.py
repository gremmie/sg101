"""forms for the contact application"""

from django import forms
from django.conf import settings
from django.template.loader import render_to_string
from django.contrib.sites.models import Site

from antispam import turnstile
from antispam.turnstile import TurnstileOutcome
from core.functions import get_ip
from core.email_categories import EmailCategory
from core.functions import send_mail


class ContactForm(forms.Form):
    """Form used to contact the website admins"""
    name=forms.CharField(label="Your Name")
    email=forms.EmailField(label="Your Email")
    subject=forms.CharField()
    honeypot=forms.CharField(max_length=64, required=False,
            label='If you enter anything in this field your message will be treated as spam')
    message=forms.CharField(label="Your Message",
            widget=forms.Textarea(),
            max_length=3000)

    recipient_list = [mail_tuple[1] for mail_tuple in settings.MANAGERS]

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(ContactForm, self).__init__(*args, **kwargs)

    def clean_subject(self):
        subject = self.cleaned_data['subject']
        # This goes out as a header, where a newline is an injection. Django
        # refuses one too, but it does so from inside the Celery task the mail
        # is handed to -- so the send dies out of sight and the person who
        # typed it is told nothing. Refuse it here, where the form can answer.
        if '\n' in subject or '\r' in subject:
            raise forms.ValidationError('Subject cannot contain line breaks')
        return subject

    def clean_honeypot(self):
        value = self.cleaned_data['honeypot']
        if value:
            raise forms.ValidationError(self.fields['honeypot'].label)
        return value

    def clean(self):
        super(ContactForm, self).clean()
        token = self.request.POST.get('cf-turnstile-response')
        # Handed over unchecked: verify() recognises an absent token and
        # returns without calling out, so a bot that never loads the widget
        # still costs nothing and still leaves a line in the log.
        result = turnstile.verify(token, get_ip(self.request),
                                  source='contact form')
        if result.outcome is TurnstileOutcome.NO_TOKEN:
            raise forms.ValidationError("Please verify you aren't a robot")

        if result.outcome is TurnstileOutcome.REJECTED:
            raise forms.ValidationError(
                    "We couldn't verify that you aren't a robot. Please try "
                    "again.")
        # UNAVAILABLE falls through: an outage must not take the form down.
        # The honeypot above still applies, and turnstile.verify() has already
        # logged the skipped check at WARNING.

    def save(self):
        # Send the feedback message email

        site = Site.objects.get_current()

        msg = render_to_string('contact/contact_email.txt', {
                    'site_name': site.name,
                    'user_name': self.cleaned_data['name'],
                    'user_email': self.cleaned_data['email'],
                    'subject': self.cleaned_data['subject'],
                    'message': self.cleaned_data['message'],
                })

        subject = site.name + ' Feedback: ' + self.cleaned_data['subject']
        send_mail(subject, msg, settings.NO_REPLY_EMAIL, self.recipient_list,
                  reply_to=self.cleaned_data['email'],
                  category=EmailCategory.CONTACT_FORM)
