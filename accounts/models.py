"""Contains models for the accounts application"""

import datetime
import random
import string
import hashlib
import base64

from django.db import models
from django.contrib.auth.models import User
from django.conf import settings


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

   create_count = 0

   def create_pending_user(self, username, email, password):
      '''creates a new pending user and saves it to the database'''

      temp_user = User()
      temp_user.set_password(password)

      now = datetime.datetime.now()
      pending_user = self.model(None,
            username,
            email,
            temp_user.password,
            now,
            self._make_key())

      pending_user.save()
      self.create_count += 1
      return pending_user


   def purge_expired(self):
      expire_time = datetime.datetime.now() - datetime.timedelta(days=1)
      expired_pending_users = self.filter(date_joined__lt=expire_time)
      expired_pending_users.delete()


   def _make_key(self):
      s = ''.join(random.sample(string.printable, 8))
      delta = datetime.date.today() - datetime.date(1846, 12, 28)
      days = base64.urlsafe_b64encode(str(delta * 10).encode('ascii')).decode('ascii')
      raw = u'%s%s%s%s' % (settings.SECRET_KEY, self.create_count, s, days)
      key = hashlib.sha1(raw.encode('utf-8')).hexdigest()[::2]
      return key


class PendingUser(models.Model):
   """model for holding users while they go through the email registration cycle"""

   username = models.CharField(max_length=30, db_index=True, unique=True)
   email = models.EmailField()
   password = models.CharField(max_length=128)
   date_joined = models.DateTimeField(default=datetime.datetime.now, db_index=True)
   key = models.CharField(max_length=20)

   objects = PendingUserManager()

   def __str__(self):
      return self.username

