"""
Models for the banners application.

"""
import datetime

from django.db import models
from django.utils.encoding import python_2_unicode_compatible


@python_2_unicode_compatible
class Campaign(models.Model):
    """
    A model to represent an ad or banner campaign.

    """
    name = models.CharField(max_length=128)
    slug = models.SlugField()
    creation_date = models.DateTimeField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.pk and not self.creation_date:
            self.creation_date = datetime.datetime.now()

        super(Campaign, self).save(*args, **kwargs)


def banner_upload_to(instance, filename):
    """
    An "upload_to" function for the Banner model.

    """
    return "banners/%s/%s" % (instance.campaign.slug, filename)


@python_2_unicode_compatible
class Banner(models.Model):
    """
    A model to represent a banner.

    """
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    image = models.ImageField(upload_to=banner_upload_to)
    description = models.CharField(max_length=128)
    creation_date = models.DateTimeField(blank=True)

    def __str__(self):
        return self.description

    class Meta:
        ordering = ['-creation_date']

    def save(self, *args, **kwargs):
        if not self.pk and not self.creation_date:
            self.creation_date = datetime.datetime.now()

        super(Banner, self).save(*args, **kwargs)
