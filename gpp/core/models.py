"""
This file contains the core Models used in gpp.
"""

from django.db import models


class DebugLog(models.Model):
   '''Model to represent debug logs used during development; arbitary text can be stored'''

   LOG_LEVELS = (
      (0, 'Not Set'),
      (10, 'Debug'),
      (20, 'Info'),
      (30, 'Warning'),
      (40, 'Error'),
      (50, 'Critical'),
   )

   timestamp = models.DateTimeField(auto_now_add = True)
   level = models.IntegerField(choices = LOG_LEVELS)
   msg = models.TextField()

   def __unicode__(self):
      return '%s - %s' % (self.timestamp.strftime('%m/%d/%Y %H:%M:%S'),
            self.msg[:64])

   class Meta:
      ordering = ('-timestamp', )
