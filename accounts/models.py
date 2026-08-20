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

