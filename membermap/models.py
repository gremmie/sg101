"""
Models for the member map application.
"""
import datetime
from django.db import models
from django.contrib.auth.models import User

from core.markup import site_markup


class MapEntry(models.Model):
    """Represents a user's entry on the map."""
    user = models.ForeignKey(User)
    location = models.CharField(max_length=255)
    lat = models.FloatField()
    lon = models.FloatField()
    message = models.TextField(blank=True)
    html = models.TextField(blank=True)
    date_updated = models.DateTimeField()

    def __unicode__(self):
        return u'Map entry for %s' % self.user.username

    class Meta:
        ordering = ('-date_updated', )
        verbose_name_plural = 'map entries'

    def save(self, *args, **kwargs):
        self.html = site_markup(self.message)
        self.date_updated = datetime.datetime.now()
        super(MapEntry, self).save(*args, **kwargs)

