"""forms for the accounts application"""

import logging

from django import forms
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from django.contrib.sites.models import Site
from django.conf import settings

from core.functions import send_mail
from accounts.models import PendingUser
from accounts.models import IllegalUsername
from accounts.models import IllegalEmail


class RegisterForm(forms.Form):
    """Form used to register with the website"""
    username = forms.RegexField(max_length=30, regex = r'^\w+$',
        error_messages={
            'invalid': 'Your username must be 30 characters or less and ' \
                    'contain only letters, numbers and underscores.'})
    email = forms.EmailField()
    password1 = forms.CharField(label = "Password", widget = forms.PasswordInput)
    password2 = forms.CharField(label = "Password confirmation", widget = forms.PasswordInput)
    agree_age = forms.BooleanField(required=True, 
        label='I certify that I am over the age of 13',
        error_messages={
            'required': 'Sorry, but you must be over the age of 13 to ' \
                    'register at our site.',
            })
    agree_tos = forms.BooleanField(required=True, 
       label='I agree to the Terms of Service',
        error_messages={
            'required': 'You have not agreed to our Terms of Service.',
            })
    agree_privacy = forms.BooleanField(required=True,
        label='I agree to the Privacy Policy',
        error_messages={
            'required': 'You have not agreed to our Privacy Policy.',
            })

    def __init__(self, *args, **kwargs):
        self.ip = kwargs.pop('ip', '?')
        super(RegisterForm, self).__init__(*args, **kwargs)

    def clean_username(self):
        username = self.cleaned_data['username']
        try:
            User.objects.get(username = username)
        except User.DoesNotExist:
            try:
                PendingUser.objects.get(username = username)
            except PendingUser.DoesNotExist:
                try:
                    IllegalUsername.objects.get(username = username)
                except IllegalUsername.DoesNotExist:
                    return username
                self._validation_error("That username is not allowed.", username)
            self._validation_error("A pending user with that username already exists.", username)
        self._validation_error("A user with that username already exists.", username)

    def clean_email(self):
        email = self.cleaned_data['email']
        try:
            User.objects.get(email = email)
        except User.DoesNotExist:
            try:
                PendingUser.objects.get(email = email)
            except PendingUser.DoesNotExist:
                try:
                    IllegalEmail.objects.get(email = email)
                except IllegalEmail.DoesNotExist:
                    return email
                self._validation_error("That email address is not allowed.", email)
            self._validation_error("A pending user with that email address already exists.", email)
        self._validation_error("A user with that email address already exists.", email)

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1", "")
        password2 = self.cleaned_data["password2"]
        if password1 != password2:
            self._validation_error("The two password fields didn't match.")
        if len(password1) < 6:
            self._validation_error("Please choose a password of 6 characters or more.")
        return password2

    def save(self):
        pending_user = PendingUser.objects.create_pending_user(self.cleaned_data['username'],
                self.cleaned_data['email'],
                self.cleaned_data['password1'])

        # Send the confirmation email

        site = Site.objects.get_current()
        admin_email = settings.ADMINS[0][1]

        activation_link = 'http://%s%s' % (site.domain, reverse('accounts.views.register_confirm', 
                kwargs = {'username' : pending_user.username, 'key' : pending_user.key}))

        msg = render_to_string('accounts/registration_email.txt',
                {
                    'site_name' : site.name,
                    'site_domain' : site.domain,
                    'user_email' : pending_user.email,
                    'activation_link' : activation_link,
                    'username' : pending_user.username,
                    'admin_email' : admin_email,
                })

        subject = 'Registration Confirmation for ' + site.name
        send_mail(subject, msg, admin_email, [self.cleaned_data['email']])
        logging.info('Accounts/registration conf. email sent to %s for user %s; IP = %s' % \
                (self.cleaned_data['email'], pending_user.username, self.ip))

        return pending_user

    def _validation_error(self, msg, param=None):
        logging.error('Accounts/registration [%s]: %s (%s)' % (self.ip, msg, param))
        raise forms.ValidationError(msg)
