"""Contains models for the accounts application"""

import datetime

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

from accounts.utils import make_confirmation_token


class IllegalUsername(models.Model):
   """model to represent the list of illegal usernames"""
   username = models.CharField(max_length=30, db_index=True)

   def __str__(self):
      return self.username

   class Meta:
      ordering = ('username', )


class IllegalEmail(models.Model):
   """model to represent the list of illegal/restricted email addresses"""
   email = models.EmailField(db_index=True)

   def __str__(self):
      return self.email

   class Meta:
      ordering = ('email', )


class PendingUserManager(models.Manager):
   """user manager for PendingUser model"""

   def create_pending_user(self, username, email, password):
      '''creates a new pending user and saves it to the database'''

      temp_user = User()
      temp_user.set_password(password)

      now = timezone.now()
      pending_user = self.model(None,
            username,
            email,
            temp_user.password,
            now,
            make_confirmation_token())

      pending_user.save()
      return pending_user


   def purge_expired(self):
      expire_time = timezone.now() - datetime.timedelta(days=1)
      expired_pending_users = self.filter(date_joined__lt=expire_time)
      expired_pending_users.delete()


class PendingUser(models.Model):
   """model for holding users while they go through the email registration cycle"""

   username = models.CharField(max_length=30, db_index=True, unique=True)
   email = models.EmailField()
   password = models.CharField(max_length=128)
   date_joined = models.DateTimeField(default=timezone.now, db_index=True)
   key = models.CharField(max_length=64)

   objects = PendingUserManager()

   def __str__(self):
      return self.username



# A requested email address change is good for one day, the same window a
# registration confirmation gets.
EMAIL_CHANGE_EXPIRATION = datetime.timedelta(days=1)


def _email_change_cutoff():
   """Requests made before this moment have expired."""
   return timezone.now() - EMAIL_CHANGE_EXPIRATION


class PendingEmailChangeManager(models.Manager):
   """manager for the PendingEmailChange model"""

   def request_change(self, user, new_email):
      """Record a request to change a user's address, replacing any earlier one.

      Replacing rather than adding is enforced by the schema, not here; see the
      model. A fresh key and timestamp mean a resend restarts the window
      instead of handing the member a link that expires in an hour.

      """
      change, _ = self.update_or_create(user=user, defaults={
            'new_email': new_email,
            'key': make_confirmation_token(),
            'date_requested': timezone.now(),
            })
      return change

   def active(self):
      """Return the requests that have not expired."""
      return self.filter(date_requested__gte=_email_change_cutoff())

   def purge_expired(self):
      expired_changes = self.filter(date_requested__lt=_email_change_cutoff())
      expired_changes.delete()


class PendingEmailChange(models.Model):
   """model for holding a requested email address until it is confirmed

   The OneToOneField is what makes the last request win: the database cannot
   hold two requests for one user, so a second one overwrites the first rather
   than racing it. The existence of the row is the whole of the pending state,
   so there is no separate flag that can disagree with it.

   """

   user = models.OneToOneField(User, on_delete=models.CASCADE,
                               related_name='pending_email_change')
   new_email = models.EmailField()
   key = models.CharField(max_length=64)
   date_requested = models.DateTimeField(default=timezone.now, db_index=True)

   objects = PendingEmailChangeManager()

   def __str__(self):
      return '%s -> %s' % (self.user.username, self.new_email)

   @property
   def is_expired(self):
      return self.date_requested < _email_change_cutoff()
