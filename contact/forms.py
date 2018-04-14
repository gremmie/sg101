"""forms for the contact application"""

import logging

from django import forms
from django.conf import settings
from django.template.loader import render_to_string
from django.contrib.sites.models import Site
import requests

from core.functions import get_ip
from core.functions import send_mail


logger = logging.getLogger(__name__)


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

    def clean_honeypot(self):
        value = self.cleaned_data['honeypot']
        if value:
            raise forms.ValidationError(self.fields['honeypot'].label)
        return value

    def clean(self):
        super(ContactForm, self).clean()
        captcha_response = self.request.POST.get('g-recaptcha-response')
        if not captcha_response:
            raise forms.ValidationError('Missing reCAPTCHA response')
        r = requests.post(settings.RECAPTCHA_URL, data={
                'secret': settings.RECAPTCHA_SECRET_KEY,
                'response': captcha_response,
                'remoteip': get_ip(self.request),
            })
        result = r.json()
        logger.info("Contact Form captcha response: %s %s",
                    result.get('success', '<Missing>'),
                    result.get('error-codes', '<Missing>'))
        success = result.get('success', False)
        if not success:
            raise forms.ValidationError('reCAPTCHA failure')

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
