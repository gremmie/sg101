"""Models for the IRC application. 
The IRC application simply reports who is in the site's IRC chatroom. A bot in the channel updates
the table and we read it.
"""
from django.db import models

class IrcChannel(models.Model):
   name = models.CharField(max_length=30)
   last_update = models.DateTimeField()

   def __unicode__(self):
      return self.name

   class Meta:
      ordering = ('name', )
