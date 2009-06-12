"""forms for the accounts application"""

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
   username = forms.RegexField(max_length = 30, regex = r'^\w+$',
      error_messages = {'invalid' : 'Your username must be 30 characters or less and contain only letters, numbers and underscores.'})
   email = forms.EmailField()
   password1 = forms.CharField(label = "Password", widget = forms.PasswordInput)
   password2 = forms.CharField(label = "Password confirmation", widget = forms.PasswordInput)
   agree_tos = forms.BooleanField(required = True, label = 'I agree to the Terms of Service',
      error_messages = {'required' : 'You have not agreed to our Terms of Service'})
   agree_privacy = forms.BooleanField(required = True, label = 'I agree to the Privacy Policy',
      error_messages = {'required' : 'You have not agreed to our Privacy Policy'})

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
            raise forms.ValidationError("That username is not allowed.")
         raise forms.ValidationError("A pending user with that username already exists.")
      raise forms.ValidationError("A user with that username already exists.")

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
            raise forms.ValidationError("That email address is not allowed.")
         raise forms.ValidationError("A pending user with that email already exists.")
      raise forms.ValidationError("A user with that email already exists.")

   def clean_password2(self):
      password1 = self.cleaned_data.get("password1", "")
      password2 = self.cleaned_data["password2"]
      if password1 != password2:
         raise forms.ValidationError("The two password fields didn't match.")
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

      return pending_user

