"""
This file contains the core Models used in gpp.
The SiteConfig information is cached in a similar manner to django.contrib.sites.
"""

from django.db import models

SITE_CACHE = {}

class SiteConfigManager(models.Manager):
   def get_current(self):
      """
      Returns the current SiteConfig based on the SITE_ID in the
      project's settings. The SiteConfig object is cached the first
      time it's retrieved from the database.
      """
      from django.conf import settings
      try:
         sid = settings.SITE_ID
      except AttributeError:
         from django.core.exceptions import ImproperlyConfigured
         raise ImproperlyConfigured("You're using the Django \"sites framework\" without having set the SITE_ID setting. " +
               "Create a site in your database and set the SITE_ID setting to fix this error.")
      try:
         current_site_config = SITE_CACHE[sid]
      except KeyError:
         current_site_config = self.get(pk = sid)
         SITE_CACHE[sid] = current_site_config
      return current_site_config


      def clear_cache(self):
         """Clears the SiteConfig object cache."""
         global SITE_CACHE
         SITE_CACHE = {}


class SiteConfig(models.Model):
   """model to represent the site's basic configuration and settings""" 
   site_slogan = models.CharField(max_length = 128, blank = True)
   admin_name = models.CharField(max_length = 64)
   admin_email = models.EmailField()
   date_created = models.DateField()

   objects = SiteConfigManager()


   def __unicode__(self):
      return u'SiteConfig ' + unicode(self.id)


   def delete(self):
      pk = self.pk
      super(SiteConfig, self).delete()
      try:
         del(SITE_CACHE[pk])
      except KeyError:
         pass


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
