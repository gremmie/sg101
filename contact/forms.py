"""forms for the contact application"""

from django import forms
from django.conf import settings
from django.template.loader import render_to_string
from django.contrib.sites.models import Site
from core.functions import send_mail


class ContactForm(forms.Form):
    """Form used to contact the website admins"""
    name=forms.CharField(label="Your Name", max_length=61,
            widget=forms.TextInput(attrs={'size': 50 }))
    email=forms.EmailField(label="Your Email",
            widget=forms.TextInput(attrs={'size': 50 }))
    subject=forms.CharField(max_length=64,
            widget=forms.TextInput(attrs={'size': 50 }))
    honeypot=forms.CharField(max_length=64, required=False,
            label='If you enter anything in this field your message will be treated as spam')
    message=forms.CharField(label="Your Message",
            widget=forms.Textarea(attrs={'rows': 16, 'cols': 50}),
            max_length=3000)

    recipient_list = [mail_tuple[1] for mail_tuple in settings.MANAGERS]

    def clean_honeypot(self):
        value = self.cleaned_data['honeypot']
        if value:
            raise forms.ValidationError(self.fields['honeypot'].label)
        return value

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
        from_email = settings.GPP_NO_REPLY_EMAIL + '@' + site.domain
        send_mail(subject, msg, from_email, self.recipient_list,
                  reply_to=self.cleaned_data['email'])
