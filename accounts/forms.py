"""forms for the accounts application"""

import logging
import random

from django import forms
from django.contrib.auth.models import User
from django.urls import reverse
from django.template.loader import render_to_string
from django.contrib.sites.models import Site
from django.conf import settings

from core.functions import send_mail
from accounts.models import PendingUser
from accounts.models import IllegalUsername
from accounts.models import IllegalEmail


logger = logging.getLogger('auth')


CODE_WORD_CHOICES = [
    'reverb',
    'sg101',
    'guitar',
    'showman',
    'surf',
    'surfer',
    'tank',
    'splash',
    'gremmie',
    'hodad',
    'stomp',
    'belairs',
    'dickdale',
    'chantays',
    'astronauts',
    'fender',
]

def generate_registration_code():
    """Generates a simple, random registration code for the user to enter."""
    return '{}-{}'.format(random.choice(CODE_WORD_CHOICES), random.randint(100, 999))


class RegisterForm(forms.Form):
    """Form used to register with the website"""
    username = forms.RegexField(
            max_length=30,
            regex=r'^\w+$',
            error_messages={'invalid': ('Your username must be 30 characters or'
                ' less and contain only letters, numbers and underscores.')},
            widget=forms.TextInput(attrs={'class': 'text'}),
            )
    email = forms.EmailField(widget=forms.TextInput(attrs={'class': 'text'}))
    password1 = forms.CharField(label="Password",
            widget=forms.PasswordInput(attrs={'class': 'text'}))
    password2 = forms.CharField(label="Password confirmation",
            widget=forms.PasswordInput(attrs={'class': 'text'}))
    agree_age = forms.BooleanField(required=True,
        label='I certify that I am over the age of 13',
        error_messages={
            'required': 'Sorry, but you must be over the age of 13 to '
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
    question1 = forms.CharField(label="What number appears in the site name?",
        widget=forms.TextInput(attrs={'class': 'text'}))
    question2 = forms.CharField(label='', required=False,
        widget=forms.TextInput(attrs={'style': 'display: none;'}))
    question3 = forms.CharField(label="Don't put anything in this box",
        required=False,
        widget=forms.TextInput(attrs={'class': 'text'}))

    def __init__(self, *args, **kwargs):
        self.ip = kwargs.pop('ip', '?')
        super(RegisterForm, self).__init__(*args, **kwargs)

    def clean_username(self):
        username = self.cleaned_data['username']
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            try:
                PendingUser.objects.get(username=username)
            except PendingUser.DoesNotExist:
                try:
                    IllegalUsername.objects.get(username=username)
                except IllegalUsername.DoesNotExist:
                    return username
                self._validation_error("That username is not allowed.", username)
            self._validation_error("A pending user with that username already exists.", username)
        self._validation_error("A user with that username already exists.", username)

    def clean_email(self):
        email = self.cleaned_data['email']

        if User.objects.filter(email=email).count():
            self._validation_error("A user with that email address already exists.", email)
        elif PendingUser.objects.filter(email=email).count():
            self._validation_error("A pending user with that email address already exists.", email)
        elif IllegalEmail.objects.filter(email=email).count():
            self._validation_error("That email address is not allowed.", email)

        # email is ok
        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1", "")
        password2 = self.cleaned_data["password2"]
        if password1 != password2:
            self._validation_error("The two password fields didn't match.")
        if len(password1) < 6:
            self._validation_error("Please choose a password of 6 characters or more.")
        return password2

    def clean_question1(self):
        answer = self.cleaned_data.get('question1')
        success = False
        if answer:
            try:
                val = int(answer)
            except ValueError:
                pass
            else:
                success = val == 101
        if not success:
            self._validation_error("Incorrect answer to our anti-spam question.", answer)
        return answer

    def clean_question2(self):
        """
        Honeypot field should be empty.
        """
        answer = self.cleaned_data.get('question2')
        if answer:
            logger.critical('Accounts/registration: Honeypot filled [%s]', self.ip)
            self._validation_error('Wrong answer #2', answer)
        return answer

    def clean_question3(self):
        answer = self.cleaned_data.get('question3')
        if answer:
            self._validation_error('Oops, that should be blank', answer)
        return answer

    def save(self, request):
        request.session['reg_info'] = {
            'username': self.cleaned_data['username'],
            'email': self.cleaned_data['email'],
            'password': self.cleaned_data['password1'],
            'code': generate_registration_code(),
        }

    def _validation_error(self, msg, param=None):
        logger.error('Accounts/registration [%s]: %s (%s)', self.ip, msg, param)
        raise forms.ValidationError(msg)


class RegisterCodeForm(forms.Form):
    """Form for processing anti-spam code."""
    code = forms.CharField(
            label="Registration code",
            widget=forms.TextInput(attrs={'class': 'text'}))

    def __init__(self, *args, **kwargs):
        self.session = kwargs.pop('session', None)
        self.ip = kwargs.pop('ip', '?')
        super(RegisterCodeForm, self).__init__(*args, **kwargs)

    def clean_code(self):
        reg_info = self.session.get('reg_info')
        saved_code = reg_info.get('code') if reg_info else None
        if not saved_code:
            self._validation_error("Registration code error")
        user_code = self.cleaned_data['code']
        if user_code:
            user_code = user_code.strip()

        if user_code != saved_code:
            self._validation_error("The registration code does not match")

    def save(self):
        """Process successful registration."""
        reg_info = self.session['reg_info']
        username = reg_info['username']
        email = reg_info['email']
        password = reg_info['password']

        pending_user = PendingUser.objects.create_pending_user(
                username,
                email,
                password)

        # Send the confirmation email
        site = Site.objects.get_current()
        admin_email = settings.DEFAULT_FROM_EMAIL

        activation_link = '%s://%s%s' % (
                settings.SITE_SCHEME,
                site.domain,
                reverse('accounts-register_confirm',
                        kwargs={'username': pending_user.username,
                                'key': pending_user.key}))

        msg = render_to_string('accounts/registration_email.txt', {
                'site_name' : site.name,
                'site_domain' : site.domain,
                'user_email' : pending_user.email,
                'activation_link' : activation_link,
                'username' : pending_user.username,
                'admin_email' : admin_email,
                })

        subject = 'Registration Confirmation for ' + site.name
        send_mail(subject, msg, admin_email, [email])
        logger.info('Accounts/registration conf. email sent to %s for user %s; IP = %s',
                    email, pending_user.username, self.ip)
        del self.session['reg_info']

    def _validation_error(self, msg, param=None):
        logger.error('Accounts/registration [%s]: %s (%s)', self.ip, msg, param)
        raise forms.ValidationError(msg)


class ForgotUsernameForm(forms.Form):
    """Form used to recover lost username"""
    email = forms.EmailField(widget=forms.TextInput(attrs={'class': 'text'}))

    def save(self):
        """Email the username associated with the email address to the user."""
        email = self.cleaned_data['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # nothing to do; we don't tell the user as this gives away info
            # about our database
            return

        site = Site.objects.get_current()
        admin_email = settings.DEFAULT_FROM_EMAIL

        subject = 'Forgotten username for %s' % site.name
        msg = render_to_string('accounts/forgot_user_email.txt', {
            'user': user,
            'site': site,
            'admin_email': admin_email,
            })
        send_mail(subject, msg, admin_email, [email])

        logger.info('Forgotten username email sent to {} <{}>'.format(
            user.username, email))
