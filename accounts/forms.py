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


logger = logging.getLogger('auth')


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

    SPAM_CHOICES = [(1, 'cat'), (2, '328'), (4, 'green'), (8, 'ocean')]
    question4 = forms.ChoiceField(label="Pick the number", choices=SPAM_CHOICES)
    question5 = forms.IntegerField(label="What number did you pick, above?",
        widget=forms.TextInput(attrs={'class': 'text'}))
    question6 = forms.ChoiceField(label="Pick the color", choices=SPAM_CHOICES)

    USER_QUALITIES = [
        (1, "I am the lowest form of life, a spammer"),
        (2, "I'm a fan of surf music or I want to learn more"),
        (3, "Someone is paying me to post links to this site"),
        (4, "I am not going to spam this site"),
        (5, "I understand my account may be removed if I post spam"),
        (6, "I am going to spam the crap out of this site"),
        (7, "Surf music is one of my interests, not spam"),
    ]
    question7 = forms.MultipleChoiceField(
        label="Check all that apply",
        choices=USER_QUALITIES,
        required=False,
        widget=forms.CheckboxSelectMultiple)


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

    def clean_question4(self):
        answer = self.cleaned_data.get('question4')
        if answer != u'2':
            self._validation_error('Please pick the number', answer)
        return answer

    def clean_question5(self):
        answer = self.cleaned_data.get('question5')
        if answer != 328:
            self._validation_error('Please enter the correct number', answer)
        return answer

    def clean_question6(self):
        answer = self.cleaned_data.get('question6')
        if answer != u'4':
            self._validation_error('Please pick the color', answer)
        return answer

    def clean_question7(self):
        answer = self.cleaned_data.get('question7')
        answer.sort()
        if answer != [u'2', u'4', u'5', u'7']:
            self._validation_error("Please double-check your checkboxes", answer)
        return answer

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
        send_mail(subject, msg, admin_email, [self.cleaned_data['email']],
                defer=False)
        logger.info('Accounts/registration conf. email sent to %s for user %s; IP = %s',
                self.cleaned_data['email'], pending_user.username, self.ip)

        return pending_user

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
        admin_email = settings.ADMINS[0][1]

        subject = 'Forgotten username for %s' % site.name
        msg = render_to_string('accounts/forgot_user_email.txt', {
            'user': user,
            'site': site,
            'admin_email': admin_email,
            })
        send_mail(subject, msg, admin_email, [email], defer=False)

        logger.info('Forgotten username email sent to {} <{}>'.format(
            user.username, email))
