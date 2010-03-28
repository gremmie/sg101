"""
Models for the member map application.
"""
from django.db import models
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.template.defaultfilters import escapejs
import django.utils.simplejson as json

from core.markup import site_markup


class MapEntry(models.Model):
    """Represents a user's entry on the map."""
    user = models.ForeignKey(User)
    location = models.CharField(max_length=255)
    lat = models.FloatField()
    lon = models.FloatField()
    message = models.TextField(blank=True)
    json = models.TextField(blank=True)
    date_updated = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return u'Entry for %s' % self.user.username

    class Meta:
        ordering = ('-date_updated', )
        verbose_name_plural = 'map entries'

    def save(self, *args, **kwargs):
        msg = render_to_string('membermap/markdown.html', {
            'user': self.user,
            'msg': site_markup(self.message)}).strip()

        self.json = json.dumps({'name': self.user.username,
            'lat': '%10.6f' % self.lat,
            'lon': '%10.6f' % self.lon,
            'message': msg,
            })
        super(MapEntry, self).save(*args, **kwargs)

