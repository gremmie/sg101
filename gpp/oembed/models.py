"""
Models for the oembed application.
"""
import datetime

from django.db import models


class Provider(models.Model):
    """
    This model described an oEmbed provider.
    """
    JSON, XML = range(2)
    FORMAT_CHOICES = (
        (JSON, "json"),
        (XML, "xml"),
    )

    name = models.CharField(max_length=128)
    api_endpoint = models.URLField(max_length=255, verbose_name='API endpoint')
    url_regex = models.CharField(max_length=255, verbose_name='URL regex')
    format = models.IntegerField(choices=FORMAT_CHOICES)

    def __unicode__(self):
        return self.name


class Oembed(models.Model):
    """
    This model represents stored embedded content retrieved from an oEmbed
    provider.
    """
    PHOTO, VIDEO, LINK, RICH = range(4)
    MEDIA_TYPE_CHOICES = (
        (PHOTO, "photo"),
        (VIDEO, "video"),
        (LINK, "link"),
        (RICH, "rich"),
    )

    url = models.URLField(max_length=255, db_index=True)
    type = models.IntegerField(choices=MEDIA_TYPE_CHOICES)
    title = models.CharField(max_length=255, blank=True, default='')
    width = models.IntegerField()
    height = models.IntegerField()
    html = models.TextField()
    date_added = models.DateTimeField()

    def __unicode__(self):
        return self.title or self.url

    def save(self, *args, **kwargs):
        if not self.pk:
            self.date_added = datetime.datetime.now()

        super(Oembed, self).save(*args, **kwargs)

