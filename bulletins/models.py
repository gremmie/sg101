"""Models for the bulletins app.
Bulletins allow the sited admins to display and manage important notices for the website.
"""

from django.db import models
from django.db.models import Q
from django.utils import timezone


class BulletinManager(models.Manager):
    """Manager for the Bulletin model."""

    def get_current(self):
        now = timezone.now()
        return self.filter(
                Q(is_enabled=True),
                Q(start_date__lte=now),
                Q(end_date__isnull=True) | Q(end_date__gte=now))


class Bulletin(models.Model):
    """Model to represent site bulletins."""
    title = models.CharField(max_length=200)
    text = models.TextField()
    start_date = models.DateTimeField(db_index=True,
            help_text='Start date for when the bulletin will be active.',)
    end_date = models.DateTimeField(blank=True, null=True, db_index=True,
            help_text='End date for the bulletin. Leave blank to keep it open-ended.')
    is_enabled = models.BooleanField(default=True, db_index=True,
            help_text='Check to allow the bulletin to be viewed on the site.')

    objects = BulletinManager()

    class Meta:
        ordering = ('-start_date', )

    def __str__(self):
        return self.title
