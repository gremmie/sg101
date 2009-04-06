"""
Models for the shoutbox application.
"""
from django.db import models
from django.contrib.auth.models import User

class Shout(models.Model):
   user = models.ForeignKey(User)
   shout_date = models.DateTimeField(auto_now_add=True)
   shout = models.TextField()

   def __unicode__(self):
      shout = self.shout[:60]
      return u'Shout from %s: %s' % (self.user.username, shout)

   class Meta:
      ordering = ('-shout_date', )
