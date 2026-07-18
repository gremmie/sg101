"""
Models for the podcast application.

"""
import datetime

from django.urls import reverse
from django.db import models
from django.utils.encoding import python_2_unicode_compatible


EXPLICIT_CHOICES = [
    ('yes', 'Yes'),
    ('no', 'No'),
    ('clean', 'Clean'),
]


@python_2_unicode_compatible
class Channel(models.Model):
    """Model to represent the Channel properties"""

    title = models.CharField(max_length=255)
    link = models.URLField()
    language = models.CharField(max_length=16)
    copyright = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255)
    author = models.CharField(max_length=64)
    description = models.CharField(max_length=255)
    owner_name = models.CharField(max_length=64)
    owner_email = models.EmailField()
    image = models.ImageField(upload_to='podcast')
    category = models.CharField(max_length=64)
    explicit = models.CharField(max_length=8, choices=EXPLICIT_CHOICES)
    keywords = models.CharField(max_length=255)

    def __str__(self):
        return self.title


@python_2_unicode_compatible
class Item(models.Model):
    """Model to represent a channel item"""
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255)
    summary = models.TextField()
    enclosure_url = models.URLField()
    alt_enclosure_url = models.URLField(blank=True)
    enclosure_length = models.IntegerField()
    enclosure_type = models.CharField(max_length=32)
    guid = models.CharField(max_length=255)
    pubdate = models.DateTimeField(db_index=True)
    duration = models.CharField(max_length=16)
    keywords = models.CharField(max_length=255)
    explicit = models.CharField(max_length=8, choices=EXPLICIT_CHOICES)
    update_date = models.DateTimeField(db_index=True, blank=True)

    def get_absolute_url(self):
        return reverse('podcast-detail', args=[str(self.id)])

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-pubdate']
        verbose_name = 'podcast'
        verbose_name_plural = 'podcasts'

    def save(self, *args, **kwargs):
        if not self.id:
            if not self.pubdate:
                self.pubdate = datetime.datetime.now()
            self.update_date = self.pubdate
        else:
            self.update_date = datetime.datetime.now()
        super(Item, self).save(*args, **kwargs)

    def search_title(self):
        return "%s: %s" % (self.title, self.subtitle)

    def search_summary(self):
        return u"\n".join((self.subtitle, self.summary, self.keywords))

    def ogp_tags(self):
        """
        Returns a dict of Open Graph Protocol meta tags.

        """
        title = "%s: %s; %s" % (self.channel.title, self.title, self.subtitle)
        return {
            'og:title': title,
            'og:type': 'article',
            'og:url': self.get_absolute_url(),
            'og:description': self.subtitle,
            'og:audio': self.enclosure_url,
            'og:audio:title': title,
            'og:audio:artist': 'Various',
            'og:audio:type': self.enclosure_type,
        }
