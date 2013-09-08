"""Models for the user_photos application."""

import datetime

from django.db import models
from django.conf import settings


class Photo(models.Model):
    """This model represents data about a user uploaded photo."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             related_name='uploaded_photos')
    upload_date = models.DateTimeField()
    url = models.URLField(max_length=200)
    thumb_url = models.URLField(max_length=200, blank=True)

    def __unicode__(self):
        return u'Photo by {} on {}'.format(self.user.username,
                               self.upload_date.strftime('%Y-%m-%d %H:%M:%S'))

    def get_absolute_url(self):
        return self.url

    def save(self, *args, **kwargs):
        if not self.pk and not self.upload_date:
            self.upload_date = datetime.datetime.now()
        super(Photo, self).save(*args, **kwargs)

