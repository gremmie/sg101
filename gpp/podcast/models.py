"""Models for the podcast application."""

from django.db import models

EXPLICIT_CHOICES = (
        ('yes', 'Yes'),
        ('no', 'No'),
        ('clean', 'Clean'),
    )


class Channel(models.Model):
    """Model to represent the Channel properties"""

    title = models.CharField(max_length=255)
    link = models.URLField(verify_exists=False)
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

    def __unicode__(self):
        return self.title


class Item(models.Model):
    """Model to represent a channel item"""
    channel = models.ForeignKey(Channel)
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255)
    summary = models.TextField()
    enclosure_url = models.URLField(verify_exists=False)
    alt_enclosure_url = models.URLField(verify_exists=False, blank=True)
    enclosure_length = models.IntegerField()
    enclosure_type = models.CharField(max_length=32)
    guid = models.CharField(max_length=255)
    pubdate = models.DateTimeField()
    duration = models.CharField(max_length=16)
    keywords = models.CharField(max_length=255)
    explicit = models.CharField(max_length=8, choices=EXPLICIT_CHOICES)

    @models.permalink
    def get_absolute_url(self):
        return ('podcast.views.detail', [str(self.id)])

    def __unicode__(self):
        return self.title

    class Meta:
        ordering = ('-pubdate', )
        verbose_name = 'podcast'
        verbose_name_plural = 'podcasts'

    def search_title(self):
        return "%s: %s" % (self.title, self.subtitle)

    def search_summary(self):
        return u"\n".join((self.subtitle, self.summary, self.keywords))
