"""Models for the bandmap application.

"""
import datetime

from django.db import models
from django.contrib.auth.models import User
from django.template.loader import render_to_string


class BandEntryManager(models.Manager):
    def new_entry_count(self):
        return self.filter(is_approved=False).count()


class BandEntry(models.Model):
    """Represents a band entry on the band map."""
    name = models.CharField(max_length=128)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date_submitted = models.DateTimeField()
    date_approved = models.DateTimeField(null=True, blank=True)
    url = models.URLField(blank=True, max_length=200)
    location = models.CharField(max_length=255)
    lat = models.FloatField()
    lon = models.FloatField()
    note = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    is_approved = models.BooleanField(default=False, db_index=True)
    html = models.TextField(blank=True)

    objects = BandEntryManager()

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'band map entries'

    def __str__(self):
        return u"BandMap entry for {}".format(self.name)

    def save(self, *args, **kwargs):
        if not self.pk and not self.date_submitted:
            self.date_submitted = datetime.datetime.now()
        html = render_to_string('bandmap/balloon.html', {'band': self})
        self.html = html.strip().replace('\n', '')
        super(BandEntry, self).save(*args, **kwargs)
